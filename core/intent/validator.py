from core.models.result import ExecutionResult, Status


def validate_intent(intent: dict) -> ExecutionResult:
    """
    Intent Validator (V1):
    - Validates configuration intent
    - Enforces required / forbidden config
    - Applies safe defaults
    - Decision-only (no execution, no mutation)
    """

    config = intent.get("config", {})
    runtime_config = intent.get("runtime_config", {})

    required = set(config.get("required", []))
    forbidden = set(config.get("forbidden", []))
    defaults = config.get("defaults", {})

    provided = set(runtime_config.keys())

    missing = required - provided
    illegal = forbidden & provided

    if missing:
        return ExecutionResult(
            stage="CONFIG",
            status=Status.BLOCKED,
            message="Missing required configuration",
            logs=[f"Missing config keys: {', '.join(sorted(missing))}"],
            action="Provide required configuration values and re-run",
        )

    if illegal:
        return ExecutionResult(
            stage="CONFIG",
            status=Status.BLOCKED,
            message="Forbidden configuration detected",
            logs=[f"Forbidden config keys present: {', '.join(sorted(illegal))}"],
            action="Remove forbidden configuration values",
        )

    applied = []
    for key, value in defaults.items():
        if key not in runtime_config:
            runtime_config[key] = value
            applied.append(key)

    return ExecutionResult(
        stage="CONFIG",
        status=Status.SUCCESS,
        message="Configuration validated successfully",
        logs=(
            [f"Defaults applied: {', '.join(applied)}"]
            if applied
            else ["All configuration values valid"]
        ),
    )
