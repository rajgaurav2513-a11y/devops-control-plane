from core.models.result import ExecutionResult, Status
from engines.testing.dsl import parse_test_intent
from engines.testing.smoke.runner import run_smoke_tests
from engines.testing.api.runner import run_api_tests
from engines.testing.selenium.runner import run_ui_tests
from engines.testing.performance.runner import run_performance_tests


def run_tests(intent: dict) -> ExecutionResult:
    cfg = parse_test_intent(intent)
    if not cfg:
        return ExecutionResult("TEST", Status.SKIPPED, "No tests defined")

    t = cfg["type"]

    if t == "smoke":
        return run_smoke_tests(cfg)
    if t == "api":
        return run_api_tests(cfg)
    if t == "selenium":
        return run_ui_tests(cfg)
    if t == "performance":
        return run_performance_tests(cfg)

    return ExecutionResult("TEST", Status.SKIPPED, "Unknown test type")
