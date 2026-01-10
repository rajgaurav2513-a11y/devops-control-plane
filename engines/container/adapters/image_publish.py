import subprocess
from core.models.result import ExecutionResult, Status


def _run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def publish_image(intent: dict) -> ExecutionResult:
    image_cfg = intent.get("image", {}).get("publish", {})
    if not image_cfg.get("enabled"):
        return ExecutionResult(
            stage="IMAGE-PUBLISH",
            status=Status.SKIPPED,
            message="Image publish disabled",
        )

    src_image = image_cfg.get("source_image")
    target = image_cfg.get("target")

    if not src_image or not target:
        return ExecutionResult(
            stage="IMAGE-PUBLISH",
            status=Status.BLOCKED,
            message="Missing source_image or target",
        )

    logs = []

    # 1. Docker tag
    code, out, err = _run(["docker", "tag", src_image, target])
    if code != 0:
        return ExecutionResult(
            stage="IMAGE-PUBLISH",
            status=Status.BLOCKED,
            message="Docker tag failed",
            logs=[err],
        )
    logs.append(f"Tagged {src_image} → {target}")

    # 2. Docker push
    code, out, err = _run(["docker", "push", target])
    if code != 0:
        return ExecutionResult(
            stage="IMAGE-PUBLISH",
            status=Status.BLOCKED,
            message="Docker push failed",
            logs=[err],
        )

    logs.append(out)

    return ExecutionResult(
        stage="IMAGE-PUBLISH",
        status=Status.SUCCESS,
        message="Image published successfully",
        logs=logs,
    )
