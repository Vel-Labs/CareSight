from __future__ import annotations

from typing import Any


def build_multi_camera_narrative(store, event_id: str) -> dict[str, Any]:
    event = store.get_event(event_id)
    observations = store.list_event_observations(event_id)
    evidence = event.get("evidence", {})
    return {
        "schema": "multi-camera-narrative",
        "narrative_id": f"narrative_{event_id}",
        "event_id": event_id,
        "source_of_truth": "sqlite",
        "claim_boundary": "likely_continuity_not_identity",
        "event": {
            "event_type": event["event_type"],
            "status": event["status"],
            "occurred_at": event["occurred_at"],
            "camera_id": event["camera_id"],
            "room": evidence.get("room_name") or event.get("camera_name") or event["camera_id"],
            "track_ids": sorted({row["track_id"] for row in observations if row.get("track_id")}),
        },
        "camera_context": {
            "active_event_camera_id": event["camera_id"],
            "active_event_room": evidence.get("room_name") or event["camera_id"],
            "observation_count": len(observations),
        },
        "not_claimed": [
            "named_identity",
            "biometric_match",
            "fall_confirmed",
            "medical_emergency",
        ],
    }


def render_multi_camera_narrative_markdown(narrative: dict[str, Any]) -> str:
    event = narrative["event"]
    track_ids = ", ".join(event.get("track_ids") or ["none"])
    return "\n".join(
        [
            "# Multi-Camera Narrative",
            "",
            (
                f"CareSight has SQLite-derived context for {event['event_type']} in "
                f"{event['room']} from camera {event['camera_id']}."
            ),
            "",
            "This is likely continuity, not identity. It does not use face recognition, biometric matching, or named-person identification.",
            "",
            "## Event Context",
            "",
            f"- Event ID: {narrative['event_id']}",
            f"- Status: {event['status']}",
            f"- Occurred at: {event['occurred_at']}",
            f"- Track IDs: {track_ids}",
            "",
            "## Boundaries",
            "",
            f"- Claim boundary: {narrative['claim_boundary']}",
            f"- Not claimed: {', '.join(narrative['not_claimed'])}",
        ]
    )
