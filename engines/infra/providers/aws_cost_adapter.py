# engines/infra/providers/aws_cost_adapter.py
AWS_INSTANCE_MAP = {
    "t3.micro": "COMPUTE_SMALL",
    "t3.small": "COMPUTE_SMALL",
    "t3.medium": "COMPUTE_MEDIUM",
    "t3.large": "COMPUTE_MEDIUM",
    "t3.xlarge": "COMPUTE_LARGE",
}


def extract_aws_cost_resources(plan: dict) -> list:
    resources = []

    for rc in plan.get("resource_changes", []):
        if rc.get("type") != "aws_instance":
            continue

        after = rc.get("change", {}).get("after", {}) or {}
        itype = after.get("instance_type", "t3.medium")
        count = after.get("count", 1)

        klass = AWS_INSTANCE_MAP.get(itype, "COMPUTE_MEDIUM")

        resources.append(
            {
                "address": rc.get("address"),
                "class": klass,
                "count": count,
            }
        )

    return resources
