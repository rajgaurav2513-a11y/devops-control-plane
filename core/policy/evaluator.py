from typing import List
from core.models.result import ExecutionResult, Status
from core.policy.model import Policy


def evaluate_policies(intent: dict) -> List[ExecutionResult]:
    results = []

    raw_policies = intent.get("policies", [])
    if not raw_policies:
        return results

    for p in raw_policies:
        policy = Policy(
            id=p.get("id"),
            when=p.get("when", {}),
            action=p.get("action", "WARN"),
            message=p.get("message", ""),
        )

        violated = True
        for key, expected in policy.when.items():
            if intent.get(key) != expected:
                violated = False
                break

        if violated:
            status = Status.BLOCKED if policy.action == "BLOCK" else Status.WARNING
            results.append(
                ExecutionResult(
                    stage="POLICY",
                    status=status,
                    message=f"Policy triggered: {policy.id}",
                    logs=[policy.message],
                )
            )

    return results
