import paramiko
from core.models.result import ExecutionResult, Status
from state.config_snapshots import save_config_snapshot


def _ssh_exec(host, user, key, command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=user, key_filename=key, timeout=10)
    stdin, stdout, stderr = client.exec_command(command)
    out = stdout.read().decode()
    err = stderr.read().decode()
    client.close()
    return out.strip(), err.strip()


def _capture_state(host, user, key):
    pkgs, _ = _ssh_exec(host, user, key, "dpkg -l")
    services, _ = _ssh_exec(host, user, key, "systemctl list-unit-files")
    return {
        "packages": pkgs,
        "services": services,
    }


def apply_config(intent: dict) -> ExecutionResult:
    cfg = intent.get("config", {})
    targets = cfg.get("targets", {}).get("hosts", [])
    conn = cfg.get("connection", {})
    user = conn.get("user")
    key = conn.get("key_path")

    logs = []

    try:
        for host in targets:
            # SNAPSHOT BEFORE CHANGE
            snapshot = _capture_state(host, user, key)
            snap_path = save_config_snapshot(host, snapshot)
            logs.append(f"{host}: snapshot={snap_path}")

            # PACKAGES
            for pkg in cfg.get("os", {}).get("packages", {}).get("install", []):
                _ssh_exec(host, user, key, f"sudo apt-get install -y {pkg}")
                logs.append(f"{host}: installed {pkg}")

            # SERVICES
            for svc, meta in cfg.get("services", {}).items():
                if meta.get("enable"):
                    _ssh_exec(host, user, key, f"sudo systemctl enable {svc}")
                if meta.get("state") == "running":
                    _ssh_exec(host, user, key, f"sudo systemctl start {svc}")
                logs.append(f"{host}: service {svc} running")

        return ExecutionResult(
            stage="CONFIG-APPLY",
            status=Status.SUCCESS,
            message="Configuration applied",
            logs=logs,
        )

    except Exception as e:
        return ExecutionResult(
            stage="CONFIG-APPLY",
            status=Status.BLOCKED,
            message="Configuration failed",
            logs=[str(e)],
        )
