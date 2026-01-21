import subprocess
from core.models.result import ExecutionResult, Status


def run_quality_checks(intent: dict) -> ExecutionResult:
    app = intent.get("application", {})
    path = app.get("path")

    if not path:
        return ExecutionResult("QUALITY", Status.SKIPPED, "No app path")

    r = subprocess.run(
        ["python", "-m", "py_compile", "."],
        cwd=path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if r.returncode != 0:
        return ExecutionResult(
            "QUALITY", Status.FAILED, "Quality checks failed", [r.stderr]
        )

    return ExecutionResult("QUALITY", Status.SUCCESS, "Quality checks passed")
