from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4


def current_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def next_check_timestamp(minutes: int = 15) -> str:
    return (datetime.now(UTC) + timedelta(minutes=minutes)).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_runtime_validation_receipt(
    *,
    check_type: str,
    target: str,
    command: list[str] | str,
    status: str,
    started_at: str | None = None,
    completed_at: str | None = None,
    result: dict | None = None,
    blockers: list[dict] | None = None,
    safety_boundaries: list[str] | None = None,
    next_check_after: str | None = None,
    receipt_id: str | None = None,
) -> dict[str, object]:
    completed = completed_at or current_timestamp()
    return {
        "schema": "runtime-validation-receipt",
        "receipt_id": receipt_id or f"runtime_receipt_{uuid4().hex}",
        "check_type": check_type,
        "started_at": started_at or completed,
        "completed_at": completed,
        "status": status,
        "target": target,
        "command": command if isinstance(command, str) else " ".join(command),
        "result": result or {},
        "safety_boundaries": safety_boundaries
        or ["no_live_send", "no_facetime_call", "no_tts_playback", "local_probe_only"],
        "blockers": blockers or [],
        "next_check_after": next_check_after or next_check_timestamp(),
    }
