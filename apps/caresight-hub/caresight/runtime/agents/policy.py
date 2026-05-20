from __future__ import annotations

from typing import Any


class AgentPolicyError(ValueError):
    pass


ALLOWED_ACTIONS = {
    "summarize_event",
    "draft_caregiver_message",
    "draft_journal_note",
    "audit_handoff_payload",
}

FORBIDDEN_ACTIONS = {
    "confirm_event",
    "dismiss_event",
    "delete_event",
    "emergency_dispatch",
    "diagnose",
    "confirm_medication_taken",
    "inspect_raw_video_for_decision",
}


def assert_agent_action_allowed(action: str, payload: dict[str, Any]) -> None:
    if action in FORBIDDEN_ACTIONS:
        raise AgentPolicyError(f"agent action is forbidden: {action}")
    if action not in ALLOWED_ACTIONS:
        raise AgentPolicyError(f"agent action is not registered: {action}")
    provenance = payload.get("provenance")
    if not isinstance(provenance, dict):
        raise AgentPolicyError("agent output requires provenance")
    event_id = provenance.get("event_id")
    source_fields = provenance.get("source_fields")
    purpose = payload.get("purpose")
    if not isinstance(event_id, str) or not event_id.startswith("evt_"):
        raise AgentPolicyError("agent provenance requires event_id")
    if not isinstance(source_fields, list) or not source_fields:
        raise AgentPolicyError("agent provenance requires source_fields")
    if not isinstance(purpose, str) or not purpose:
        raise AgentPolicyError("agent output requires purpose")
