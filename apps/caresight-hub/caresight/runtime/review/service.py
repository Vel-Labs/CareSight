from __future__ import annotations

from typing import Any, Protocol


class ReviewServiceError(ValueError):
    pass


class ReviewStore(Protocol):
    def list_events(self, *, status: str | None = None) -> list[dict[str, Any]]: ...

    def get_event_context(self, event_id: str) -> dict[str, Any]: ...

    def list_event_observations(self, event_id: str) -> list[dict[str, Any]]: ...

    def list_event_reviews(self, event_id: str) -> list[dict[str, Any]]: ...

    def list_journal_entries(self, event_id: str) -> list[dict[str, Any]]: ...

    def list_agent_handoffs(self, event_id: str) -> list[dict[str, Any]]: ...

    def list_appearance_profiles_for_event(self, event_id: str) -> list[dict[str, Any]]: ...

    def record_event_review(
        self,
        event_id: str,
        *,
        reviewer: str,
        decision: str,
        note: str | None = None,
    ) -> dict[str, Any]: ...


AUTOMATION_REVIEWERS = {
    "agent",
    "assistant",
    "automation",
    "bot",
    "carebot",
    "chatgpt",
    "codex",
    "llm",
    "model",
    "openclaw",
}


class ReviewService:
    def __init__(self, store: ReviewStore):
        self._store = store

    def list_events(self, *, include_all: bool = False) -> list[dict[str, Any]]:
        status = None if include_all else "awaiting_human_confirmation"
        return self._store.list_events(status=status)

    def get_event_summary(self, event_id: str) -> dict[str, Any]:
        return self._store.get_event_context(event_id)

    def confirm_event(
        self,
        event_id: str,
        *,
        reviewer: str | None,
        note: str | None = None,
    ) -> dict[str, Any]:
        return self._record_human_review(
            event_id,
            reviewer=reviewer,
            decision="human_confirmed",
            note=note,
        )

    def dismiss_event(
        self,
        event_id: str,
        *,
        reviewer: str | None,
        note: str | None = None,
    ) -> dict[str, Any]:
        return self._record_human_review(
            event_id,
            reviewer=reviewer,
            decision="dismissed",
            note=note,
        )

    def list_journal_entries(self, event_id: str) -> list[dict[str, Any]]:
        return self._store.list_journal_entries(event_id)

    def get_audit_chain(self, event_id: str) -> dict[str, Any]:
        return {
            "event": self._store.get_event_context(event_id),
            "observations": self._store.list_event_observations(event_id),
            "reviews": self._store.list_event_reviews(event_id),
            "journal_entries": self._store.list_journal_entries(event_id),
            "agent_handoffs": self._store.list_agent_handoffs(event_id),
        }

    def list_appearance_profiles_for_event(self, event_id: str) -> list[dict[str, Any]]:
        return self._store.list_appearance_profiles_for_event(event_id)

    def _record_human_review(
        self,
        event_id: str,
        *,
        reviewer: str | None,
        decision: str,
        note: str | None,
    ) -> dict[str, Any]:
        human_reviewer = validate_human_reviewer(reviewer)
        return self._store.record_event_review(
            event_id,
            reviewer=human_reviewer,
            decision=decision,
            note=note,
        )


def validate_human_reviewer(reviewer: str | None) -> str:
    if reviewer is None or not reviewer.strip():
        raise ReviewServiceError("--reviewer is required")

    normalized = " ".join(reviewer.strip().split())
    if normalized.casefold() in AUTOMATION_REVIEWERS:
        raise ReviewServiceError("reviewer must be an authorized human")
    return normalized
