def decide_build_strategy(app_meta: dict):
    if app_meta["lang"] in ["python", "node", "java"]:
        return "buildpack"
    return "unsupported"


def decide_test_strategy(app_meta: dict):
    if app_meta["runtime"] in ["spring", "node", "python"]:
        return ["smoke", "api"]
    return []


def decide_infra_profile(app_meta: dict, env: str):
    if env == "prod":
        return "web-ha"
    return "web-small"


def decide_deploy_target(app_meta: dict):
    return "kubernetes"
