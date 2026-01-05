import subprocess
import time

from core.models.result import ExecutionResult, Status


def run_container(intent: dict, image_name: str, wait_seconds: int = 5) -> ExecutionResult:
    container_id = None
    logs = []

    env_vars = intent.get("env", {})
    env_flags = []

    for k, v in env_vars.items():
        env_flags.extend(["-e", f"{k}={v}"])

    run_cfg = intent.get("run", {})
    command = run_cfg.get("command")

    if not command:
        return ExecutionResult(
            stage="RUN",
            status=Status.BLOCKED,
            message="run.command not specified in intent",
            logs=[],
            action="Add run.command to intent",
        )

    try:
        container_id = subprocess.check_output(
            [
                "docker",
                "run",
                "-d",
                *env_flags,
                image_name,
                *command,
            ],
            text=True,
        ).strip()

        logs.append(f"Container started: {container_id}")
        logs.append(f"Run command: {' '.join(command)}")
        logs.append(f"Injected env vars: {env_vars}")

        time.sleep(wait_seconds)

        container_logs = subprocess.check_output(
            ["docker", "logs", container_id],
            text=True,
            stderr=subprocess.STDOUT,
        )

        logs.append("---- Container Logs ----")
        logs.extend(container_logs.splitlines())

        running = subprocess.check_output(
            ["docker", "ps", "-q", "-f", f"id={container_id}"],
            text=True,
        ).strip()

        if running:
            return ExecutionResult(
                stage="RUN",
                status=Status.SUCCESS,
                message="Container running (service workload)",
                logs=logs,
            )

        exit_code = subprocess.check_output(
            ["docker", "inspect", container_id, "--format={{.State.ExitCode}}"],
            text=True,
        ).strip()

        if exit_code == "0":
            return ExecutionResult(
                stage="RUN",
                status=Status.SUCCESS,
                message="Container ran successfully and exited cleanly (batch workload)",
                logs=logs,
            )

        return ExecutionResult(
            stage="RUN",
            status=Status.FAILED,
            message=f"Container exited with code {exit_code}",
            logs=logs,
            action="Fix runtime command or application errors",
        )

    except Exception as e:
        logs.append(str(e))
        return ExecutionResult(
            stage="RUN",
            status=Status.FAILED,
            message="Docker run failed",
            logs=logs,
        )

    finally:
        if container_id:
            subprocess.call(["docker", "stop", container_id])
            subprocess.call(["docker", "rm", container_id])
            logs.append("Container stopped and removed")
