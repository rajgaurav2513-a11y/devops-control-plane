import subprocess

from core.models.result import ExecutionResult, Status


def deploy_local(intent: dict, image: str) -> ExecutionResult:
    deploy_cfg = intent.get("deploy", {})
    ports = deploy_cfg.get("ports", [])

    port_args = []
    for p in ports:
        port_args.extend(["-p", p])

    execution_id = intent["_execution"]["id"]
    container_name = f"{execution_id}-local"

    try:
        # Remove existing container if present
        subprocess.call(
            ["docker", "rm", "-f", container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Run container in detached (service) mode
        container_id = subprocess.check_output(
            ["docker", "run", "-d", "--name", container_name, *port_args, image],
            text=True,
        ).strip()

        logs = [
            f"container_name={container_name}",
            f"container_id={container_id}",
        ]

        for p in ports:
            host_port = p.split(":")[0]
            logs.append(f"http://localhost:{host_port}")

        return ExecutionResult(
            stage="DEPLOY",
            status=Status.SUCCESS,
            message="Application deployed locally",
            logs=logs,
        )

    except Exception as e:
        return ExecutionResult(
            stage="DEPLOY",
            status=Status.FAILED,
            message="Local Docker deployment failed",
            logs=[str(e)],
        )
