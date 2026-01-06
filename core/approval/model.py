from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    HELD = "HELD"


@dataclass
class ApprovalRecord:
    execution_id: str
    status: ApprovalStatus
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    comment: Optional[str] = None
