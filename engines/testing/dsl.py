def parse_test_intent(intent: dict) -> dict:
    testing = intent.get("testing")
    if not testing or not testing.get("enabled"):
        return {}

    return {
        "type": testing.get("type", "smoke"),
        "target": testing.get("target"),
        "checks": testing.get("checks", []),
        "api": testing.get("api", []),
        "ui": testing.get("ui", []),
        "performance": testing.get("performance", {}),
        "browsers": testing.get("browsers", ["chrome"]),
    }
