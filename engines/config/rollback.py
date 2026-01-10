import json
from core.models.result import ExecutionResult, Status
from engines.config.ssh_engine import _ssh_exec


def rollback_config(intent: dict) -> ExecutionResult:
    rollback = intent.get("rollback", {})
    host = rollback.get("host")
    snapshot_file = rollback.get("snapshot")

    conn = intent.get("config", {}).get("connection", {})
    user = conn.get("user")
    key = conn.get("key_path")

    if not host or not snapshot_file:
        return ExecutionResult(
            stage="CONFIG-ROLLBACK",
            status=Status.BLOCKED,
            message="Missing rollback host or snapshot",
        )

    try:
        with open(snapshot_file) as f:
            data = json.load(f)

        # Minimal rollback example (services only)
        for line in data.get("services", "").splitlines():
            if "enabled" in line:
                svc = line.split()[0]
                _ssh_exec(host, user, key, f"sudo systemctl enable {svc}")

        return ExecutionResult(
            stage="CONFIG-ROLLBACK",
            status=Status.SUCCESS,
            message="Rollback completed",
            logs=[f"host={host}", f"snapshot={snapshot_file}"],
        )

    except Exception as e:
        return ExecutionResult(
            stage="CONFIG-ROLLBACK",
            status=Status.BLOCKED,
            message="Rollback failed",
            logs=[str(e)],
        )
