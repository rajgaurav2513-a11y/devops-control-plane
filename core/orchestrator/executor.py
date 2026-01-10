# core/orchestrator/executor.py

import uuid
import os

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


STAGE_ORDER = [
    "SOURCE",
    "BUILD",
    "IMAGE-PUBLISH",
    "TEST",
    "QUALITY",
    "CONFIG",
    "POLICY",
    "CONFIG-ROLLING",
    "K8S-DRY-RUN",
    "K8S-APPLY",
    "RUN",
    "INFRA",
    "INFRA-RISK",
    "INFRA-PUBLIC-RISK",
    "INFRA-COST-RISK",
    "FIX-SUGGESTIONS",
    "SNAPSHOT",
    "CONFIG-ROLLBACK",

]


def is_code_required(intent: dict) -> bool:
    return "application" in intent


def has_infra(intent: dict) -> bool:
    return "infra" in intent


def execute(intent: dict):
    results = []

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

    # SOURCE
    if code_required and should_run("SOURCE"):
        app_cfg = intent.get("application", {})
        local_path = app_cfg.get("path")

        if local_path:
            workspace = os.path.abspath(local_path)
        else:
            workspace = prepare_source(intent)

        if not workspace or not os.path.isdir(workspace):
            results.append(
                ExecutionResult(
                    stage="SOURCE",
                    status=Status.BLOCKED,
                    message="Invalid application workspace",
                    logs=[f"workspace={workspace}"],
                )
            )
            return results

        intent["_execution"]["workspace"] = workspace
        mark_stage_complete(execution_id, "SOURCE")

    # BUILD
    if code_required and should_run("BUILD"):
        if not docker_available():
            results.append(
                ExecutionResult(
                    stage="BUILD",
                    status=Status.BLOCKED,
                    message="Docker engine not reachable",
                )
            )
            return results

        r = build_image(intent)
        results.append(r)
        if r.status != Status.SUCCESS:
            cleanup_source(intent)
            return results

        mark_stage_complete(execution_id, "BUILD")

        # -----------------------------
        # IMAGE PUBLISH
        # -----------------------------
    if should_run("IMAGE-PUBLISH"):
        r = publish_image(intent)
        results.append(r)
        if r.status == Status.BLOCKED:
            cleanup_source(intent)
            return results

        mark_stage_complete(execution_id, "IMAGE-PUBLISH")


    # TEST
    if code_required and should_run("TEST"):
        r = run_tests(intent)
        results.append(r)
        if r.status != Status.SUCCESS:
            cleanup_source(intent)
            return results

        mark_stage_complete(execution_id, "TEST")

    # QUALITY
    if code_required and should_run("QUALITY"):
        r = run_quality_checks(intent)
        results.append(r)
        if r.status != Status.SUCCESS:
            cleanup_source(intent)
            return results

        mark_stage_complete(execution_id, "QUALITY")

    # CONFIG (intent validation)
    if should_run("CONFIG"):
        r = validate_intent(intent)
        results.append(r)
        if r.status != Status.SUCCESS:
            cleanup_source(intent)
            return results

        mark_stage_complete(execution_id, "CONFIG")

    # POLICY
    if should_run("POLICY"):
        policy_results = evaluate_policies(intent)
    results.extend(policy_results)

    if any(r.status == Status.BLOCKED for r in policy_results):
        cleanup_source(intent)
        return results

    mark_stage_complete(execution_id, "POLICY")


    # CONFIG ROLLING (native config engine)
    if "config" in intent and should_run("CONFIG-ROLLING"):
        r = rolling_apply(intent)
        results.append(r)
        if r.status == Status.BLOCKED:
            cleanup_source(intent)
            return results

        mark_stage_complete(execution_id, "CONFIG-ROLLING")

    # KUBERNETES DRY-RUN
    if "kubernetes" in intent and should_run("K8S-DRY-RUN"):
        r = kubernetes_dry_run(intent)
        results.append(r)
        if r.status == Status.BLOCKED:
            cleanup_source(intent)
            return results

        mark_stage_complete(execution_id, "K8S-DRY-RUN")

    # KUBERNETES APPLY (explicit)
    if intent.get("_apply_k8s") and should_run("K8S-APPLY"):
        r = kubernetes_apply(intent)
        results.append(r)
        if r.status == Status.BLOCKED:
            cleanup_source(intent)
            return results

        mark_stage_complete(execution_id, "K8S-APPLY")

    # RUN
    if code_required and should_run("RUN"):
        app = intent.get("application", {}).get("name", "app").lower()
        image = f"{app}:{artifact_tag}"

        r = run_container(intent=intent, image_name=image)
        results.append(r)
        if r.status != Status.SUCCESS:
            cleanup_source(intent)
            return results

        mark_stage_complete(execution_id, "RUN")

    # INFRA (PLAN ONLY)
    if infra_required and should_run("INFRA"):
        plan = provision(intent)
        normalized = normalize_plan(plan)

        results.append(
            ExecutionResult(
                stage="INFRA",
                status=Status.SUCCESS,
                message="Terraform plan analyzed",
                logs=[
                    f"Create: {normalized['create']}",
                    f"Update: {normalized['update']}",
                    f"Delete: {normalized['delete']}",
                    f"Replace: {normalized['replace']}",
                ],
            )
        )

        mark_stage_complete(execution_id, "INFRA")

    # INFRA RISKS
    if infra_required and should_run("INFRA-RISK"):
        r = evaluate_risks(normalized)
        results.append(r)
        mark_stage_complete(execution_id, "INFRA-RISK")

    if infra_required and should_run("INFRA-PUBLIC-RISK"):
        r = evaluate_public_exposure(plan)
        results.append(r)
        if r.status == Status.BLOCKED:
            cleanup_source(intent)
            return results

        mark_stage_complete(execution_id, "INFRA-PUBLIC-RISK")

    if infra_required and should_run("INFRA-COST-RISK"):
        r = evaluate_cost_risk(plan)
        results.append(r)
        if r.status == Status.BLOCKED:
            cleanup_source(intent)
            return results

        mark_stage_complete(execution_id, "INFRA-COST-RISK")

    # FIX SUGGESTIONS
    if should_run("FIX-SUGGESTIONS"):
        r = generate_infra_fix_suggestions(results)
        results.append(r)
        mark_stage_complete(execution_id, "FIX-SUGGESTIONS")

    # SNAPSHOT
    if should_run("SNAPSHOT"):
        save_snapshot(intent)
        results.append(
            ExecutionResult(
                stage="SNAPSHOT",
                status=Status.SUCCESS,
                message="Execution snapshot saved",
                logs=[
                    f"execution_id={execution_id}",
                    f"artifact={artifact_tag}",
                ],
            )
        )
        mark_stage_complete(execution_id, "SNAPSHOT")

    # AUTO-DEPLOY (existing behavior)
    exec_mode = intent.get("execution", {}).get("mode", "analyze")
    deploy_cfg = intent.get("deploy", {})
    blocked = any(r.status == Status.BLOCKED for r in results)

    if exec_mode == "auto-deploy" and not blocked:
        if deploy_cfg.get("mode") == "docker":
            app = intent.get("application", {}).get("name", "app").lower()
            image = f"{app}:{artifact_tag}"
            results.append(deploy_local(intent, image))
        else:
            results.append(auto_deploy_local(intent))

    cleanup_source(intent)
    return results
