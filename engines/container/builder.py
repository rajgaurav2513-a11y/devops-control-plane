import os
import subprocess
from core.models.result import ExecutionResult, Status


def _dockerfile_exists(workspace: str) -> bool:
    return os.path.exists(os.path.join(workspace, "Dockerfile"))


def _build_with_dockerfile(intent: dict, image_name: str) -> ExecutionResult:
    workspace = intent["_execution"]["workspace"]

    cmd = ["docker", "build", "-t", image_name, workspace]
    r = subprocess.run(cmd, capture_output=True, text=True)

    if r.returncode != 0:
        return ExecutionResult(
            stage="BUILD",
            status=Status.BLOCKED,
            message="Docker build failed",
            logs=[r.stderr],
        )

    return ExecutionResult(
        stage="BUILD",
        status=Status.SUCCESS,
        message="Image built using Dockerfile",
        logs=[r.stdout],
    )


def _build_with_buildpacks(intent: dict, image_name: str) -> ExecutionResult:
    workspace = intent["_execution"]["workspace"]

    cmd = [
        "pack",
        "build",
        image_name,
        "--path",
        workspace,
        "--builder",
        "paketobuildpacks/builder:base",
    ]

    r = subprocess.run(cmd, capture_output=True, text=True)

    if r.returncode != 0:
        return ExecutionResult(
            stage="BUILD",
            status=Status.BLOCKED,
            message="Buildpack build failed",
            logs=[r.stderr],
        )

    return ExecutionResult(
        stage="BUILD",
        status=Status.SUCCESS,
        message="Image built using Cloud Native Buildpacks",
        logs=[r.stdout],
    )


def build_image(intent: dict) -> ExecutionResult:
    """
    FINAL BUILD ENGINE
    - No Dockerfile required
    - Auto-detects best build strategy
    - Platform-owned logic
    """

    app = intent.get("application", {})
    app_name = app.get("name", "app").lower()

    exec_meta = intent["_execution"]
    workspace = exec_meta.get("workspace")
    artifact_tag = exec_meta.get("artifact_tag", exec_meta.get("id"))

    if not workspace or not os.path.isdir(workspace):
        return ExecutionResult(
            stage="BUILD",
            status=Status.BLOCKED,
            message="Workspace not available for build",
        )

    image_name = f"{app_name}:{artifact_tag}"

    # -------------------------
    # STRATEGY DECISION
    # -------------------------
    if _dockerfile_exists(workspace):
        return _build_with_dockerfile(intent, image_name)

    # Default, platform-owned strategy
    return _build_with_buildpacks(intent, image_name)
