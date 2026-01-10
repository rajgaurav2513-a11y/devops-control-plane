from core.models.result import ExecutionResult, Status
import os
import subprocess


def kubernetes_apply(intent: dict) -> ExecutionResult:
    k8s = intent.get("kubernetes", {})
    path = k8s.get("manifests_path")

    if not path or not os.path.isdir(path):
        return ExecutionResult(
            stage="K8S-APPLY",
            status=Status.BLOCKED,
            message="Kubernetes manifests path not found",
            logs=[f"path={path}"],
        )

    try:
        result = subprocess.run(
            ["kubectl", "apply", "-f", path],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return ExecutionResult(
                stage="K8S-APPLY",
                status=Status.BLOCKED,
                message="Kubernetes apply failed",
                logs=[result.stderr],
            )

        return ExecutionResult(
            stage="K8S-APPLY",
            status=Status.SUCCESS,
            message="Kubernetes apply successful",
            logs=[result.stdout],
        )

    except Exception as e:
        return ExecutionResult(
            stage="K8S-APPLY",
            status=Status.BLOCKED,
            message="Kubernetes apply exception",
            logs=[str(e)],
        )
