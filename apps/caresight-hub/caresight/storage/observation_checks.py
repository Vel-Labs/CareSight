from __future__ import annotations

from typing import Any


def observation_check_identity(check: dict[str, Any]) -> dict[str, Any]:
    return {
        "check_id": check["check_id"],
        "check_type": check["check_type"],
        "status": check["status"],
    }
