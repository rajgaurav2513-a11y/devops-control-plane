
def apply_policies(intent):
    if intent.get("environment", {}).get("name") == "prod":
        intent.setdefault("deployment", {})["replicas"] = max(
            2, intent.get("deployment", {}).get("replicas", 1)
        )
    return intent
