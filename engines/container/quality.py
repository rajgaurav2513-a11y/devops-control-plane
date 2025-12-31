from core.models.result import ExecutionResult, Status


def run_quality_checks(intent: dict) -> ExecutionResult:
    """
    Quality Agent:
    - Enforces quality gates (Sonar-like behavior)
    - Can BLOCK execution without marking it as FAILED
    """

    # Allow disabling quality gate via intent
    if intent.get("quality", {}).get("enabled") is False:
        return ExecutionResult(
            stage="QUALITY",
            status=Status.SUCCESS,
            message="Quality checks skipped",
            logs=["Quality gate disabled by intent"],
        )

    app_name = intent.get("application", {}).get("name", "")

    # Simulated quality gate failure
    if app_name == "bad-quality-app":
        return ExecutionResult(
            stage="QUALITY",
            status=Status.BLOCKED,
            message="Quality gate failed",
            logs=[
                "Code coverage below required threshold",
                "Critical code smells detected",
            ],
            action="Fix quality issues and re-run the pipeline",
        )

    # Default success case
    return ExecutionResult(
        stage="QUALITY",
        status=Status.SUCCESS,
        message="Quality gate passed",
        logs=[
            "Code coverage within limits",
            "No critical vulnerabilities found",
        ],
    )
