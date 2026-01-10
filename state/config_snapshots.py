import json
import os
from datetime import datetime

SNAPSHOT_DIR = "state/config_snapshots"


def save_config_snapshot(host: str, snapshot: dict):
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    path = os.path.join(SNAPSHOT_DIR, f"{host}_{ts}.json")

    with open(path, "w") as f:
        json.dump(snapshot, f, indent=2)

    return path
