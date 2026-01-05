def normalize_plan(plan: dict) -> dict:
    """
    Normalize terraform plan JSON into decision-friendly summary.
    """

    summary = {
        "create": 0,
        "update": 0,
        "delete": 0,
        "replace": 0,
        "resources": [],
    }

    for rc in plan.get("resource_changes", []):
        actions = rc.get("change", {}).get("actions", [])
        res_type = rc.get("type")
        address = rc.get("address")

        if actions == ["create"]:
            summary["create"] += 1
        elif actions == ["update"]:
            summary["update"] += 1
        elif actions == ["delete"]:
            summary["delete"] += 1
        elif actions == ["create", "delete"]:
            summary["replace"] += 1

        summary["resources"].append(
            {
                "address": address,
                "type": res_type,
                "actions": actions,
            }
        )

    return summary
