import requests
import socket
from core.models.result import ExecutionResult, Status


def run_smoke_tests(cfg: dict) -> ExecutionResult:
    target = cfg.get("target")
    checks = cfg.get("checks", [])
    logs = []

    if not target:
        return ExecutionResult("TEST", Status.BLOCKED, "Smoke test target missing")

    for check in checks:
        if check["type"] == "http":
            url = target + check.get("path", "")
            r = requests.get(url, timeout=5)
            logs.append(f"GET {url} → {r.status_code}")
            if r.status_code != check.get("expect", 200):
                return ExecutionResult("TEST", Status.FAILED, "HTTP smoke failed", logs)

        if check["type"] == "tcp":
            host, port = target.split(":")
            socket.create_connection((host, int(port)), timeout=5)
            logs.append(f"TCP {host}:{port} OK")

    return ExecutionResult("TEST", Status.SUCCESS, "Smoke tests passed", logs)
