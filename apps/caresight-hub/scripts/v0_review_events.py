import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
DEFAULT_DB_PATH = ROOT_DIR / "data" / "caresight-v0.sqlite3"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review CareSight v0 events.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="CareSight SQLite database.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List event inbox rows.")
    list_parser.add_argument("--all", action="store_true", help="Include non-awaiting events.")

    show_parser = subparsers.add_parser("show", help="Show a human-readable event summary.")
    show_parser.add_argument("event_id")

    for command in ("confirm", "dismiss"):
        review_parser = subparsers.add_parser(command, help=f"{command.title()} an event.")
        review_parser.add_argument("event_id")
        review_parser.add_argument("--reviewer")
        review_parser.add_argument("--note")

    journal_parser = subparsers.add_parser("journal", help="Show journal entries for an event.")
    journal_parser.add_argument("event_id")

    audit_parser = subparsers.add_parser("audit", help="Show read-only SQLite audit chain.")
    audit_parser.add_argument("event_id")

    return parser.parse_args()


def main() -> None:
    from caresight.runtime.review import ReviewService, ReviewServiceError
    from caresight.storage.sqlite_store import SQLiteStore

    args = parse_args()
    store = SQLiteStore(args.db)
    store.initialize()
    service = ReviewService(store)

    if args.command == "list":
        print(format_event_list(service.list_events(include_all=args.all)))
        return

    if args.command == "show":
        print(format_event_summary(service.get_event_summary(args.event_id)))
        return

    if args.command in {"confirm", "dismiss"}:
        try:
            if args.command == "confirm":
                result = service.confirm_event(
                    args.event_id,
                    reviewer=args.reviewer,
                    note=args.note,
                )
            else:
                result = service.dismiss_event(
                    args.event_id,
                    reviewer=args.reviewer,
                    note=args.note,
                )
        except ReviewServiceError as exc:
            raise SystemExit(str(exc)) from exc
        print(f"Event {result['event_id']} status: {result['decision']}")
        print(f"Review: {result['review_id']}")
        print(f"Journal: {result['journal_id']}")
        print(f"Agent handoff: {result['handoff_id']} (report_only)")
        return

    if args.command == "journal":
        entries = service.list_journal_entries(args.event_id)
        print(format_journal(args.event_id, entries))
        return

    if args.command == "audit":
        print(format_audit(service.get_audit_chain(args.event_id)))
        return


def format_event_list(events: list[dict]) -> str:
    if not events:
        return "No events found."

    lines = ["CareSight Event Inbox"]
    for event in events:
        lines.append(
            f"- {event['event_id']} | {event['event_type']} | "
            f"{event['status']} | {event['occurred_at']}"
        )
    return "\n".join(lines)


def format_event_summary(event: dict) -> str:
    evidence = event["evidence"]
    camera_name = event.get("camera_name") or event["camera_id"]
    zone_name = event.get("zone_name") or event.get("zone_id") or "unknown zone"
    dwell_seconds = float(evidence.get("dwell_seconds", 0.0))
    detection_confidence = float(evidence.get("detection_confidence", 0.0)) * 100
    blocked_actions = ", ".join(action.replace("_", " ") for action in event["blocked_actions"])

    return "\n".join(
        [
            f"Event: {event['event_id']}",
            f"Possible floor-stay event in {camera_name}.",
            f"Observed in {zone_name} for {dwell_seconds:.2f} seconds.",
            f"Detection confidence: {detection_confidence:.1f}%.",
            f"Status: {event['status'].replace('_', ' ')}.",
            f"Zone: {zone_name}.",
            f"Snapshot: {evidence.get('snapshot_path', 'not recorded')}",
            f"Blocked actions: {blocked_actions}.",
        ]
    )


def format_journal(event_id: str, entries: list[dict]) -> str:
    if not entries:
        return f"Care Journal\nNo journal entries for {event_id}."

    lines = [f"Care Journal: {event_id}"]
    for entry in entries:
        lines.extend(
            [
                "",
                f"{entry['title']}",
                f"Created: {entry['created_at']} by {entry['created_by']}",
                entry["body"],
            ]
        )
    return "\n".join(lines)


def format_audit(audit: dict) -> str:
    event = audit["event"]
    evidence = event["evidence"]
    observations = audit["observations"]
    reviews = audit["reviews"]
    journal_entries = audit["journal_entries"]
    handoffs = audit["agent_handoffs"]
    latest_review = reviews[-1] if reviews else None
    latest_handoff = handoffs[-1] if handoffs else None

    lines = [
        "CareSight SQLite Audit",
        f"Event ID: {event['event_id']}",
        f"Event type: {event['event_type']}",
        f"Status: {event['status']}",
        f"Occurred at: {event['occurred_at']}",
        f"Camera: {event.get('camera_name') or event['camera_id']}",
        f"Zone: {event.get('zone_name') or event.get('zone_id') or 'unknown zone'}",
        f"Snapshot path: {evidence.get('snapshot_path', 'not recorded')}",
        f"Observation rows: {len(observations)}",
        f"Review rows: {len(reviews)}",
        f"Journal rows: {len(journal_entries)}",
        f"Agent handoff rows: {len(handoffs)}",
    ]
    if latest_review is not None:
        lines.extend(
            [
                f"Latest reviewer: {latest_review['reviewer']}",
                f"Latest review decision: {latest_review['decision']}",
                f"Latest reviewed at: {latest_review['reviewed_at']}",
            ]
        )
    if latest_handoff is not None:
        payload = latest_handoff["payload"]
        lines.extend(
            [
                f"Latest handoff status: {latest_handoff['status']}",
                f"Latest handoff reviewer: {payload.get('reviewer', 'not recorded')}",
                f"Latest handoff reviewed at: {payload.get('reviewed_at', 'not recorded')}",
                f"Latest handoff journal: {payload.get('journal_id', 'not recorded')}",
            ]
        )
    lines.append(
        "Boundary: SQLite rows are canonical; agents may summarize or draft but cannot confirm, "
        "dismiss, dispatch, diagnose, delete, or become reviewer of record."
    )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
