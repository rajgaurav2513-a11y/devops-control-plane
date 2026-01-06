# core/orchestrator/executor.py
# 🔧 FULL FILE WITH FINAL APPROVAL FIX (COPY–PASTE)

import uuid
import os

from core.models.result import ExecutionResult, Status
from state.execution_store import mark_stage_complete, get_last_completed_stage
from state.snapshots import save_snapshot

from core.intent.validator import validate_intent

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

from engines.deploy.local_docker import deploy_local

from core.approval.model import ApprovalRecord, ApprovalStatus
from core.approval.store import load as load_approval, save as save_approval


STAGE_ORDER = [
    "SOURCE",
    "BUILD",
    "TEST",
    "QUALITY",
    "CONFIG",
    "RUN",
    "INFRA",
    "INFRA-RISK",
    "INFRA-PUBLIC-RISK",
    "INFRA-COST-RISK",
    "APPROVAL",
    "FIX-SUGGESTIONS",
    "DEPLOY",
    "SNAPSHOT",
]


def is_code_required(intent: dict) -> bool:
    return "application" in intent


def has_infra(intent: dict) -> bool:
    return "infra" in intent


def execute(intent: dict):
    results = []

    execution_id = intent.get("_execution", {}).get("id")
    if not execution_id:
        execution_id = str(uuid.uuid4())[:8]

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

    if code_required and should_run("SOURCE"):
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

    if code_required and should_run("BUILD"):
        if not docker_available():
            results.append(
                ExecutionResult(
                    stage="BUILD",
                    status=Status.BLOCKED,
                    message="Docker engine not reachable",
                    logs=[],
                )
            )
            return results

        r = build_image(intent)
        results.append(r)
        if r.status != Status.SUCCESS:
            cleanup_source(intent)
            return results
        mark_stage_complete(execution_id, "BUILD")

    if code_required and should_run("TEST"):
        r = run_tests(intent)
        results.append(r)
        if r.status != Status.SUCCESS:
            cleanup_source(intent)
            return results
        mark_stage_complete(execution_id, "TEST")

    if code_required and should_run("QUALITY"):
        r = run_quality_checks(intent)
        results.append(r)
        if r.status != Status.SUCCESS:
            cleanup_source(intent)
            return results
        mark_stage_complete(execution_id, "QUALITY")

    if should_run("CONFIG"):
        r = validate_intent(intent)
        results.append(r)
        if r.status != Status.SUCCESS:
            cleanup_source(intent)
            return results
        mark_stage_complete(execution_id, "CONFIG")

    if code_required and should_run("RUN"):
        app = intent.get("application", {}).get("name", "app").lower()
        image = f"{app}:{artifact_tag}"
        r = run_container(intent, image)
        results.append(r)
        if r.status != Status.SUCCESS:
            cleanup_source(intent)
            return results
        mark_stage_complete(execution_id, "RUN")

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

    if infra_required and should_run("INFRA-RISK"):
        r = evaluate_risks(normalized)
        results.append(r)
        mark_stage_complete(execution_id, "INFRA-RISK")

    if infra_required and should_run("INFRA-PUBLIC-RISK"):
        r = evaluate_public_exposure(plan)
        results.append(r)
        if r.status == Status.BLOCKED:
            return results
        mark_stage_complete(execution_id, "INFRA-PUBLIC-RISK")

    if infra_required and should_run("INFRA-COST-RISK"):
        r = evaluate_cost_risk(plan)
        results.append(r)
        if r.status == Status.BLOCKED:
            return results
        mark_stage_complete(execution_id, "INFRA-COST-RISK")

    # =============================
    # APPROVAL GATE (FINAL)
    # =============================
    if should_run("APPROVAL"):
        approval = load_approval(execution_id)

        if not approval:
            approval = ApprovalRecord(
                execution_id=execution_id,
                status=ApprovalStatus.PENDING,
            )
            save_approval(approval)

        if approval.status in (
            ApprovalStatus.PENDING,
            ApprovalStatus.HELD,
        ):
            results.append(
                ExecutionResult(
                    stage="APPROVAL",
                    status=Status.SUCCESS,
                    message=f"Approval status: {approval.status}",
                    logs=[f"execution_id={execution_id}"],
                )
            )
            return results

        if approval.status == ApprovalStatus.REJECTED:
            results.append(
                ExecutionResult(
                    stage="APPROVAL",
                    status=Status.BLOCKED,
                    message="Execution rejected by approver",
                    logs=[f"execution_id={execution_id}"],
                )
            )
            return results

        mark_stage_complete(execution_id, "APPROVAL")

    if should_run("FIX-SUGGESTIONS"):
        r = generate_infra_fix_suggestions(results)
        results.append(r)
        mark_stage_complete(execution_id, "FIX-SUGGESTIONS")

    if should_run("SNAPSHOT"):
        save_snapshot(intent)
        results.append(
            ExecutionResult(
                stage="SNAPSHOT",
                status=Status.SUCCESS,
                message="Execution snapshot saved",
                logs=[f"execution_id={execution_id}"],
            )
        )
        mark_stage_complete(execution_id, "SNAPSHOT")

    cleanup_source(intent)
    return results
