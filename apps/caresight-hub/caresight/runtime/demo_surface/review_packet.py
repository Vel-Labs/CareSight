from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


SOURCE_FIELDS = [
    "events",
    "event_observations",
    "event_reviews",
    "journal_entries",
    "agent_handoffs",
]


def build_human_review_packet(
    audit_chain: dict[str, Any],
    *,
    created_at: str | None = None,
) -> dict[str, Any]:
    event = audit_chain["event"]
    observations = audit_chain["observations"]
    reviews = audit_chain["reviews"]
    latest_review = reviews[-1] if reviews else None

    return {
        "schema": "human-review-packet",
        "packet_id": f"review_packet_{event['event_id']}",
        "event_id": event["event_id"],
        "event_type": event["event_type"],
        "status": event["status"],
        "created_at": created_at or _utc_now(),
        "source_of_truth": "sqlite",
        "summary": {
            "headline": _headline(event),
            "bounded_language": True,
            "requires_human_confirmation": bool(event["requires_human_confirmation"]),
        },
        "evidence": {
            "camera_id": event["camera_id"],
            "room": _room_label(event),
            "zone_id": event.get("zone_id"),
            "track_ids": _track_ids(observations),
            "snapshot_path": event["evidence"].get("snapshot_path"),
            "observation_count": len(observations),
        },
        "review_state": {
            "review_count": len(reviews),
            "latest_reviewer": latest_review["reviewer"] if latest_review else None,
            "latest_decision": latest_review["decision"] if latest_review else None,
        },
        "available_human_actions": ["confirm", "dismiss", "needs_followup"],
        "blocked_actions": event["blocked_actions"],
        "provenance": {
            "source": "sqlite_audit_chain",
            "source_fields": SOURCE_FIELDS,
        },
    }


def render_review_packet_markdown(packet: dict[str, Any]) -> str:
    review = packet["review_state"]
    evidence = packet["evidence"]
    return "\n".join(
        [
            f"# Human Review Packet: {packet['event_id']}",
            "",
            f"- Source of truth: {packet['source_of_truth'].upper()}",
            f"- Event type: {packet['event_type']}",
            f"- Status: {packet['status']}",
            f"- Headline: {packet['summary']['headline']}",
            f"- Camera: {evidence['camera_id']}",
            f"- Room: {evidence.get('room') or 'unknown'}",
            f"- Zone: {evidence.get('zone_id') or 'unknown'}",
            f"- Track IDs: {', '.join(evidence.get('track_ids') or ['none'])}",
            f"- Snapshot path: {evidence.get('snapshot_path') or 'not recorded'}",
            f"- Observation count: {evidence['observation_count']}",
            f"- Review count: {review['review_count']}",
            f"- Latest reviewer: {review.get('latest_reviewer') or 'none'}",
            f"- Latest decision: {review.get('latest_decision') or 'none'}",
            f"- Available human actions: {', '.join(packet['available_human_actions'])}",
            f"- Blocked actions: {', '.join(packet['blocked_actions'])}",
            "",
            "SQLite is source of truth. No autonomous emergency dispatch.",
        ]
    )


def _headline(event: dict[str, Any]) -> str:
    room = _room_label(event) or event["camera_id"]
    event_text = event["event_type"].replace("_", " ")
    return f"{event_text.title()} in {room}"


def _room_label(event: dict[str, Any]) -> str | None:
    return event["evidence"].get("room_name") or event.get("camera_name")


def _track_ids(observations: list[dict[str, Any]]) -> list[str]:
    return sorted({observation["track_id"] for observation in observations if observation.get("track_id")})


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
