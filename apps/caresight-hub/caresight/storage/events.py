from __future__ import annotations

from typing import Any


def event_identity(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": event["event_id"],
        "event_type": event["event_type"],
        "status": event["status"],
    }
