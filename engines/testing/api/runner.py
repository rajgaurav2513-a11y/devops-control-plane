import requests
from core.models.result import ExecutionResult, Status


def run_api_tests(cfg: dict) -> ExecutionResult:
    base = cfg.get("target")
    logs = []

    for test in cfg.get("api", []):
        url = base + test["path"]
        r = requests.request(
            method=test.get("method", "GET"),
            url=url,
            headers=test.get("headers", {}),
            json=test.get("body"),
            timeout=5,
        )

        logs.append(f"{test['method']} {url} → {r.status_code}")
        if r.status_code != test.get("expect_status", 200):
            return ExecutionResult("TEST", Status.FAILED, "API test failed", logs)

    return ExecutionResult("TEST", Status.SUCCESS, "API tests passed", logs)
