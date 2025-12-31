from core.models.result import ExecutionResult, Status


def run_build(intent: dict) -> ExecutionResult:
    app_name = intent.get("application", {}).get("name")

    # Simulated failure case
    if app_name == "bad-app":
        return ExecutionResult(
            stage="BUILD",
            status=Status.FAILED,
            message="Maven build failed due to unit test errors",
            logs=[
                "Running mvn test",
                "TestUserService FAILED",
                "TestOrderService FAILED",
            ],
            action="Fix failing tests and re-run",
        )

    return ExecutionResult(
        stage="BUILD",
        status=Status.SUCCESS,
        message="Maven build completed successfully",
        logs=[
            "Running mvn clean test",
            "All unit tests passed",
        ],
    )
