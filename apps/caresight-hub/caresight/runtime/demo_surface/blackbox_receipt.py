from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def build_blackbox_receipt(
    audit_chain: dict[str, Any],
    *,
    dashboard_state: dict[str, Any] | None = None,
    alert_draft: dict[str, Any] | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    event = audit_chain["event"]
    observations = audit_chain["observations"]
    reviews = audit_chain["reviews"]
    journals = audit_chain["journal_entries"]
    handoffs = audit_chain["agent_handoffs"]
    blockers = _blockers(
        observations=observations,
        reviews=reviews,
        journals=journals,
        handoffs=handoffs,
        dashboard_state=dashboard_state,
        alert_draft=alert_draft,
        event_id=event["event_id"],
    )
    latest_review = reviews[-1] if reviews else None
    receipt: dict[str, Any] = {
        "schema": "blackbox-receipt",
        "receipt_id": f"receipt_{event['event_id']}",
        "event_id": event["event_id"],
        "created_at": created_at or _utc_now(),
        "source_of_truth": "sqlite",
        "completion_status": "not_complete" if blockers else "complete",
        "event": {
            "event_type": event["event_type"],
            "status": event["status"],
            "occurred_at": event["occurred_at"],
            "camera_id": event["camera_id"],
            "zone_id": event.get("zone_id"),
            "severity": event["severity"],
            "confidence": event["confidence"],
        },
        "counts": {
            "observations": len(observations),
            "reviews": len(reviews),
            "journal_entries": len(journals),
            "agent_handoffs": len(handoffs),
        },
        "track_ids": _track_ids(observations),
        "human_review": _human_review(latest_review),
        "derived_outputs": {
            "dashboard_includes_event": _dashboard_includes_event(dashboard_state, event["event_id"]),
            "alert_draft_has_provenance": bool(alert_draft and alert_draft.get("event_id") == event["event_id"]),
        },
        "blocked_actions": event["blocked_actions"],
        "safety_boundaries": [
            "raw_video_local",
            "human_review_required",
            "sqlite_canonical",
            "dashboard_derived",
            "read_only_receipt",
            "no_autonomous_dispatch",
            "no_medical_diagnosis",
        ],
    }
    if blockers:
        receipt["blockers"] = blockers
    return receipt


def render_blackbox_receipt_markdown(receipt: dict[str, Any]) -> str:
    event = receipt["event"]
    counts = receipt["counts"]
    lines = [
        f"# Blackbox Receipt: {receipt['event_id']}",
        "",
        f"- Source of truth: {receipt['source_of_truth'].upper()}",
        f"- Completion status: {receipt['completion_status']}",
        f"- Event type: {event['event_type']}",
        f"- Event status: {event['status']}",
        f"- Occurred at: {event['occurred_at']}",
        f"- Camera: {event['camera_id']}",
        f"- Zone: {event.get('zone_id') or 'unknown'}",
        f"- Severity: {event['severity']}",
        f"- Confidence: {event['confidence']}",
        f"- Track IDs: {', '.join(receipt.get('track_ids') or ['none'])}",
        f"- Observations: {counts['observations']}",
        f"- Reviews: {counts['reviews']}",
        f"- Journal entries: {counts['journal_entries']}",
        f"- Agent handoffs: {counts['agent_handoffs']}",
        f"- Blocked actions: {', '.join(receipt['blocked_actions'])}",
    ]
    if receipt.get("blockers"):
        lines.append(f"- Blockers: {', '.join(receipt['blockers'])}")
    lines.extend(["", "SQLite is source of truth. No autonomous emergency dispatch."])
    return "\n".join(lines)


def _blockers(
    *,
    observations: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
    journals: list[dict[str, Any]],
    handoffs: list[dict[str, Any]],
    dashboard_state: dict[str, Any] | None,
    alert_draft: dict[str, Any] | None,
    event_id: str,
) -> list[str]:
    blockers: list[str] = []
    if not observations:
        blockers.append("missing_event_observation")
    if not _track_ids(observations):
        blockers.append("missing_observation_track_id")
    if not reviews:
        blockers.append("missing_human_review")
    if not journals:
        blockers.append("missing_journal_entry")
    if not handoffs:
        blockers.append("missing_report_only_handoff")
    if dashboard_state is not None and not _dashboard_includes_event(dashboard_state, event_id):
        blockers.append("missing_dashboard_timeline_entry")
    if alert_draft is not None and alert_draft.get("event_id") != event_id:
        blockers.append("missing_alert_provenance")
    return blockers


def _track_ids(observations: list[dict[str, Any]]) -> list[str]:
    return sorted({observation["track_id"] for observation in observations if observation.get("track_id")})


def _human_review(review: dict[str, Any] | None) -> dict[str, Any] | None:
    if review is None:
        return None
    return {
        "reviewer": review["reviewer"],
        "decision": review["decision"],
        "reviewed_at": review["reviewed_at"],
    }


def _dashboard_includes_event(dashboard_state: dict[str, Any] | None, event_id: str) -> bool:
    if dashboard_state is None:
        return False
    return any(entry.get("event_id") == event_id for entry in dashboard_state.get("timeline", []))


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
