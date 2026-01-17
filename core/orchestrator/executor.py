import uuid
import os
import time

from core.models.result import ExecutionResult, Status
from core.policy.evaluator import evaluate_policies
from core.intent.validator import validate_intent

from state.execution_store import mark_stage_complete, get_last_completed_stage
from state.snapshots import save_snapshot

from engines.source.git_agent import prepare_source, cleanup_source
from engines.container.builder import build_image
from engines.container.tester import run_tests
from engines.container.quality import run_quality_checks
from engines.container.docker_runner import run_container
from engines.container.docker_health import docker_available

from engines.infra.terraform_engine import provision
from engines.infra.plan_normalizer import normalize_plan
from engines.infra.risk_rules import evaluate_risks
from engines.infra.public_exposure_rules import evaluate_public_exposure
from engines.infra.cost_risk_rules import evaluate_cost_risk
from engines.infra.fix_suggestion_engine import generate_infra_fix_suggestions

from engines.kubernetes.dry_run import kubernetes_dry_run
from engines.kubernetes.apply import kubernetes_apply

from engines.config.rolling import rolling_apply
from engines.container.adapters.image_publish import publish_image

from engines.deploy.local_docker import deploy_local
from engines.deploy.local_auto import auto_deploy_local

# observability (safe)
from core.observability.collectors import (
    collect_all_basic,
    record_deploy_result,
    record_config_rollout,
)

from core.observability.rules import evaluate_health, ALLOW, WARN, DELAY, BLOCK


STAGE_ORDER = [
    "SOURCE","BUILD","IMAGE-PUBLISH","TEST","QUALITY","CONFIG",
    "HEALTH","POLICY",
    "CONFIG-ROLLING","K8S-DRY-RUN","K8S-APPLY",
    "RUN","INFRA","INFRA-RISK","INFRA-PUBLIC-RISK",
    "INFRA-COST-RISK","FIX-SUGGESTIONS",
    "ROLLBACK","SNAPSHOT"
]


def is_code_required(intent: dict) -> bool:
    return "application" in intent


def has_infra(intent: dict) -> bool:
    return "infra" in intent


def execute(intent: dict):
    results = []

    collect_all_basic()

    execution_id = intent.get("_execution", {}).get("id") or str(uuid.uuid4())[:8]
    artifact_tag = f"exec-{execution_id}"

    intent["_execution"] = {
        "id": execution_id,
        "artifact_tag": artifact_tag,
    }

    last_completed = get_last_completed_stage(execution_id)

    def should_run(stage: str) -> bool:
        if not last_completed:
            return True
        return STAGE_ORDER.index(stage) > STAGE_ORDER.index(last_completed)

    code_required = is_code_required(intent)
    infra_required = has_infra(intent)

    # ---------- SOURCE ----------
    if code_required and should_run("SOURCE"):
        path = intent.get("application", {}).get("path")
        workspace = os.path.abspath(path) if path else prepare_source(intent)

        if not workspace or not os.path.isdir(workspace):
            return [ExecutionResult("SOURCE", Status.BLOCKED, "Invalid workspace")]

        intent["_execution"]["workspace"] = workspace
        mark_stage_complete(execution_id, "SOURCE")

    # ---------- BUILD ----------
    if code_required and should_run("BUILD"):
        if not docker_available():
            return [ExecutionResult("BUILD", Status.BLOCKED, "Docker not reachable")]

        start = time.time()
        r = build_image(intent)
        record_deploy_result(r.status == Status.SUCCESS, time.time() - start)
        results.append(r)

        if r.status != Status.SUCCESS:
            cleanup_source(intent)
            return results

        mark_stage_complete(execution_id, "BUILD")

    # ---------- IMAGE PUBLISH ----------
    if should_run("IMAGE-PUBLISH"):
        r = publish_image(intent)
        results.append(r)
        if r.status == Status.BLOCKED:
            cleanup_source(intent)
            return results
        mark_stage_complete(execution_id, "IMAGE-PUBLISH")

    # ---------- TEST ----------
    if code_required and should_run("TEST"):
        r = run_tests(intent)
        results.append(r)
        if r.status != Status.SUCCESS:
            cleanup_source(intent)
            return results
        mark_stage_complete(execution_id, "TEST")

    # ---------- QUALITY ----------
    if code_required and should_run("QUALITY"):
        r = run_quality_checks(intent)
        results.append(r)
        if r.status != Status.SUCCESS:
            cleanup_source(intent)
            return results
        mark_stage_complete(execution_id, "QUALITY")

    # ---------- CONFIG ----------
    if should_run("CONFIG"):
        r = validate_intent(intent)
        results.append(r)
        if r.status != Status.SUCCESS:
            cleanup_source(intent)
            return results
        mark_stage_complete(execution_id, "CONFIG")

    # ---------- HEALTH ----------
    if should_run("HEALTH"):
        h = evaluate_health(intent.get("environment", "dev"))

        status_map = {
            ALLOW: Status.SUCCESS,
            WARN: Status.WARNING,
            DELAY: Status.BLOCKED,
            BLOCK: Status.BLOCKED,
        }

        hr = ExecutionResult("HEALTH", status_map[h["decision"]], h["reason"])
        results.append(hr)

        if hr.status == Status.BLOCKED:
            cleanup_source(intent)
            return results

        mark_stage_complete(execution_id, "HEALTH")

    # ---------- POLICY ----------
    if should_run("POLICY"):
        policy_results = evaluate_policies(intent)
        results.extend(policy_results)

        if any(r.status == Status.BLOCKED for r in policy_results):
            cleanup_source(intent)
            return results

        mark_stage_complete(execution_id, "POLICY")

    # ---------- CONFIG ROLLING ----------
    if "config" in intent and should_run("CONFIG-ROLLING"):
        r = rolling_apply(intent)
        record_config_rollout(r.status == Status.SUCCESS, r.status == Status.WARNING)
        results.append(r)

        if r.status == Status.BLOCKED:
            results.append(
                ExecutionResult("ROLLBACK", Status.WARNING, "Config rollback required")
            )
            cleanup_source(intent)
            return results

        mark_stage_complete(execution_id, "CONFIG-ROLLING")

    # ---------- RUN ----------
    if code_required and should_run("RUN"):
        image = f"{intent.get('application', {}).get('name','app')}:{artifact_tag}"
        start = time.time()
        r = run_container(intent=intent, image_name=image)
        record_deploy_result(r.status == Status.SUCCESS, time.time() - start)
        results.append(r)

        if r.status != Status.SUCCESS:
            results.append(
                ExecutionResult("ROLLBACK", Status.WARNING, "App rollback required")
            )
            cleanup_source(intent)
            return results

        mark_stage_complete(execution_id, "RUN")

    # ---------- SNAPSHOT ----------
    if should_run("SNAPSHOT"):
        save_snapshot(intent)
        results.append(
            ExecutionResult("SNAPSHOT", Status.SUCCESS, "Execution snapshot saved")
        )
        mark_stage_complete(execution_id, "SNAPSHOT")

    cleanup_source(intent)
    return results
