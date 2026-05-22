#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT_DIR / "config" / "hermes" / "allowlisted-contacts.local.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an ignored local CareSight caregiver contact allowlist.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Ignored private allowlist path.")
    parser.add_argument("--contact-id", default="contact_emergency_primary")
    parser.add_argument("--role", choices=["caregiver", "emergency_contact"], default="emergency_contact")
    parser.add_argument("--display-label", default="Primary emergency contact")
    parser.add_argument("--imessage", required=True, help="Private iMessage handle, usually a phone or iCloud email.")
    parser.add_argument("--facetime", help="Private FaceTime handle. Defaults to --imessage.")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing local allowlist.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = Path(args.output).expanduser()
    if output.exists() and not args.force:
        raise SystemExit(f"{output} already exists; pass --force to overwrite")

    payload = {
        "schema": "care-contact-allowlist",
        "updated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "notes": [
            "Private local file. Do not commit.",
            "Set CARESIGHT_CONTACT_ALLOWLIST_PATH to this path for live demo commands.",
        ],
        "contacts": [
            {
                "contact_id": args.contact_id,
                "role": args.role,
                "display_label": args.display_label,
                "channel_refs": {
                    "imessage": args.imessage,
                    "facetime": args.facetime or args.imessage,
                },
            }
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "allowlist_path": str(output),
                "contact_id": args.contact_id,
                "status": "written",
                "export": f"export CARESIGHT_CONTACT_ALLOWLIST_PATH={output}",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
