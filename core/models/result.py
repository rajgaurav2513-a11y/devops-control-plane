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
        logs: Optional[List[str]] = None,
        action: Optional[str] = None,
        policy_report: Optional[Dict] = None,
    ):
        self.stage = stage
        self.status = status
        self.message = message
        self.logs = logs or []
        self.action = action
        self.policy_report = policy_report

    def to_dict(self):
        return {
            "stage": self.stage,
            "status": self.status.value,
            "message": self.message,
            "logs": self.logs,
            "action": self.action,
            "policy_report": self.policy_report,
        }
