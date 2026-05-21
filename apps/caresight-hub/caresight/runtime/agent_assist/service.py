from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Protocol

from caresight.storage.sqlite_store import utc_now


FORBIDDEN_CLAIMS: dict[str, tuple[str, ...]] = {
    "medical_device": ("medical device", "certified fall detector"),
    "hipaa_compliance": ("hipaa compliant", "hipaa-ready"),
    "autonomous_emergency_dispatch": (
        "called 911",
        "dispatch emergency",
        "dispatched emergency",
        "emergency services were dispatched",
    ),
    "medication_administration": ("medication was taken", "confirmed medication"),
    "vision_overcertainty": ("fall detected", "diagnosed"),
}


class AgentDraftStore(Protocol):
    def get_event_context(self, event_id: str) -> dict[str, Any]: ...

    def list_event_observations(self, event_id: str) -> list[dict[str, Any]]: ...

    def list_event_reviews(self, event_id: str) -> list[dict[str, Any]]: ...

    def list_journal_entries(self, event_id: str) -> list[dict[str, Any]]: ...

    def list_agent_handoffs(self, event_id: str) -> list[dict[str, Any]]: ...

    def insert_agent_draft(self, draft: dict[str, Any]) -> None: ...

    def list_agent_drafts(self, event_id: str) -> list[dict[str, Any]]: ...

    def get_agent_draft(self, draft_id: str) -> dict[str, Any]: ...

    def insert_agent_action_request(self, request: dict[str, Any]) -> None: ...


@dataclass(frozen=True)
class FakeAgentProvider:
    provider_name: str = "fake"

    def draft_text(self, audit: dict[str, Any], purpose: str) -> str:
        event = audit["event"]
        evidence = event["evidence"]
        room = evidence.get("room_name") or event.get("camera_name") or event["camera_id"]
        status = event["status"].replace("_", " ")
        snapshot_path = evidence.get("snapshot_path", "not recorded")
        if purpose == "alert_draft":
            return (
                f"CareSight recorded a possible event ({event['event_type']}) in {room}. "
                f"Status is {status}. Snapshot path: {snapshot_path}. "
                "Please review the local CareSight record before taking action."
            )
        return (
            f"CareSight recorded a possible event ({event['event_type']}) in {room}. "
            f"The local record includes SQLite event provenance, review state, journal context, "
            f"handoff context, and snapshot path: {snapshot_path}."
        )


def build_agent_draft(
    store: AgentDraftStore,
    event_id: str,
    *,
    purpose: str = "caregiver_summary",
    provider: FakeAgentProvider | None = None,
    override_text: str | None = None,
) -> dict[str, Any]:
    audit = {
        "event": store.get_event_context(event_id),
        "observations": store.list_event_observations(event_id),
        "reviews": store.list_event_reviews(event_id),
        "journal_entries": store.list_journal_entries(event_id),
        "agent_handoffs": store.list_agent_handoffs(event_id),
    }
    fake_provider = provider or FakeAgentProvider()
    draft_text = override_text if override_text is not None else fake_provider.draft_text(audit, purpose)
    blocked_claims = validate_draft_text(draft_text)
    validation_status = "blocked" if blocked_claims else "validated"
    draft = {
        "schema": "agent-draft",
        "draft_id": _draft_id(event_id, purpose),
        "event_id": event_id,
        "created_at": utc_now(),
        "provider": fake_provider.provider_name,
        "source_of_truth": "sqlite",
        "purpose": purpose,
        "validation_status": validation_status,
        "draft_text": draft_text,
        "safe_rewrite": _safe_rewrite(audit) if blocked_claims else None,
        "safety_boundaries": [
            "draft_only",
            "human_review_required",
            "sqlite_canonical",
            "no_autonomous_dispatch",
            "no_medical_diagnosis",
            "no_medication_confirmation",
            "no_hipaa_claim",
        ],
        "provenance": {
            "source": "sqlite_audit_chain",
            "source_fields": [
                "events",
                "event_observations",
                "event_reviews",
                "journal_entries",
                "agent_handoffs",
            ],
        },
        "blocked_claims": blocked_claims,
    }
    store.insert_agent_draft(draft)
    return draft


def validate_draft_text(text: str) -> list[str]:
    normalized = text.casefold()
    blocked: list[str] = []
    for claim, phrases in FORBIDDEN_CLAIMS.items():
        if any(re.search(rf"\b{re.escape(phrase.casefold())}\b", normalized) for phrase in phrases):
            blocked.append(claim)
    return blocked


def stage_action_request(
    store: AgentDraftStore,
    *,
    event_id: str,
    source_draft_id: str,
    requested_action: str,
    destination: str | None = None,
) -> dict[str, Any]:
    draft = store.get_agent_draft(source_draft_id)
    if draft["event_id"] != event_id:
        raise ValueError("source draft does not belong to event")
    if draft["validation_status"] != "validated":
        raise ValueError("cannot stage an action request from a blocked draft")
    if requested_action not in {
        "send_caregiver_message",
        "create_apple_note",
        "prepare_handoff_packet",
        "play_tts_utterance",
    }:
        raise ValueError(f"unsupported staged action: {requested_action}")

    request = {
        "schema": "agent-action-request",
        "request_id": _action_request_id(event_id, requested_action, source_draft_id),
        "event_id": event_id,
        "created_at": utc_now(),
        "requested_action": requested_action,
        "stage": "staged",
        "execution_state": "not_executed",
        "requires_human_approval": True,
        "source_draft_id": source_draft_id,
        "destination": destination,
        "safety_boundaries": [
            "stage_only",
            "human_review_required",
            "no_external_execution",
            "no_autonomous_dispatch",
            "sqlite_canonical",
        ],
        "provenance": {
            "source": "sqlite_audit_chain",
            "source_fields": ["events", "agent_drafts", "agent_action_requests"],
        },
    }
    store.insert_agent_action_request(request)
    return request


def _safe_rewrite(audit: dict[str, Any]) -> str:
    event = audit["event"]
    return (
        f"CareSight recorded a possible event ({event['event_type']}). "
        "Please review the local CareSight record and follow the household care plan."
    )


def _draft_id(event_id: str, purpose: str) -> str:
    safe_purpose = re.sub(r"[^a-z0-9_]+", "_", purpose.casefold()).strip("_")
    return f"draft_{event_id}_{safe_purpose}"


def _action_request_id(event_id: str, requested_action: str, draft_id: str) -> str:
    safe_action = re.sub(r"[^a-z0-9_]+", "_", requested_action.casefold()).strip("_")
    draft_suffix = draft_id.removeprefix("draft_")
    return f"action_req_{event_id}_{safe_action}_{draft_suffix}"[:180]
