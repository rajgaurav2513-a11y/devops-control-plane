# engines/deploy/local_auto.py

import subprocess
import os

from core.models.result import ExecutionResult, Status


def auto_deploy_local(intent: dict) -> ExecutionResult:
    app_cfg = intent.get("application", {})
    entrypoint = app_cfg.get("entrypoint", "app.py")

    if not os.path.exists(entrypoint):
        return ExecutionResult(
            stage="DEPLOY",
            status=Status.BLOCKED,
            message="Entrypoint not found for local auto-deploy",
            logs=[f"missing file: {entrypoint}"],
        )

    try:
        proc = subprocess.run(
            ["python", entrypoint],
            capture_output=True,
            text=True,
            check=True,
        )

        return ExecutionResult(
            stage="DEPLOY",
            status=Status.SUCCESS,
            message="Application auto-deployed locally",
            logs=proc.stdout.splitlines(),
        )

    except subprocess.CalledProcessError as e:
        return ExecutionResult(
            stage="DEPLOY",
            status=Status.BLOCKED,
            message="Local auto-deploy execution failed",
            logs=e.stderr.splitlines(),
        )
