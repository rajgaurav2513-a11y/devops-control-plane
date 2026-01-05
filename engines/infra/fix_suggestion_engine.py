from core.models.result import ExecutionResult, Status


def generate_infra_fix_suggestions(results: list) -> ExecutionResult:
    suggestions = []

    for r in results:
        # Public exposure block
        if r.stage == "INFRA-PUBLIC-RISK" and r.status == Status.BLOCKED:
            suggestions.append(
                "Restrict ingress CIDR blocks instead of using 0.0.0.0/0"
            )

        # Cost block
        if r.stage == "INFRA-COST-RISK" and r.status == Status.BLOCKED:
            suggestions.append(
                "High infrastructure cost detected — reduce instance size or count"
            )

        # Cost success (optional hint)
        if r.stage == "INFRA-COST-RISK" and r.status == Status.SUCCESS:
            suggestions.append(
                "Infrastructure cost is within limits — no action required"
            )

        # Infra success
        if r.stage == "INFRA" and r.status == Status.SUCCESS:
            suggestions.append(
                "Terraform plan looks clean — no destructive changes detected"
            )

    if not suggestions:
        return ExecutionResult(
            stage="FIX-SUGGESTIONS",
            status=Status.SUCCESS,
            message="No fix suggestions required",
            logs=[],
        )

    return ExecutionResult(
        stage="FIX-SUGGESTIONS",
        status=Status.SUCCESS,
        message="Fix suggestions generated",
        logs=suggestions,
    )
