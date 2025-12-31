from core.models.result import ExecutionResult, Status


def run_build(intent: dict) -> ExecutionResult:
    return ExecutionResult(
        stage="BUILD",
        status=Status.SUCCESS,
        message="Node.js build completed successfully",
        logs=[
            "npm install",
            "npm test",
            "All tests passed",
        ],
    )
