from core.models.result import ExecutionResult, Status


def run_tests(intent: dict) -> ExecutionResult:
    # allow skipping tests via intent
    if intent.get("tests", {}).get("enabled") is False:
        return ExecutionResult(
            stage="TEST",
            status=Status.SUCCESS,
            message="Tests skipped",
            logs=["Tests disabled by intent"],
        )

    # simulated failure case
    if intent.get("application", {}).get("name") == "bad-test-app":
        return ExecutionResult(
            stage="TEST",
            status=Status.FAILED,
            message="Unit tests failed",
            logs=["TestLogin FAILED", "TestCheckout FAILED"],
            action="Fix failing tests and re-run",
        )

    return ExecutionResult(
        stage="TEST",
        status=Status.SUCCESS,
        message="All tests passed",
        logs=["Unit tests passed", "Integration tests passed"],
    )
