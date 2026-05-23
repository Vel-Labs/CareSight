from __future__ import annotations

from typing import Any, Protocol

from caresight.runtime.alerts import draft_caregiver_alert
from caresight.runtime.appearance.render import render_appearance_summary


class DashboardReviewService(Protocol):
    def list_events(self, *, include_all: bool = False) -> list[dict[str, Any]]: ...

    def get_event_summary(self, event_id: str) -> dict[str, Any]: ...

    def list_journal_entries(self, event_id: str) -> list[dict[str, Any]]: ...

    def get_audit_chain(self, event_id: str) -> dict[str, Any]: ...

    def list_appearance_profiles_for_event(self, event_id: str) -> list[dict[str, Any]]: ...


def build_dashboard_state(service: DashboardReviewService, *, event_id: str | None = None) -> dict[str, Any]:
    all_events = service.list_events(include_all=True)
    awaiting_events = [event for event in all_events if event["status"] == "awaiting_human_confirmation"]
    requested_event = next((event for event in all_events if event["event_id"] == event_id), None)
    current_event = requested_event or (awaiting_events[0] if awaiting_events else (all_events[0] if all_events else None))
    current_event_id = current_event["event_id"] if current_event else None
    backlog_events = [
        event for event in awaiting_events if current_event_id is None or event["event_id"] != current_event_id
    ]
    journal_preview = []
    alert_draft = None

    if current_event_id is not None:
        journal_preview = service.list_journal_entries(current_event_id)
        alert_draft = draft_caregiver_alert(service.get_audit_chain(current_event_id))
        appearance_context = _appearance_context(service.list_appearance_profiles_for_event(current_event_id))
    else:
        appearance_context = None

    return {
        "source_of_truth": "sqlite",
        "view": {
            "mode": "focused_event" if event_id else "inbox",
            "requested_event_id": event_id,
            "focused_event_found": event_id is None or requested_event is not None,
        },
        "focused_event": _focused_event(current_event),
        "appearance_context": appearance_context,
        "awaiting_review_backlog": {
            "count": len(backlog_events),
            "events": [
                {
                    "event_id": event["event_id"],
                    "event_type": event["event_type"],
                    "status": event["status"],
                    "severity": event["severity"],
                    "age_label": "awaiting_review_backlog",
                }
                for event in backlog_events
            ],
        },
        "live_feed": {"status": "operator_view_required", "raw_video_stays_local": True},
        "current_state": {
            "awaiting_review": len(awaiting_events),
            "total_events": len(all_events),
            "current_event_id": current_event_id,
        },
        "timeline": [
            {
                "event_id": event["event_id"],
                "event_type": event["event_type"],
                "status": event["status"],
                "occurred_at": event["occurred_at"],
                "severity": event["severity"],
            }
            for event in all_events
        ],
        "concerns": [
            {
                "event_id": event["event_id"],
                "event_type": event["event_type"],
                "severity": event["severity"],
                "status": event["status"],
            }
            for event in awaiting_events
        ],
        "review_controls": {
            "confirm": "ReviewService.confirm_event",
            "dismiss": "ReviewService.dismiss_event",
            "delete": "forbidden",
            "dispatch": "forbidden",
        },
        "journal_preview": journal_preview,
        "caregiver_alert_draft": alert_draft,
    }


def _focused_event(event: dict[str, Any] | None) -> dict[str, Any] | None:
    if event is None:
        return None
    return {
        "event_id": event["event_id"],
        "event_type": event["event_type"],
        "status": event["status"],
        "occurred_at": event["occurred_at"],
        "camera_id": event["camera_id"],
        "zone_id": event.get("zone_id"),
        "severity": event["severity"],
        "confidence": event["confidence"],
    }


def _appearance_context(profiles: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not profiles:
        return None
    profile = profiles[0]
    return {
        "identity_boundary": "non_biometric_daily_appearance_only",
        "profile_id": profile["appearance_profile_id"],
        "role_assignment": profile["role_assignment"],
        "assignment_source": profile["assignment_source"],
        "descriptor_source": profile["descriptor_source"],
        "descriptor_status": profile["descriptor_status"],
        "summary": render_appearance_summary(_profile_for_render(profile)),
        "forbidden_claims": [
            "named_person_identification",
            "face_recognition",
            "biometric_identity",
            "cross_day_identity",
        ],
    }


def _profile_for_render(profile: dict[str, Any]):
    from caresight.runtime.appearance import AppearanceProfile

    attributes = profile.get("attributes", {})
    return AppearanceProfile(
        appearance_profile_id=profile["appearance_profile_id"],
        active_date=profile["active_date"],
        expires_at=profile["expires_at"],
        role_assignment=profile["role_assignment"],
        assignment_source=profile["assignment_source"],
        track_id=None,
        upper_body_color=attributes.get("upper_body_color", {}).get("value", "unknown"),
        lower_body_color=attributes.get("lower_body_color", {}).get("value", "unknown"),
        last_seen_camera_id=profile.get("last_seen_camera_id") or "",
        last_seen_room=profile.get("last_seen_room") or "",
        last_seen_at=profile.get("last_seen_at") or "",
        last_seen_event_id=profile.get("source_event_id"),
    )
