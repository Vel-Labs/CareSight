from __future__ import annotations

from typing import Any


def journal_preview(entries: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "journal_id": entry["journal_id"],
            "title": entry["title"],
            "created_at": entry["created_at"],
            "created_by": entry["created_by"],
            "body": entry["body"],
        }
        for entry in entries
    ]
