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
            "escalation_stage": event["evidence"].get("escalation_stage"),
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
    latest_decision = review.get("latest_decision") or "not reviewed yet"
    latest_reviewer = review.get("latest_reviewer") or "none"
    snapshot_path = evidence.get("snapshot_path") or "not recorded"
    track_ids = ", ".join(evidence.get("track_ids") or ["none"])
    return "\n".join(
        [
            f"# Human Review Packet",
            "",
            f"CareSight recorded a possible event in {evidence.get('room') or 'the configured room'}.",
            "A human should use the local record and care plan before deciding what to do next.",
            "",
            "## At a Glance",
            "",
            f"- Event: {packet['summary']['headline']}",
            f"- Current status: {packet['status']}",
            f"- Latest human review: {latest_decision} by {latest_reviewer}",
            f"- Evidence: {evidence['observation_count']} observation, track {track_ids}",
            f"- Escalation stage: {evidence.get('escalation_stage') or 'not recorded'}",
            f"- Snapshot: {snapshot_path}",
            "",
            "## Suggested Next Step",
            "",
            _next_step(packet),
            "",
            "## Boundaries",
            "",
            "- CareSight did not dispatch emergency services.",
            "- CareSight did not make a medical diagnosis.",
            "- SQLite is source of truth; this message is a readable summary of the local audit record.",
            "",
            "## Audit Details",
            "",
            f"- Event ID: {packet['event_id']}",
            f"- Source fields: {', '.join(packet['provenance']['source_fields'])}",
            f"- Available human actions: {', '.join(packet['available_human_actions'])}",
            f"- Blocked actions: {', '.join(packet['blocked_actions'])}",
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


def _next_step(packet: dict[str, Any]) -> str:
    if packet["status"] == "human_confirmed":
        return "This event has already been human-confirmed. Review the snapshot and journal if more context is needed."
    if packet["status"] == "dismissed":
        return "This event has been dismissed by a human reviewer. Keep it in the local audit trail."
    return "Review the snapshot and local evidence, then choose confirm, dismiss, or needs follow-up."


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
