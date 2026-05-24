from __future__ import annotations

from typing import Any


def execution_attempt_identity(attempt: dict[str, Any]) -> dict[str, Any]:
    return {
        "attempt_id": attempt["attempt_id"],
        "request_id": attempt["request_id"],
        "event_id": attempt["event_id"],
        "execution_state": attempt["execution_state"],
    }
