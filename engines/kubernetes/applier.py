import subprocess
import tempfile
from core.models.result import ExecutionResult, Status
from engines.kubernetes.generator import generate_manifests


def apply(intent: dict) -> ExecutionResult:
    app = intent.get("application", {})
    app_name = app.get("name", "app").lower()
    env = intent.get("environment", "dev")

    exec_meta = intent["_execution"]
    image = exec_meta.get("image")

    if not image:
        return ExecutionResult(
            stage="DEPLOY",
            status=Status.BLOCKED,
            message="No image available for deployment",
        )

    manifests = generate_manifests(app_name, image, env)

    try:
        for manifest in manifests:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
                f.write(manifest)
                subprocess.check_call(["kubectl", "apply", "-f", f.name])

        return ExecutionResult(
            stage="DEPLOY",
            status=Status.SUCCESS,
            message="Application deployed to Kubernetes",
        )

    except subprocess.CalledProcessError as e:
        return ExecutionResult(
            stage="DEPLOY",
            status=Status.BLOCKED,
            message="Kubernetes deployment failed",
            logs=[str(e)],
        )
