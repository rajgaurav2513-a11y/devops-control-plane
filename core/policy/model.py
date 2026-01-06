from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Policy:
    id: str
    when: Dict[str, Any]
    action: str
    message: str
