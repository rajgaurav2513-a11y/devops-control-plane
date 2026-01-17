import time
from dataclasses import dataclass
from typing import List, Optional, Dict


# =========================
# BASIC METRIC STRUCTURE
# =========================

@dataclass
class MetricPoint:
    timestamp: float
    value: float


class MetricSeries:
    """
    In-memory ring buffer for a single metric.
    Stores last N points only.
    """

    def __init__(self, name: str, max_points: int = 60):
        self.name = name
        self.max_points = max_points
        self.points: List[MetricPoint] = []

    def add(self, value: float):
        self.points.append(
            MetricPoint(timestamp=time.time(), value=value)
        )
        if len(self.points) > self.max_points:
            self.points.pop(0)

    def latest(self) -> Optional[float]:
        if not self.points:
            return None
        return self.points[-1].value

    def last_n(self, n: int) -> List[float]:
        return [p.value for p in self.points[-n:]]

    def is_empty(self) -> bool:
        return len(self.points) == 0


# =========================
# METRIC CATEGORIES
# =========================

# Infra-level metrics
infra_metrics: Dict[str, MetricSeries] = {
    "cpu_percent": MetricSeries("cpu_percent"),
    "memory_percent": MetricSeries("memory_percent"),
    "disk_percent": MetricSeries("disk_percent"),
    "node_reachable": MetricSeries("node_reachable"),  # 1 = up, 0 = down
}

# Application-level metrics
app_metrics: Dict[str, MetricSeries] = {
    "error_rate": MetricSeries("error_rate"),
    "restart_count": MetricSeries("restart_count"),
    "health_status": MetricSeries("health_status"),  # 1 = healthy, 0 = unhealthy
}

# Deployment metrics
deploy_metrics: Dict[str, MetricSeries] = {
    "deploy_success": MetricSeries("deploy_success"),  # 1 / 0
    "deploy_duration": MetricSeries("deploy_duration"),
    "recent_failures": MetricSeries("recent_failures"),
}

# Config rollout metrics
config_metrics: Dict[str, MetricSeries] = {
    "rollout_success": MetricSeries("rollout_success"),  # 1 / 0
    "partial_rollout": MetricSeries("partial_rollout"),  # 1 / 0
}

# Infra / IaC metrics
iac_metrics: Dict[str, MetricSeries] = {
    "terraform_plan_error": MetricSeries("terraform_plan_error"),  # 1 / 0
    "drift_detected": MetricSeries("drift_detected"),              # 1 / 0
}


# =========================
# GLOBAL REGISTRY
# =========================

METRICS = {
    "infra": infra_metrics,
    "app": app_metrics,
    "deploy": deploy_metrics,
    "config": config_metrics,
    "iac": iac_metrics,
}


# =========================
# SAFE ACCESS HELPERS
# =========================

def add_metric(category: str, name: str, value: float):
    """
    Safe metric write helper.
    Missing metrics are ignored (never crash control plane).
    """
    try:
        METRICS[category][name].add(value)
    except KeyError:
        pass


def get_latest(category: str, name: str) -> Optional[float]:
    try:
        return METRICS[category][name].latest()
    except KeyError:
        return None
