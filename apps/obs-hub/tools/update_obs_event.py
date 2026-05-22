#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB = ROOT / "apps" / "caresight-hub" / "data" / "caresight-v0.sqlite3"
APP_DIR = ROOT / "apps" / "obs-hub"
SAMPLE_EVENT_PATH = APP_DIR / "config" / "sample_event.json"
DEFAULT_OUTPUT = APP_DIR / "config" / "current_event.json"
DEFAULT_JS_OUTPUT = APP_DIR / "config" / "current_event.js"
DEFAULT_LIVE_PREVIEW = APP_DIR / "config" / "live_preview.jpg"
FORBIDDEN_TERMS = [
    "fall detected",
    "emergency detected",
    "medication confirmed",
    "patient stable",
    "ai diagnosis",
    "dispatching help",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update CareSight OBS overlay state from local data.")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="CareSight SQLite database path.")
    parser.add_argument("--event-id", help="Event ID to publish. Defaults to latest event.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Overlay JSON path to write.")
    parser.add_argument("--js-output", default=str(DEFAULT_JS_OUTPUT), help="Overlay JavaScript path to write.")
    parser.add_argument("--site-name", default="Maple Residence")
    parser.add_argument("--site-mode", default="Observation Mode")
    parser.add_argument("--recent-limit", type=int, default=4)
    parser.add_argument("--sample", action="store_true", help="Copy sample fixture data into current_event.json.")
    parser.add_argument(
        "--live-preview",
        default=str(DEFAULT_LIVE_PREVIEW),
        help="Annotated detector preview image path exposed to OBS browser overlays.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print overlay JSON without writing.")
    parser.add_argument("--watch", action="store_true", help="Continuously refresh overlay state from SQLite.")
    parser.add_argument("--interval-seconds", type=float, default=2.0, help="Watch refresh interval.")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def latest_event_id(conn: sqlite3.Connection) -> str:
    row = conn.execute(
        "SELECT event_id FROM events ORDER BY occurred_at DESC, event_id DESC LIMIT 1"
    ).fetchone()
    if row is None:
        raise ValueError("no events found in SQLite; use --sample or provide an event_id after a live proof run")
    return str(row["event_id"])


def event_row(conn: sqlite3.Connection, event_id: str) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT
          events.*,
          cameras.name AS camera_name,
          zones.name AS zone_name
        FROM events
        LEFT JOIN cameras ON cameras.camera_id = events.camera_id
        LEFT JOIN zones ON zones.zone_id = events.zone_id
        WHERE events.event_id = ?
        """,
        (event_id,),
    ).fetchone()
    if row is None:
        raise KeyError(event_id)
    return row


def latest_draft(conn: sqlite3.Connection, event_id: str) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT * FROM agent_drafts
        WHERE event_id = ?
        ORDER BY created_at DESC, draft_id DESC
        LIMIT 1
        """,
        (event_id,),
    ).fetchone()


def latest_action_request(conn: sqlite3.Connection, event_id: str) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT * FROM agent_action_requests
        WHERE event_id = ?
        ORDER BY created_at DESC, request_id DESC
        LIMIT 1
        """,
        (event_id,),
    ).fetchone()


def recent_event_rows(conn: sqlite3.Connection, limit: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
          events.event_id,
          events.event_type,
          events.status,
          events.occurred_at,
          events.camera_id,
          events.evidence_json,
          cameras.name AS camera_name,
          zones.name AS zone_name
        FROM events
        LEFT JOIN cameras ON cameras.camera_id = events.camera_id
        LEFT JOIN zones ON zones.zone_id = events.zone_id
        ORDER BY events.occurred_at DESC, events.event_id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def recent_check_rows(conn: sqlite3.Connection, limit: int) -> list[sqlite3.Row]:
    try:
        return conn.execute(
            """
            SELECT * FROM observation_checks
            ORDER BY completed_at DESC, check_id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    except sqlite3.OperationalError:
        return []


def display_label(event_type: str) -> str:
    labels = {
        "possible_floor_stay": "Possible floor-stay",
        "missing_off_camera_extended": "Extended inactivity observed",
        "routine_activity": "Routine activity observed",
    }
    return labels.get(event_type, event_type.replace("_", " ").title())


def display_event_id(event_id: str) -> str:
    if event_id.startswith("evt_") and len(event_id) > 18:
        return f"{event_id[:10]}...{event_id[-6:]}"
    if len(event_id) > 18:
        return f"{event_id[:8]}...{event_id[-6:]}"
    return event_id


def review_status(status: str) -> str:
    if status == "human_confirmed":
        return "reviewed"
    if status == "dismissed":
        return "reviewed"
    if status == "needs_followup":
        return "needs_followup"
    return "unreviewed"


def escalation_state(action_request: sqlite3.Row | None) -> str:
    if action_request is None:
        return "draft_caregiver_alert_prepared"
    if action_request["escalation_level"] == "urgent_handoff":
        return "draft_caregiver_alert_prepared"
    return "caregiver_update_prepared"


def room_for_event(row: sqlite3.Row) -> str:
    evidence = json.loads(row["evidence_json"] or "{}")
    return str(evidence.get("room_name") or row["zone_name"] or row["camera_name"] or row["camera_id"])


def camera_label(row: sqlite3.Row) -> str:
    camera_id = str(row["camera_id"] or "")
    camera_aliases = {
        "living_room": "C1",
        "kitchen": "C2",
        "hallway": "C3",
        "bedroom": "C4",
    }
    return camera_aliases.get(camera_id, camera_id or "C1")


def format_activity_time(value: str | None) -> str:
    if not value:
        return "unknown"
    parsed = parse_datetime(value)
    if parsed is None:
        return value
    return parsed.astimezone().strftime("%-I:%M %p")


def parse_datetime(value: str) -> datetime | None:
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed
    except ValueError:
        return None


def activity_from_event(row: sqlite3.Row) -> dict[str, str]:
    return {
        "time": format_activity_time(row["occurred_at"]),
        "label": display_label(str(row["event_type"])),
        "zone": room_for_event(row),
        "status": review_status(str(row["status"])).replace("_", " ").title(),
    }


def activity_from_check(row: sqlite3.Row) -> dict[str, str]:
    status = str(row["status"])
    label = "Routine activity observed" if status == "no_possible_floor_stay_event" else status.replace("_", " ").title()
    return {
        "time": format_activity_time(row["completed_at"]),
        "label": label,
        "zone": str(row["camera_id"] or "Configured camera").replace("_", " ").title(),
        "status": "Logged",
    }


def build_overlay_state(conn: sqlite3.Connection, args: argparse.Namespace) -> dict[str, Any]:
    event_id = args.event_id or latest_event_id(conn)
    event = event_row(conn, event_id)
    draft = latest_draft(conn, event_id)
    action_request = latest_action_request(conn, event_id)
    room = room_for_event(event)
    observed_at = str(event["occurred_at"])

    recent_events = [activity_from_event(row) for row in recent_event_rows(conn, args.recent_limit)]
    remaining = max(args.recent_limit - len(recent_events), 0)
    recent_checks = [activity_from_check(row) for row in recent_check_rows(conn, remaining)] if remaining else []

    state = {
        "site": {
            "name": args.site_name,
            "mode": args.site_mode,
        },
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "source": {
            "kind": "sqlite",
            "database": str(Path(args.db)),
            "event_id": event_id,
        },
        "current_event": {
            "event_id": event_id,
            "display_id": display_event_id(event_id),
            "event_type": str(event["event_type"]),
            "display_label": display_label(str(event["event_type"])),
            "zone": room,
            "camera_id": camera_label(event),
            "observed_at": observed_at,
            "subject_label": "Resident",
            "review_status": review_status(str(event["status"])),
            "escalation_state": escalation_state(action_request),
            "suggested_next_step": suggested_next_step(draft),
        },
        "recent_activity": (recent_events + recent_checks)[: args.recent_limit],
        "camera_health": "Configured locally",
        "live_preview": live_preview_state(args.live_preview),
        "constraints": [
            "Raw video stays local",
            "Human review required",
            "No emergency dispatch",
            "Not a medical device",
        ],
    }
    assert_safe_language(state)
    return state


def suggested_next_step(draft: sqlite3.Row | None) -> str:
    if draft is not None and draft["validation_status"] == "validated":
        return "Review the live feed and approved caregiver alert draft."
    return "Check live feed and contact caregiver if concern remains"


def live_preview_state(path_value: str) -> dict[str, Any]:
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT / path
    return {
        "path": str(path),
        "url": path.resolve().as_uri(),
        "available": path.exists(),
        "updated_at": datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat().replace("+00:00", "Z")
        if path.exists()
        else None,
        "description": "Annotated detector preview frame",
    }


def assert_safe_language(value: Any) -> None:
    text = json.dumps(value, sort_keys=True).lower()
    for forbidden in FORBIDDEN_TERMS:
        if forbidden in text:
            raise ValueError(f"unsafe OBS overlay wording: {forbidden}")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_js(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, indent=2, sort_keys=True)
    path.write_text(f"window.CareSightOverlayData = {serialized};\n", encoding="utf-8")


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    if args.sample:
        payload = load_json(SAMPLE_EVENT_PATH)
    else:
        db = Path(args.db)
        if not db.is_absolute():
            db = ROOT / db
        if not db.exists():
            raise SystemExit(f"SQLite database not found: {db}. Use --sample for fixture overlay data.")
        with connect(db) as conn:
            payload = build_overlay_state(conn, args)

    assert_safe_language(payload)
    return payload


def write_outputs(payload: dict[str, Any], output: Path, js_output: Path) -> None:
    write_json(output, payload)
    write_js(js_output, payload)


def main() -> int:
    args = parse_args()
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    js_output = Path(args.js_output)
    if not js_output.is_absolute():
        js_output = ROOT / js_output

    if args.watch and args.dry_run:
        raise SystemExit("--watch cannot be combined with --dry-run")
    if args.watch and args.sample:
        raise SystemExit("--watch cannot be combined with --sample")
    if args.interval_seconds <= 0:
        raise SystemExit("--interval-seconds must be greater than 0")

    if args.watch:
        print(
            json.dumps(
                {
                    "overlay_watch_started": True,
                    "interval_seconds": args.interval_seconds,
                    "overlay_script": str(js_output),
                    "overlay_state": str(output),
                },
                sort_keys=True,
            )
        )
        last_event_id = None
        while True:
            payload = build_payload(args)
            write_outputs(payload, output, js_output)
            event_id = payload["current_event"]["event_id"]
            if event_id != last_event_id:
                print(json.dumps({"overlay_state_written": str(output), "event_id": event_id}, sort_keys=True), flush=True)
                last_event_id = event_id
            time.sleep(args.interval_seconds)
        return 0

    payload = build_payload(args)
    if args.dry_run:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        write_outputs(payload, output, js_output)
        print(
            json.dumps(
                {
                    "event_id": payload["current_event"]["event_id"],
                    "overlay_script_written": str(js_output),
                    "overlay_state_written": str(output),
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
