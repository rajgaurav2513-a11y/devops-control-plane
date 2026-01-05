from core.models.result import ExecutionResult, Status


def generate_fix_suggestions(results: list) -> ExecutionResult:
    suggestions = []

    for r in results:
        status = r.status

        # ---- SAFE STATUS CHECK (NO WARNING ASSUMPTION) ----
        if status not in (Status.BLOCKED, getattr(Status, "WARN", None), getattr(Status, "WARNING", None)):
            continue

        # -----------------------------
        # Infra destructive changes
        # -----------------------------
        if r.stage == "INFRA-RISK":
            suggestions.append(
                "Review destructive or replacement infrastructure changes."
            )

        # -----------------------------
        # Public exposure
        # -----------------------------
        if r.stage == "INFRA-PUBLIC-RISK":
            suggestions.append(
                "Restrict security group ingress and remove public IP exposure."
            )

        # -----------------------------
        # Cost risk
        # -----------------------------
        if r.stage == "INFRA-COST-RISK":
            suggestions.append(
                "Reduce instance size or count to lower infrastructure cost."
            )

        # -----------------------------
        # Config issues
        # -----------------------------
        if r.stage == "CONFIG":
            suggestions.append(
                "Provide all required configuration values and remove forbidden ones."
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
        status=getattr(Status, "WARN", Status.SUCCESS),
        message="Suggested fixes generated",
        logs=list(set(suggestions)),
    )
