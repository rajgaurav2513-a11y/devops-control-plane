import json
from pathlib import Path
from datetime import datetime
from core.approval.model import ApprovalRecord, ApprovalStatus

APPROVAL_DIR = Path("state/approvals")
APPROVAL_DIR.mkdir(parents=True, exist_ok=True)

def _path(execution_id: str) -> Path:
    return APPROVAL_DIR / f"{execution_id}.json"

def save(record: ApprovalRecord):
    data = {
        "execution_id": record.execution_id,
        "status": record.status.value,
        "decided_by": record.decided_by,
        "decided_at": record.decided_at.isoformat() if record.decided_at else None,
        "comment": record.comment,
    }
    _path(record.execution_id).write_text(json.dumps(data, indent=2))

def load(execution_id: str) -> ApprovalRecord | None:
    p = _path(execution_id)
    if not p.exists():
        return None

    data = json.loads(p.read_text())
    return ApprovalRecord(
        execution_id=data["execution_id"],
        status=ApprovalStatus(data["status"]),
        decided_by=data.get("decided_by"),
        decided_at=datetime.fromisoformat(data["decided_at"]) if data.get("decided_at") else None,
        comment=data.get("comment"),
    )
