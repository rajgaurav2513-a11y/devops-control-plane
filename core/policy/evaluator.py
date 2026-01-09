from core.models.result import ExecutionResult, Status


def _get_nested(data: dict, key: str):
    cur = data
    for part in key.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def evaluate_policies(intent: dict):
    policies = intent.get("policies", [])
    triggered = []
    blocked = False

    for policy in policies:
        condition = policy.get("when", {})
        action = policy.get("action")
        message = policy.get("message", "")
        policy_id = policy.get("id")

        matched = True
        for key, expected in condition.items():
            if _get_nested(intent, key) != expected:
                matched = False
                break

        if matched:
            triggered.append({
                "policy_id": policy_id,
                "action": action,
                "message": message,
            })
            if action == "BLOCK":
                blocked = True

    if blocked:
        status = Status.BLOCKED
    elif triggered:
        status = Status.WARNING
    else:
        status = Status.SUCCESS

    return [
        ExecutionResult(
            stage="POLICY",
            status=status,
            message="Policy evaluation completed",
            policy_report={
                "total_policies": len(policies),
                "triggered": triggered,
                "blocked": blocked,
            },
        )
    ]
