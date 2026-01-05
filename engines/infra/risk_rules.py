from core.models.result import ExecutionResult, Status


def evaluate_risks(normalized_plan: dict) -> ExecutionResult:
    """
    Risk Rules V1 (Decision-only)
    BLOCK:
      - Any delete
      - Any replace
    WARN:
      - High create count (>5)
    """

    deletes = normalized_plan.get("delete", 0)
    replaces = normalized_plan.get("replace", 0)
    creates = normalized_plan.get("create", 0)

    # BLOCKING RULES
    if deletes > 0:
        return ExecutionResult(
            stage="INFRA-RISK",
            status=Status.BLOCKED,
            message="Terraform plan contains destructive changes",
            logs=[f"Delete actions detected: {deletes}"],
            action="Remove delete actions or review infra design",
        )

    if replaces > 0:
        return ExecutionResult(
            stage="INFRA-RISK",
            status=Status.BLOCKED,
            message="Terraform plan contains resource replacement",
            logs=[f"Replace actions detected: {replaces}"],
            action="Avoid replacement or split change safely",
        )

    # WARNING RULES
    if creates > 5:
        return ExecutionResult(
            stage="INFRA-RISK",
            status=Status.WARN,
            message="High number of resources to be created",
            logs=[f"Create actions detected: {creates}"],
            action="Review cost and scaling impact",
        )

    # SAFE
    return ExecutionResult(
        stage="INFRA-RISK",
        status=Status.SUCCESS,
        message="No infrastructure risks detected",
        logs=["Terraform plan is safe to proceed"],
    )
