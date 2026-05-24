from __future__ import annotations

from typing import Any


def appearance_profile_identity(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "appearance_profile_id": profile["appearance_profile_id"],
        "active_date": profile["active_date"],
        "descriptor_status": profile["descriptor_status"],
    }
