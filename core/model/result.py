from enum import Enum
from typing import List, Optional


class Status(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class ExecutionResult:
    def __init__(
        self,
        stage: str,
        status: Status,
        message: str,
        logs: Optional[List[str]] = None,
        action: Optional[str] = None,
    ):
        self.stage = stage
        self.status = status
        self.message = message
        self.logs = logs or []
        self.action = action

    def to_dict(self):
        return {
            "stage": self.stage,
            "status": self.status.value,
            "message": self.message,
            "logs": self.logs,
            "action": self.action,
        }
