from __future__ import annotations


def should_stop_loop(
    *,
    started_at: float,
    now: float,
    max_seconds: float | None,
    event_persisted: bool,
    stop_after_event: bool,
) -> bool:
    if stop_after_event and event_persisted:
        return True
    if max_seconds is not None and now - started_at >= max_seconds:
        return True
    return False
