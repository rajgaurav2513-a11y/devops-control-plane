# core/approvals/store.py

_approvals = {}


def request_approval(execution_id: str, stage: str):
    if execution_id not in _approvals:
        _approvals[execution_id] = {
            "stage": stage,
            "decision": "PENDING",   # PENDING | APPROVED | REJECTED | HELD
        }


def approve(execution_id: str):
    if execution_id in _approvals:
        _approvals[execution_id]["decision"] = "APPROVED"


def reject(execution_id: str):
    if execution_id in _approvals:
        _approvals[execution_id]["decision"] = "REJECTED"


def hold(execution_id: str):
    if execution_id in _approvals:
        _approvals[execution_id]["decision"] = "HELD"


def get_decision(execution_id: str):
    return _approvals.get(execution_id, {}).get("decision")


def get_stage(execution_id: str):
    return _approvals.get(execution_id, {}).get("stage")
