import os


def detect_language(source_path: str = ".") -> str:
    """
    Detect application language based on common build files.
    """
    files = os.listdir(source_path)

    if "pom.xml" in files:
        return "java-maven"

    if "build.gradle" in files:
        return "java-gradle"

    if "requirements.txt" in files or "pyproject.toml" in files:
        return "python"

    if "package.json" in files:
        return "node"

    return "unknown"
