from core.models.result import ExecutionResult, Status


INSTANCE_CLASS_MAP = {
    "t3.micro": 8,
    "t3.small": 16,
    "t3.medium": 32,
    "t3.large": 64,
    "t3.xlarge": 128,
}


WARN_LIMIT = 100
BLOCK_LIMIT = 200


def evaluate_cost_risk(plan: dict) -> ExecutionResult:
    total = 0
    logs = []

    for rc in plan.get("resource_changes", []):
        if rc.get("type") != "aws_instance":
            continue

        after = rc.get("change", {}).get("after", {}) or {}
        instance_type = after.get("instance_type", "t3.medium")
        count = after.get("count", 1)

        unit_cost = INSTANCE_CLASS_MAP.get(instance_type, 32)
        cost = unit_cost * count

        total += cost
        logs.append(
            f"{rc.get('address')} → {instance_type} x {count} ≈ ${cost}/month"
        )

    if total >= BLOCK_LIMIT:
        return ExecutionResult(
            stage="INFRA-COST-RISK",
            status=Status.BLOCKED,
            message="Infrastructure cost exceeds allowed limit",
            logs=[f"Estimated monthly cost: ${total}", *logs],
            action="Reduce instance size or count",
        )

    if total >= WARN_LIMIT:
        return ExecutionResult(
            stage="INFRA-COST-RISK",
            status=Status.WARNING,
            message="Infrastructure cost is high",
            logs=[f"Estimated monthly cost: ${total}", *logs],
            action="Review instance sizing",
        )

    return ExecutionResult(
        stage="INFRA-COST-RISK",
        status=Status.SUCCESS,
        message="Infrastructure cost within limits",
        logs=[f"Estimated monthly cost: ${total}", *logs],
    )
