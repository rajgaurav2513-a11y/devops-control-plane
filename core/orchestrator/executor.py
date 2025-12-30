from core.models.result import ExecutionResult, Status

from engines.infra.terraform_engine import provision
from engines.container.builder import build_image
from engines.deploy.k8s_engine import deploy_app
from state.snapshots import save_snapshot


def execute(intent: dict):
    """
    Main execution orchestrator.
    Executes stages sequentially and STOPS on failure.
    """
    results = []

    # =========================
    # BUILD STAGE
    # =========================
    build_result = build_image(intent)
    results.append(build_result)

    if build_result.status != Status.SUCCESS:
        return results  # ⛔ STOP EXECUTION ON BUILD FAILURE / BLOCKED

    # =========================
    # INFRA STAGE
    # =========================
    try:
        infra_state = provision(intent)
        infra_result = ExecutionResult(
            stage="INFRA",
            status=Status.SUCCESS,
            message="Infrastructure provisioned successfully",
            logs=[f"Infrastructure state: {infra_state}"],
        )
        results.append(infra_result)
    except Exception as e:
        infra_result = ExecutionResult(
            stage="INFRA",
            status=Status.FAILED,
            message="Infrastructure provisioning failed",
            logs=[str(e)],
            action="Fix infrastructure configuration and re-run",
        )
        results.append(infra_result)
        return results  # ⛔ STOP EXECUTION

    # =========================
    # DEPLOY STAGE
    # =========================
    try:
        deploy_app(intent, build_result)
        deploy_result = ExecutionResult(
            stage="DEPLOY",
            status=Status.SUCCESS,
            message="Application deployed successfully (simulated)",
            logs=["Blue/Green deployment simulated"],
        )
        results.append(deploy_result)
    except Exception as e:
        deploy_result = ExecutionResult(
            stage="DEPLOY",
            status=Status.FAILED,
            message="Deployment failed",
            logs=[str(e)],
            action="Check deployment logs and retry",
        )
        results.append(deploy_result)
        return results  # ⛔ STOP EXECUTION

    # =========================
    # SNAPSHOT STAGE
    # =========================
    try:
        save_snapshot(intent)
        snapshot_result = ExecutionResult(
            stage="SNAPSHOT",
            status=Status.SUCCESS,
            message="Execution snapshot saved",
            logs=["System state recorded successfully"],
        )
        results.append(snapshot_result)
    except Exception as e:
        snapshot_result = ExecutionResult(
            stage="SNAPSHOT",
            status=Status.BLOCKED,
            message="Snapshot could not be saved",
            logs=[str(e)],
            action="Check snapshot storage",
        )
        results.append(snapshot_result)

    return results
