import os
import subprocess
import tempfile

from core.models.result import ExecutionResult, Status
from engines.container.dockerfile_generator import generate_dockerfile


def build_docker_image(intent: dict, language: str, image_name: str) -> ExecutionResult:
    dockerfile_content = generate_dockerfile(language)

    if dockerfile_content is None:
        return ExecutionResult(
            stage="BUILD",
            status=Status.BLOCKED,
            message="Unsupported language for Docker build",
            logs=[f"Detected language: {language}"],
            action="Add Dockerfile support for this language",
        )

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # copy source code
            os.system(f"cp -r . {tmpdir}")

            dockerfile_path = os.path.join(tmpdir, "Dockerfile")
            with open(dockerfile_path, "w") as f:
                f.write(dockerfile_content)

            process = subprocess.Popen(
                ["docker", "build", "-t", image_name, tmpdir],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            logs = []
            for line in process.stdout:
                logs.append(line.strip())

            process.wait()

            if process.returncode != 0:
                return ExecutionResult(
                    stage="BUILD",
                    status=Status.FAILED,
                    message="Docker build failed",
                    logs=logs,
                    action="Fix Docker build errors and retry",
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
            action="Check Docker installation and permissions",
        )
