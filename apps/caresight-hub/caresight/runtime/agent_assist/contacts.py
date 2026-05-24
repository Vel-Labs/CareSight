from __future__ import annotations

import json
import hashlib
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


def verify_contact_target(
    allowlist: dict[str, dict[str, Any]],
    *,
    contact_id: str,
    channel: str,
    target: str,
) -> dict[str, Any]:
    try:
        contact = allowlist[contact_id]
    except KeyError as exc:
        raise ValueError(f"contact id not allowlisted: {contact_id}") from exc

    if not target.strip():
        raise ValueError(f"missing live {channel} target for {contact_id}")

    channel_ref = str(contact.get("channel_refs", {}).get(channel, "")).strip()
    digest = target_sha256(target)
    if channel_ref and channel_ref != "redacted-local-channel-ref" and target == channel_ref:
        return {
            "status": "verified",
            "contact_id": contact_id,
            "channel": channel,
            "method": "allowlist_channel_ref",
            "target_hash": digest,
        }

    approved_hashes = _approved_hashes(contact, channel)
    if digest in approved_hashes or digest[:12] in approved_hashes:
        return {
            "status": "verified",
            "contact_id": contact_id,
            "channel": channel,
            "method": "allowlist_target_hash",
            "target_hash": digest,
        }

    raise ValueError(f"live {channel} target does not match allowlisted contact: {contact_id}")


def target_sha256(target: str) -> str:
    return hashlib.sha256(target.encode("utf-8")).hexdigest()


def _approved_hashes(contact: dict[str, Any], channel: str) -> set[str]:
    hashes: set[str] = set()
    for key in ("channel_hashes", "approved_target_hashes"):
        values = contact.get(key, {})
        if not isinstance(values, dict):
            continue
        channel_value = values.get(channel)
        if isinstance(channel_value, str):
            hashes.add(channel_value.strip())
        elif isinstance(channel_value, list):
            hashes.update(str(item).strip() for item in channel_value)
    return {item for item in hashes if item}
