from core.models.result import ExecutionResult, Status
from engines.container.detector import detect_language

from engines.container.adapters import java
from engines.container.adapters import python as python_adapter
from engines.container.adapters import node


def build_image(intent: dict) -> ExecutionResult:
    """
    Detects application language and dispatches to the correct build adapter.
    Returns an ExecutionResult.
    """
    language = detect_language()

    if language.startswith("java"):
        return java.run_build(intent)

    if language == "python":
        return python_adapter.run_build(intent)

    if language == "node":
        return node.run_build(intent)

    return ExecutionResult(
        stage="BUILD",
        status=Status.BLOCKED,
        message="Unsupported application language",
        logs=[f"Detected language: {language}"],
        action="Add a build adapter for this language",
    )
