from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EscalationEvent:
    event_id: str
    event_type: str
    severity: str
    status: str

    @classmethod
    def from_event(cls, event: dict) -> "EscalationEvent":
        return cls(
            event_id=str(event["event_id"]),
            event_type=str(event["event_type"]),
            severity=str(event.get("severity", "medium")),
            status=str(event.get("status", "awaiting_human_confirmation")),
        )
