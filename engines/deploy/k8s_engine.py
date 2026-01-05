from core.models.result import ExecutionResult, Status


def deploy_app(intent: dict, image: str, deploy_type: str):
    if deploy_type == "none":
        return ExecutionResult(
            stage="DEPLOY",
            status=Status.SKIPPED,
            message="Deploy type is 'none'",
            logs=[],
        )

    if deploy_type == "local":
        return ExecutionResult(
            stage="DEPLOY",
            status=Status.SUCCESS,
            message=f"Local deployment simulated for image {image}",
            logs=[],
        )

    if deploy_type == "k8s":
        return ExecutionResult(
            stage="DEPLOY",
            status=Status.SUCCESS,
            message=f"Kubernetes deployment simulated for image {image}",
            logs=["cluster=eks-demo"],
        )

    return ExecutionResult(
        stage="DEPLOY",
        status=Status.FAILED,
        message=f"Unknown deploy type: {deploy_type}",
        logs=[],
        action="Fix deploy.type in intent",
    )
