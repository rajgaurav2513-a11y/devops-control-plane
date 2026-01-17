import time
import subprocess
from core.observability.metrics import add_metric


# =========================
# INFRA COLLECTORS
# =========================

def collect_cpu_memory():
    """
    Collect CPU & memory using OS commands.
    Works on Linux / VM / local machine.
    """
    try:
        # CPU (1-minute load approximation)
        cpu = subprocess.getoutput("awk '{print $1*100}' /proc/loadavg")
        add_metric("infra", "cpu_percent", float(cpu))
    except Exception:
        pass

    try:
        mem = subprocess.getoutput(
            "free | awk '/Mem:/ {print ($3/$2)*100}'"
        )
        add_metric("infra", "memory_percent", float(mem))
    except Exception:
        pass


def collect_disk():
    try:
        disk = subprocess.getoutput(
            "df / | awk 'NR==2 {print $5}' | sed 's/%//'"
        )
        add_metric("infra", "disk_percent", float(disk))
    except Exception:
        pass


def collect_node_reachable():
    # If this code runs, node is reachable
    add_metric("infra", "node_reachable", 1)


# =========================
# APPLICATION COLLECTORS
# =========================

def collect_app_health(health_check_fn=None):
    """
    health_check_fn should return True / False
    """
    if not health_check_fn:
        return

    try:
        status = 1 if health_check_fn() else 0
        add_metric("app", "health_status", status)
    except Exception:
        add_metric("app", "health_status", 0)


def collect_error_rate(error_rate_fn=None):
    """
    error_rate_fn should return numeric error rate
    """
    if not error_rate_fn:
        return

    try:
        rate = error_rate_fn()
        add_metric("app", "error_rate", float(rate))
    except Exception:
        pass


# =========================
# DEPLOY / EXECUTION COLLECTORS
# =========================

def record_deploy_result(success: bool, duration: float):
    add_metric("deploy", "deploy_success", 1 if success else 0)
    add_metric("deploy", "deploy_duration", duration)

    if not success:
        add_metric("deploy", "recent_failures", 1)
    else:
        add_metric("deploy", "recent_failures", 0)


# =========================
# CONFIG COLLECTORS
# =========================

def record_config_rollout(success: bool, partial: bool = False):
    add_metric("config", "rollout_success", 1 if success else 0)
    add_metric("config", "partial_rollout", 1 if partial else 0)


# =========================
# INFRA / IAC COLLECTORS
# =========================

def record_terraform_plan_result(success: bool):
    add_metric("iac", "terraform_plan_error", 0 if success else 1)


def record_drift(drift_detected: bool):
    add_metric("iac", "drift_detected", 1 if drift_detected else 0)


# =========================
# MAIN COLLECT LOOP (OPTIONAL)
# =========================

def collect_all_basic():
    """
    Lightweight periodic collector.
    Can be called every 30–60 seconds.
    """
    collect_cpu_memory()
    collect_disk()
    collect_node_reachable()
