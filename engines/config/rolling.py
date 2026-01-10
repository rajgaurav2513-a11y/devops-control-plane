from core.models.result import ExecutionResult, Status
from engines.config.ssh_engine import apply_config
from engines.config.rollback import rollback_config


def rolling_apply(intent: dict) -> ExecutionResult:
    cfg = intent.get("config", {})
    hosts = cfg.get("targets", {}).get("hosts", [])
    rollout = cfg.get("rollout", {})

    batch_size = rollout.get("batch_size", len(hosts))
    pause_on_failure = rollout.get("pause_on_failure", True)

    logs = []

    for i in range(0, len(hosts), batch_size):
        batch = hosts[i:i + batch_size]

        sub_intent = dict(intent)
        sub_intent["config"] = dict(cfg)
        sub_intent["config"]["targets"] = {"hosts": batch}

        r = apply_config(sub_intent)
        logs.extend(r.logs or [])

        if r.status == Status.BLOCKED:
            if pause_on_failure:
                # AUTO ROLLBACK
                for h in batch:
                    rb_intent = {
                        "rollback": {
                            "host": h,
                            "snapshot": next(
                                (l.split("=")[1] for l in logs if l.startswith(f"{h}: snapshot")),
                                None
                            )
                        },
                        "config": cfg,
                    }
                    rollback_config(rb_intent)

                return ExecutionResult(
                    stage="CONFIG-ROLLING",
                    status=Status.BLOCKED,
                    message="Rolling config failed and rollback executed",
                    logs=logs,
                )

    return ExecutionResult(
        stage="CONFIG-ROLLING",
        status=Status.SUCCESS,
        message="Rolling configuration completed",
        logs=logs,
    )
