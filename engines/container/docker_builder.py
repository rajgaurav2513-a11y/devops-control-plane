import os
import subprocess
import tempfile
import shutil

from core.models.result import ExecutionResult, Status
from engines.container.dockerfile_generator import generate_dockerfile


def build_docker_image(intent: dict, language: str, image_name: str) -> ExecutionResult:
    logs = []

    dockerfile_content = generate_dockerfile(language)

    # Workspace always comes from executor (local or git)
    app_path = intent["_execution"].get("workspace")

    if not dockerfile_content:
        return ExecutionResult(
            stage="BUILD",
            status=Status.BLOCKED,
            message="Unsupported language for Docker build",
            logs=[f"language={language}"],
        )

    if not app_path or not os.path.isdir(app_path):
        return ExecutionResult(
            stage="BUILD",
            status=Status.FAILED,
            message="Invalid application workspace",
            logs=[f"workspace={app_path}"],
        )

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Copy source code to temp directory
            for item in os.listdir(app_path):
                if item in [".git", "__pycache__", ".venv", "venv"]:
                    continue

                src = os.path.join(app_path, item)
                dst = os.path.join(tmpdir, item)

                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)

            # Write generated Dockerfile
            dockerfile_path = os.path.join(tmpdir, "Dockerfile")
            with open(dockerfile_path, "w") as f:
                f.write(dockerfile_content)

            # Run Docker build
            process = subprocess.Popen(
                ["docker", "build", "-t", image_name, tmpdir],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            for line in process.stdout:
                logs.append(line.rstrip())

            process.wait()

            if process.returncode != 0:
                return ExecutionResult(
                    stage="BUILD",
                    status=Status.FAILED,
                    message="Docker build failed",
                    logs=logs,
                )

            return ExecutionResult(
                stage="BUILD",
                status=Status.SUCCESS,
                message=f"Docker image '{image_name}' built successfully",
                logs=logs,
            )

    except Exception as e:
        return ExecutionResult(
            stage="BUILD",
            status=Status.FAILED,
            message="Docker build execution error",
            logs=[str(e)],
        )
