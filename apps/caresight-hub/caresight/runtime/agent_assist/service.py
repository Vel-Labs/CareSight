from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any, Protocol
import urllib.request

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

    def list_appearance_profiles_for_event(self, event_id: str) -> list[dict[str, Any]]: ...

    def insert_agent_draft(self, draft: dict[str, Any]) -> None: ...

    def list_agent_drafts(self, event_id: str) -> list[dict[str, Any]]: ...

    def get_agent_draft(self, draft_id: str) -> dict[str, Any]: ...

    def insert_agent_action_request(self, request: dict[str, Any]) -> None: ...

    def get_agent_action_request(self, request_id: str) -> dict[str, Any]: ...


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


@dataclass(frozen=True)
class GemmaLocalProvider:
    endpoint: str = "http://127.0.0.1:8080/v1"
    model: str = "apps/caresight-hub/models/reasoning/gemma/gemma-4-e2b-it-4bit"
    provider_name: str = "gemma_mlx"
    timeout_seconds: float = 30.0

    def draft_text(self, audit: dict[str, Any], purpose: str) -> str:
        request = urllib.request.Request(
            f"{self.endpoint.rstrip('/')}/chat/completions",
            data=json.dumps(
                {
                    "model": self.model,
                    "messages": _gemma_messages(audit, purpose),
                    "max_tokens": 120,
                    "temperature": 0,
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        try:
            text = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("Gemma response did not include assistant message content") from exc
        return _normalize_provider_text(text)


def build_agent_draft(
    store: AgentDraftStore,
    event_id: str,
    *,
    purpose: str = "caregiver_summary",
    provider: FakeAgentProvider | GemmaLocalProvider | None = None,
    override_text: str | None = None,
) -> dict[str, Any]:
    audit = {
        "event": store.get_event_context(event_id),
        "observations": store.list_event_observations(event_id),
        "reviews": store.list_event_reviews(event_id),
        "journal_entries": store.list_journal_entries(event_id),
        "agent_handoffs": store.list_agent_handoffs(event_id),
        "appearance_profiles": store.list_appearance_profiles_for_event(event_id),
    }
    fake_provider = provider or FakeAgentProvider()
    draft_text = override_text if override_text is not None else fake_provider.draft_text(audit, purpose)
    blocked_claims = validate_draft_text(draft_text)
    validation_status = "blocked" if blocked_claims else "validated"
    draft = {
        "schema": "agent-draft",
        "draft_id": _draft_id(event_id, purpose, fake_provider.provider_name),
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
                "appearance_profiles",
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
    escalation_level: str = "attention",
    recipient_role: str | None = None,
    allowed_contact_ids: list[str] | None = None,
    response_options: list[str] | None = None,
    contact_allowlist: set[str] | None = None,
) -> dict[str, Any]:
    draft = store.get_agent_draft(source_draft_id)
    if draft["event_id"] != event_id:
        raise ValueError("source draft does not belong to event")
    if draft["validation_status"] != "validated":
        raise ValueError("cannot stage an action request from a blocked draft")
    if requested_action not in {
        "send_caregiver_message",
        "send_imessage_draft",
        "create_apple_note",
        "prepare_handoff_packet",
        "prepare_facetime_handoff",
        "play_tts_utterance",
    }:
        raise ValueError(f"unsupported staged action: {requested_action}")
    if escalation_level not in {"routine", "attention", "urgent_handoff"}:
        raise ValueError(f"unsupported escalation level: {escalation_level}")
    allowed_contacts = allowed_contact_ids or []
    if destination in {"imessage", "facetime"} and not allowed_contacts:
        raise ValueError("imessage/facetime staging requires at least one allowlisted contact id")
    if destination in {"imessage", "facetime"} and contact_allowlist is not None:
        unknown_contacts = [contact_id for contact_id in allowed_contacts if contact_id not in contact_allowlist]
        if unknown_contacts:
            raise ValueError(f"contact id not allowlisted: {', '.join(unknown_contacts)}")
    if recipient_role not in {None, "caregiver", "emergency_contact"}:
        raise ValueError(f"unsupported recipient role: {recipient_role}")
    resolved_response_options = response_options or _default_response_options(requested_action)
    allowed_options = {
        "acknowledge_text_update",
        "request_local_screen_capture",
        "request_facetime_handoff",
        "dismiss_after_review",
    }
    unsupported_options = [option for option in resolved_response_options if option not in allowed_options]
    if unsupported_options:
        raise ValueError(f"unsupported response options: {', '.join(unsupported_options)}")
    safety_boundaries = [
        "stage_only",
        "human_review_required",
        "no_external_execution",
        "no_autonomous_dispatch",
        "sqlite_canonical",
    ]
    if destination in {"imessage", "facetime"}:
        safety_boundaries.append("allowlisted_recipient_only")
    if requested_action in {"send_imessage_draft", "prepare_facetime_handoff"}:
        safety_boundaries.append("no_raw_video_to_agent")

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
        "escalation_level": escalation_level,
        "recipient_role": recipient_role,
        "allowed_contact_ids": allowed_contacts,
        "response_options": resolved_response_options,
        "safety_boundaries": safety_boundaries,
        "provenance": {
            "source": "sqlite_audit_chain",
            "source_fields": ["events", "agent_drafts", "agent_action_requests"],
        },
    }
    store.insert_agent_action_request(request)
    return request


def _default_response_options(requested_action: str) -> list[str]:
    if requested_action in {"send_imessage_draft", "prepare_facetime_handoff"}:
        return ["acknowledge_text_update", "request_local_screen_capture", "request_facetime_handoff"]
    return ["acknowledge_text_update"]


def _safe_rewrite(audit: dict[str, Any]) -> str:
    event = audit["event"]
    return (
        f"CareSight recorded a possible event ({event['event_type']}). "
        "Please review the local CareSight record and follow the household care plan."
    )


def _draft_id(event_id: str, purpose: str, provider_name: str = "fake") -> str:
    safe_purpose = re.sub(r"[^a-z0-9_]+", "_", purpose.casefold()).strip("_")
    if provider_name == "fake":
        return f"draft_{event_id}_{safe_purpose}"
    safe_provider = re.sub(r"[^a-z0-9_]+", "_", provider_name.casefold()).strip("_")
    return f"draft_{event_id}_{safe_purpose}_{safe_provider}"


def _action_request_id(event_id: str, requested_action: str, draft_id: str) -> str:
    safe_action = re.sub(r"[^a-z0-9_]+", "_", requested_action.casefold()).strip("_")
    draft_suffix = draft_id.removeprefix("draft_")
    return f"action_req_{event_id}_{safe_action}_{draft_suffix}"[:180]


def _gemma_messages(audit: dict[str, Any], purpose: str) -> list[dict[str, str]]:
    event = audit["event"]
    evidence = event["evidence"]
    context = {
        "event_id": event["event_id"],
        "event_type": event["event_type"],
        "status": event["status"],
        "severity": event["severity"],
        "confidence": event["confidence"],
        "camera_id": event["camera_id"],
        "zone_id": event["zone_id"],
        "room_name": evidence.get("room_name"),
        "dwell_seconds": evidence.get("dwell_seconds"),
        "snapshot_path_present": bool(evidence.get("snapshot_path")),
        "reviews_count": len(audit["reviews"]),
        "journal_entries_count": len(audit["journal_entries"]),
        "purpose": purpose,
    }
    return [
        {
            "role": "system",
            "content": (
                "You draft short CareSight caregiver text from structured SQLite audit context only. "
                "Do not claim a fall, injury, diagnosis, medical emergency, medication administration, "
                "HIPAA compliance, or emergency dispatch. Use 'possible' or 'needs review' language. "
                "Return only the caregiver-facing message text."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(context, sort_keys=True),
        },
    ]


def _normalize_provider_text(text: str) -> str:
    normalized = text.strip()
    for prefix in ("Caregiver Alert:", "**Caregiver Alert:**", "Alert:"):
        if normalized.startswith(prefix):
            normalized = normalized.removeprefix(prefix).strip()
    return normalized.strip()
