def generate_dockerfile(language: str) -> str:
    """
    Generic Dockerfile.
    Entry point is decided at runtime via docker run / CMD override.
    """

    # Minimal universal base images
    if language == "python":
        return """
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt || true
CMD ["sh"]
"""

    if language == "node":
        return """
FROM node:20-alpine
WORKDIR /app
COPY . .
RUN npm install || true
CMD ["sh"]
"""

    if language.startswith("java"):
        return """
FROM eclipse-temurin:17-jre
WORKDIR /app
COPY . .
CMD ["sh"]
"""

    # Fallback: totally generic
    return """
FROM alpine:latest
WORKDIR /app
COPY . .
CMD ["sh"]
"""
