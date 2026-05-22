from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def build_escalation_receipt(
    store: Any,
    event_id: str,
    *,
    overlay_state_path: str | Path | None = None,
    live_preview_path: str | Path | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    event = store.get_event_context(event_id)
    drafts = store.list_agent_drafts(event_id)
    requests = store.list_agent_action_requests(event_id)
    attempts = store.list_agent_execution_attempts_for_event(event_id)
    snapshot_path = event.get("evidence", {}).get("snapshot_path")
    overlay_path = Path(overlay_state_path).expanduser() if overlay_state_path else None
    preview_path = Path(live_preview_path).expanduser() if live_preview_path else None

    return {
        "schema": "care-escalation-receipt",
        "receipt_id": f"escalation_receipt_{event_id}",
        "event_id": event_id,
        "created_at": created_at or _utc_now(),
        "source_of_truth": "sqlite",
        "event": {
            "event_type": event["event_type"],
            "status": event["status"],
            "occurred_at": event["occurred_at"],
            "camera_id": event["camera_id"],
            "zone_id": event.get("zone_id"),
            "room": event.get("evidence", {}).get("room_name") or event.get("camera_name"),
            "severity": event["severity"],
            "confidence": event["confidence"],
            "snapshot_path": snapshot_path,
            "snapshot_exists": Path(snapshot_path).exists() if snapshot_path else False,
        },
        "escalation_counts": {
            "agent_drafts": len(drafts),
            "action_requests": len(requests),
            "execution_attempts": len(attempts),
            "live_attempts": len([attempt for attempt in attempts if attempt["attempt_kind"] == "live"]),
        },
        "action_requests": [_request_summary(request) for request in requests],
        "execution_attempts": [_attempt_summary(attempt) for attempt in attempts],
        "overlay_evidence": {
            "current_event_state_path": str(overlay_path) if overlay_path else None,
            "current_event_state_exists": overlay_path.exists() if overlay_path else False,
            "live_preview_path": str(preview_path) if preview_path else None,
            "live_preview_exists": preview_path.exists() if preview_path else False,
        },
        "safety_boundaries": [
            "human_review_required",
            "allowlisted_recipient_only",
            "raw_video_stays_local",
            "no_autonomous_dispatch",
            "no_medical_diagnosis",
            "read_only_receipt",
        ],
    }


def render_escalation_receipt_markdown(receipt: dict[str, Any]) -> str:
    event = receipt["event"]
    counts = receipt["escalation_counts"]
    lines = [
        "# Escalation Receipt",
        "",
        f"CareSight linked escalation evidence for `{receipt['event_id']}`.",
        "",
        "## Event",
        "",
        f"- Type: {event['event_type']}",
        f"- Status: {event['status']}",
        f"- Observed: {event['occurred_at']}",
        f"- Room: {event.get('room') or 'unknown'}",
        f"- Snapshot: {event.get('snapshot_path') or 'not recorded'}",
        f"- Snapshot exists: {_yes_no(event['snapshot_exists'])}",
        "",
        "## Escalation Evidence",
        "",
        f"- Drafts: {counts['agent_drafts']}",
        f"- Action requests: {counts['action_requests']}",
        f"- Execution attempts: {counts['execution_attempts']}",
        f"- Live attempts: {counts['live_attempts']}",
    ]
    for attempt in receipt["execution_attempts"]:
        lines.append(
            f"- {attempt['created_at']}: {attempt['result']} via {attempt['harness']} "
            f"(external action: {_yes_no(attempt['external_action_performed'])})"
        )
    overlay = receipt["overlay_evidence"]
    lines.extend(
        [
            "",
            "## OBS Evidence",
            "",
            f"- Overlay state: {overlay.get('current_event_state_path') or 'not configured'}",
            f"- Overlay state exists: {_yes_no(overlay['current_event_state_exists'])}",
            f"- Live preview: {overlay.get('live_preview_path') or 'not configured'}",
            f"- Live preview exists: {_yes_no(overlay['live_preview_exists'])}",
            "",
            "## Boundaries",
            "",
            "- This receipt is read-only and local.",
            "- It does not confirm a medical diagnosis or dispatch help.",
            "- Live actions remain tied to human approval and allowlisted contacts.",
        ]
    )
    return "\n".join(lines)


def _request_summary(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "request_id": request["request_id"],
        "created_at": request["created_at"],
        "requested_action": request["requested_action"],
        "destination": request.get("destination"),
        "escalation_level": request.get("escalation_level"),
        "recipient_role": request.get("recipient_role"),
        "allowed_contact_ids": request.get("allowed_contact_ids", []),
        "requires_human_approval": request.get("requires_human_approval", True),
    }


def _attempt_summary(attempt: dict[str, Any]) -> dict[str, Any]:
    delivery = attempt.get("payload", {}).get("delivery", {})
    return {
        "attempt_id": attempt["attempt_id"],
        "request_id": attempt["request_id"],
        "created_at": attempt["created_at"],
        "harness": attempt["harness"],
        "attempt_kind": attempt["attempt_kind"],
        "execution_state": attempt["execution_state"],
        "result": attempt["result"],
        "external_action_performed": attempt["external_action_performed"],
        "delivery_status": delivery.get("status"),
        "delivery_platform": delivery.get("platform"),
        "attachment": delivery.get("attachment"),
    }


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
