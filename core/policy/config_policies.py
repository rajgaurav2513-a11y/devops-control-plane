from core.models.result import ExecutionResult, Status


FORBIDDEN_PACKAGES_PROD = {"kernel", "openssh", "docker"}
FORBIDDEN_SERVICES_PROD = {"ssh", "sshd", "kubelet", "docker"}
MAX_BATCH_PROD = 10
MAX_HOSTS_PROD = 20


def evaluate_config_prod_policies(intent: dict) -> list[ExecutionResult]:
    results = []

    env = intent.get("environment")
    cfg = intent.get("config")

    if not cfg:
        return results

    # Only enforce prod safety
    if env != "prod":
        return results

    # 1. Approval required
    approval = intent.get("approval", {})
    if not approval.get("approved"):
        results.append(
            ExecutionResult(
                stage="POLICY",
                status=Status.BLOCKED,
                message="Prod config requires approval",
                logs=["approval.missing=true"],
            )
        )
        return results

    # 2. Blast radius checks
    hosts = cfg.get("targets", {}).get("hosts", [])
    batch = cfg.get("rollout", {}).get("batch_size", 0)

    if len(hosts) > MAX_HOSTS_PROD:
        results.append(
            ExecutionResult(
                stage="POLICY",
                status=Status.BLOCKED,
                message="Too many hosts targeted in prod",
                logs=[f"hosts={len(hosts)} max={MAX_HOSTS_PROD}"],
            )
        )
        return results

    if batch > MAX_BATCH_PROD:
        results.append(
            ExecutionResult(
                stage="POLICY",
                status=Status.BLOCKED,
                message="Batch size too large for prod",
                logs=[f"batch={batch} max={MAX_BATCH_PROD}"],
            )
        )
        return results

    # 3. Forbidden packages
    pkgs = set(cfg.get("os", {}).get("packages", {}).get("install", []))
    forbidden = pkgs & FORBIDDEN_PACKAGES_PROD
    if forbidden:
        results.append(
            ExecutionResult(
                stage="POLICY",
                status=Status.BLOCKED,
                message="Forbidden package install in prod",
                logs=[f"packages={list(forbidden)}"],
            )
        )
        return results

    # 4. Forbidden service restarts
    services = cfg.get("services", {})
    bad_services = set(services.keys()) & FORBIDDEN_SERVICES_PROD
    if bad_services:
        results.append(
            ExecutionResult(
                stage="POLICY",
                status=Status.BLOCKED,
                message="Forbidden service operation in prod",
                logs=[f"services={list(bad_services)}"],
            )
        )
        return results

    return results
