from __future__ import annotations

from typing import Any, Protocol

from caresight.runtime.alerts import draft_caregiver_alert


class DashboardReviewService(Protocol):
    def list_events(self, *, include_all: bool = False) -> list[dict[str, Any]]: ...

    def get_event_summary(self, event_id: str) -> dict[str, Any]: ...

    def list_journal_entries(self, event_id: str) -> list[dict[str, Any]]: ...

    def get_audit_chain(self, event_id: str) -> dict[str, Any]: ...


def build_dashboard_state(service: DashboardReviewService, *, event_id: str | None = None) -> dict[str, Any]:
    all_events = service.list_events(include_all=True)
    awaiting_events = [event for event in all_events if event["status"] == "awaiting_human_confirmation"]
    requested_event = next((event for event in all_events if event["event_id"] == event_id), None)
    current_event = requested_event or (awaiting_events[0] if awaiting_events else (all_events[0] if all_events else None))
    current_event_id = current_event["event_id"] if current_event else None
    journal_preview = []
    alert_draft = None

    if current_event_id is not None:
        journal_preview = service.list_journal_entries(current_event_id)
        alert_draft = draft_caregiver_alert(service.get_audit_chain(current_event_id))

    return {
        "source_of_truth": "sqlite",
        "view": {
            "requested_event_id": event_id,
            "focused_event_found": event_id is None or requested_event is not None,
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
