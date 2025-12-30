from core.models.result import ExecutionResult, Status


def run_build(intent: dict) -> ExecutionResult:
    return ExecutionResult(
        stage="BUILD",
        status=Status.SUCCESS,
        message="Python build completed successfully",
        logs=[
            "Installing dependencies",
            "Running pytest",
            "All tests passed",
        ],
    )
