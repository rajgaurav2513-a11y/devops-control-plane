from core.models.result import ExecutionResult, Status
from core.policy.config_policies import evaluate_config_prod_policies


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

    # Generic intent policies
    for policy in policies:
        condition = policy.get("when", {})
        action = policy.get("action", "WARN")
        message = policy.get("message", "")
        policy_id = policy.get("id", "unknown-policy")

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

    # CONFIG prod-safety policies
    config_results = evaluate_config_prod_policies(intent)
    for r in config_results:
        if r.status == Status.BLOCKED:
            return [r]

    status = Status.BLOCKED if blocked else Status.WARNING if triggered else Status.SUCCESS

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
