from core.models.result import ExecutionResult, Status


def normalize_error(stage: str, exc: Exception) -> ExecutionResult:
    msg = str(exc)

    reason = "UNKNOWN_ERROR"
    hint = "Check logs for more details"
    where = None

    # ---- Docker / Container ----
    if "docker" in msg.lower():
        reason = "DOCKER_ERROR"
        hint = "Ensure Docker is running and accessible"

    if "imagepullbackoff" in msg.lower():
        reason = "IMAGE_PULL_FAILED"
        hint = "Verify image tag exists in registry"

    # ---- Terraform / Infra ----
    if "terraform" in msg.lower():
        reason = "TERRAFORM_ERROR"
        hint = "Run terraform plan locally to inspect issue"

    # ---- Kubernetes ----
    if "kubectl" in msg.lower():
        reason = "KUBERNETES_ERROR"
        hint = "Check cluster access and namespace"

    # ---- SSH / Config ----
    if "ssh" in msg.lower():
        reason = "SSH_ERROR"
        hint = "Verify host reachability and SSH credentials"

    return ExecutionResult(
        stage=stage,
        status=Status.FAILED,
        message="Execution failed",
        reason=reason,
        hint=hint,
        where=where,
        logs=[msg]
    )
