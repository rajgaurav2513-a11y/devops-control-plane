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
        subprocess.call(
            ["docker", "rm", "-f", container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        container_id = subprocess.check_output(
            [
                "docker",
                "run",
                "-d",
                "--name",
                container_name,
                *port_args,
                image,
            ],
            stderr=subprocess.STDOUT,
        ).decode().strip()

        return ExecutionResult(
            stage="DEPLOY",
            status=Status.SUCCESS,
            message="Container deployed locally",
            logs=[f"container_id={container_id}"],
        )

    except subprocess.CalledProcessError as e:
        return ExecutionResult(
            stage="DEPLOY",
            status=Status.BLOCKED,
            message="Local docker deployment failed",
            logs=[e.output.decode() if e.output else str(e)],
        )
