import subprocess
from core.models.result import ExecutionResult, Status


def run_performance_tests(cfg: dict) -> ExecutionResult:
    perf = cfg.get("performance", {})
    users = perf.get("users", 50)
    duration = perf.get("duration", "1m")

    cmd = ["k6", "run", "--vus", str(users), "--duration", duration, "perf.js"]

    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if r.returncode != 0:
        return ExecutionResult(
            "TEST", Status.FAILED, "Performance test failed", [r.stderr]
        )

    return ExecutionResult(
        "TEST", Status.SUCCESS, "Performance tests passed", [r.stdout]
    )
