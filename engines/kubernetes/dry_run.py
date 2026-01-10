from core.models.result import ExecutionResult, Status
import subprocess
import os


def kubernetes_dry_run(intent: dict) -> ExecutionResult:
    k8s = intent.get("kubernetes", {})
    path = k8s.get("manifests_path")

    if not path or not os.path.isdir(path):
        return ExecutionResult(
            stage="K8S-DRY-RUN",
            status=Status.BLOCKED,
            message="Kubernetes manifests path not found",
            logs=[f"path={path}"],
        )

    try:
        cmd = [
            "kubectl",
            "apply",
            "--dry-run=server",
            "-f",
            path,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return ExecutionResult(
                stage="K8S-DRY-RUN",
                status=Status.BLOCKED,
                message="Kubernetes dry-run failed",
                logs=[result.stderr],
            )

        return ExecutionResult(
            stage="K8S-DRY-RUN",
            status=Status.SUCCESS,
            message="Kubernetes dry-run successful",
            logs=[result.stdout],
        )

    except FileNotFoundError:
        return ExecutionResult(
            stage="K8S-DRY-RUN",
            status=Status.BLOCKED,
            message="kubectl not found on system",
            logs=[],
        )
