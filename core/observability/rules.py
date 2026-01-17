from typing import Dict, List
from core.observability.metrics import METRICS


# =========================
# DECISION CONSTANTS
# =========================
ALLOW = "ALLOW"
WARN = "WARN"
DELAY = "DELAY"
BLOCK = "BLOCK"


# =========================
# RULE EVALUATION RESULT
# =========================
def decision(decision: str, reason: str) -> Dict:
    return {
        "decision": decision,
        "reason": reason
    }


# =========================
# HELPER FUNCTIONS
# =========================
def rising(values: List[float]) -> bool:
    if len(values) < 2:
        return False
    return values[-1] > values[0]


# =========================
# HEALTH RULE ENGINE
# =========================
def evaluate_health(environment: str) -> Dict:
    """
    Evaluates system health and returns
    ALLOW / WARN / DELAY / BLOCK with reason
    """

    # ---- Infra ----
    cpu = METRICS["infra"]["cpu_percent"].last_n(3)
    mem = METRICS["infra"]["memory_percent"].last_n(3)
    node = METRICS["infra"]["node_reachable"].latest()

    # ---- App ----
    error_rate = METRICS["app"]["error_rate"].last_n(3)
    app_health = METRICS["app"]["health_status"].latest()

    # ---- Deploy ----
    recent_failures = METRICS["deploy"]["recent_failures"].latest()

    # ---- IaC / Drift ----
    drift = METRICS["iac"]["drift_detected"].latest()
    plan_error = METRICS["iac"]["terraform_plan_error"].latest()

    # =========================
    # BLOCK RULES (HARD STOP)
    # =========================
    if node == 0:
        return decision(BLOCK, "Node unreachable")

    if environment == "prod" and app_health == 0:
        return decision(BLOCK, "Application unhealthy in production")

    if plan_error == 1:
        return decision(BLOCK, "Terraform plan error detected")

    if drift == 1 and environment == "prod":
        return decision(BLOCK, "Infra drift detected in production")

    # =========================
    # DELAY RULES
    # =========================
    if recent_failures and recent_failures >= 2:
        return decision(DELAY, "Multiple recent deployment failures")

    if cpu and all(v > 80 for v in cpu):
        return decision(DELAY, "Sustained high CPU usage")

    # =========================
    # WARN RULES
    # =========================
    if error_rate and rising(error_rate):
        return decision(WARN, "Application error rate increasing")

    if mem and all(v > 75 for v in mem):
        return decision(WARN, "High memory usage")

    if drift == 1:
        return decision(WARN, "Infra drift detected")

    # =========================
    # DEFAULT
    # =========================
    return decision(ALLOW, "System health stable")
