from core.models.result import ExecutionResult, Status


def evaluate_public_exposure(plan: dict) -> ExecutionResult:
    exposures = []

    for rc in plan.get("resource_changes", []):
        rtype = rc.get("type")
        after = rc.get("change", {}).get("after", {}) or {}

        if rtype in ("aws_security_group", "aws_security_group_rule"):
            for rule in after.get("ingress", []):
                if "0.0.0.0/0" in rule.get("cidr_blocks", []):
                    exposures.append(
                        f"{rc.get('address')} allows ingress from 0.0.0.0/0"
                    )

        if rtype == "aws_instance":
            if after.get("associate_public_ip_address") is True:
                exposures.append(
                    f"{rc.get('address')} has public IP enabled"
                )

    if exposures:
        return ExecutionResult(
            stage="INFRA-PUBLIC-RISK",
            status=Status.BLOCKED,
            message="Public exposure detected in infrastructure plan",
            logs=exposures,
        )

    return ExecutionResult(
        stage="INFRA-PUBLIC-RISK",
        status=Status.SUCCESS,
        message="No public exposure detected",
        logs=[],
    )
