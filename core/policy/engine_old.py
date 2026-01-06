from core.models.result import ExecutionResult, Status


def evaluate_policies(intent: dict) -> ExecutionResult:
    raw_policies = intent.get("policies", [])

    if not raw_policies:
        return ExecutionResult(
            stage="POLICY",
            status=Status.SUCCESS,
            message="No policies defined",
            logs=[],
        )

    logs: list[str] = []
    final_status = Status.SUCCESS

    for policy in raw_policies:
        name = policy.get("id", "unknown-policy")
        action = policy.get("action", "WARN")
        when = policy.get("when", {})

        violated = True
        for key, expected in when.items():
            actual = intent.get(key)
            if actual != expected:
                violated = False
                break

        logs.append(
            f"policy={name} action={action} violated={violated}"
        )

        if violated:
            if action == "BLOCK":
                final_status = Status.BLOCKED
                break
            if action == "WARN":
                final_status = Status.WARNING

    return ExecutionResult(
        stage="POLICY",
        status=final_status,
        message="Policy evaluation completed",
        logs=logs,
    )
