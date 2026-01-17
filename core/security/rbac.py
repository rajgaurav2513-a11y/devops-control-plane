from enum import Enum
from typing import Dict


# =========================
# ROLES
# =========================
class Role(str, Enum):
    DEVELOPER = "developer"
    OPS = "ops"
    ADMIN = "admin"


# =========================
# PERMISSIONS
# =========================
PERMISSIONS = {
    "EXECUTE_LOW_RISK": [Role.DEVELOPER, Role.OPS, Role.ADMIN],
    "EXECUTE_MEDIUM_RISK": [Role.OPS, Role.ADMIN],
    "EXECUTE_HIGH_RISK": [Role.ADMIN],

    "OVERRIDE_WARN": [Role.OPS, Role.ADMIN],
    "APPROVE_BLOCK": [Role.ADMIN],

    "TRIGGER_ROLLBACK": [Role.OPS, Role.ADMIN],
}


# =========================
# RBAC DECISION ENGINE
# =========================
def check_permission(
    user_role: str,
    action: str
) -> Dict:
    allowed_roles = PERMISSIONS.get(action, [])

    if Role(user_role) in allowed_roles:
        return {
            "allowed": True,
            "reason": f"{user_role} permitted for {action}"
        }

    return {
        "allowed": False,
        "reason": f"{user_role} NOT permitted for {action}"
    }
