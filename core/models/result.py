from enum import Enum
from typing import List, Optional, Dict


class Status(str, Enum):
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"


class ExecutionResult:
    def __init__(
        self,
        stage: str,
        status: Status,
        message: str = "",

        # Existing fields (unchanged)
        logs: Optional[List[str]] = None,
        action: Optional[str] = None,
        policy_report: Optional[Dict] = None,

        # ============================
        # NEW (OPTIONAL, SAFE)
        # ============================
        reason: Optional[str] = None,   # machine-readable cause
        hint: Optional[str] = None,     # human-readable fix
        where: Optional[str] = None,    # failure location
    ):
        self.stage = stage
        self.status = status
        self.message = message

        self.logs = logs or []
        self.action = action
        self.policy_report = policy_report

        # New optional attributes
        self.reason = reason
        self.hint = hint
        self.where = where

    def to_dict(self):
        data = {
            "stage": self.stage,
            "status": self.status.value,
            "message": self.message,
            "logs": self.logs,
            "action": self.action,
            "policy_report": self.policy_report,
        }

        # ============================
        # Optional debug clarity
        # ============================
        if self.reason:
            data["reason"] = self.reason
        if self.hint:
            data["hint"] = self.hint
        if self.where:
            data["where"] = self.where

        return data
