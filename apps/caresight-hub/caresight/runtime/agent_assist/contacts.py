from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_CONTACT_ALLOWLIST_PATH = (
    Path(__file__).resolve().parents[3] / "config" / "hermes" / "allowlisted-contacts.example.json"
)


def load_contact_allowlist(path: str | Path = DEFAULT_CONTACT_ALLOWLIST_PATH) -> dict[str, dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    contacts = payload.get("contacts", [])
    allowlist: dict[str, dict[str, Any]] = {}
    for contact in contacts:
        contact_id = str(contact["contact_id"]).strip()
        if not contact_id:
            raise ValueError("contact_id is required in allowlist")
        allowlist[contact_id] = contact
    return allowlist


def contact_ids(allowlist: dict[str, dict[str, Any]]) -> set[str]:
    return set(allowlist)
