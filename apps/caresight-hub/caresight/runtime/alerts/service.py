from __future__ import annotations

from typing import Any


def draft_caregiver_alert(audit: dict[str, Any]) -> dict[str, Any]:
    event = audit["event"]
    evidence = event["evidence"]
    event_type = event["event_type"]
    room = evidence.get("room_name") or event.get("camera_name") or event["camera_id"]
    status = event["status"].replace("_", " ")
    snapshot = evidence.get("snapshot_path", "not recorded")
    source_fields = [
        "event.event_id",
        "event.event_type",
        "event.status",
        "event.occurred_at",
        "event.camera_id",
        "event.evidence",
        "event_observations",
        "event_reviews",
        "journal_entries",
        "agent_handoffs",
    ]
    body = (
        f"CareSight possible event: {event_type} in {room}. "
        f"Status is {status}. Snapshot path: {snapshot}. "
        "Please review the local CareSight record before taking action."
    )
    return {
        "event_id": event["event_id"],
        "purpose": "caregiver_alert_draft",
        "channel_sequence": ["text", "facetime"],
        "body": body,
        "provenance": {
            "source": "sqlite_audit_chain",
            "source_fields": source_fields,
        },
        "boundaries": [
            "draft_only",
            "human_review_required",
            "no_autonomous_dispatch",
            "no_medical_diagnosis",
        ],
    }
