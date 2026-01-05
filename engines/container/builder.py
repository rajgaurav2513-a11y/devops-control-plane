from core.models.result import ExecutionResult
from engines.container.detector import detect_language
from engines.container.docker_builder import build_docker_image


def build_image(intent: dict) -> ExecutionResult:
    """
    Docker BUILD agent with artifact tagging
    """
    language = detect_language()
    app_name = intent.get("application", {}).get("name", "app").lower()
    artifact_tag = intent["_execution"]["artifact_tag"]

    image_name = f"{app_name}:{artifact_tag}"

    return build_docker_image(
        intent=intent,
        language=language,
        image_name=image_name,
    )
