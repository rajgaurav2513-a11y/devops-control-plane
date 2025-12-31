from core.models.result import ExecutionResult, Status

from engines.container.builder import build_image
from engines.container.tester import run_tests
from engines.container.quality import run_quality_checks
from engines.infra.terraform_engine import provision
from engines.deploy.k8s_engine import deploy_app
from state.snapshots import save_snapshot


def execute(intent: dict):
    """
    Agentic Orchestrator:
    Executes stages sequentially and STOPS on FAILED or BLOCKED.
    """
    results = []

    # =========================
    # BUILD STAGE
    # =========================
    build_result = build_image(intent)
    results.append(build_result)

    if build_result.status != Status.SUCCESS:
        return results  # ⛔ STOP ON BUILD FAIL / BLOCK

    # =========================
    # TEST STAGE
    # =========================
    test_result = run_tests(intent)
    results.append(test_result)

    if test_result.status != Status.SUCCESS:
        return results  # ⛔ STOP ON TEST FAIL / BLOCK

    # =========================
    # QUALITY STAGE
    # =========================
    quality_result = run_quality_checks(intent)
    results.append(quality_result)

    if quality_result.status != Status.SUCCESS:
        return results  # ⛔ STOP ON QUALITY BLOCK / FAIL

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
        results.append(
            ExecutionResult(
                stage="INFRA",
                status=Status.FAILED,
                message="Infrastructure provisioning failed",
                logs=[str(e)],
                action="Fix infrastructure configuration and re-run",
            )
        )
        return results  # ⛔ STOP

    # =========================
    # DEPLOY STAGE
    # =========================
    try:
        deploy_result = deploy_app(intent)
        results.append(deploy_result)

        if deploy_result.status != Status.SUCCESS:
            return results  # ⛔ STOP
    except Exception as e:
        results.append(
            ExecutionResult(
                stage="DEPLOY",
                status=Status.FAILED,
                message="Deployment failed",
                logs=[str(e)],
                action="Check deployment configuration and retry",
            )
        )
        return results  # ⛔ STOP

    # =========================
    # SNAPSHOT STAGE (NON-BLOCKING)
    # =========================
    try:
        save_snapshot(intent)
        results.append(
            ExecutionResult(
                stage="SNAPSHOT",
                status=Status.SUCCESS,
                message="Execution snapshot saved",
                logs=["System state recorded"],
            )
        )
    except Exception as e:
        results.append(
            ExecutionResult(
                stage="SNAPSHOT",
                status=Status.BLOCKED,
                message="Snapshot could not be saved",
                logs=[str(e)],
                action="Check snapshot storage",
            )
        )

    return results
