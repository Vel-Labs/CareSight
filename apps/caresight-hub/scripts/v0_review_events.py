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

    return parser.parse_args()


def main() -> None:
    from caresight.storage.sqlite_store import SQLiteStore

    args = parse_args()
    store = SQLiteStore(args.db)
    store.initialize()

    if args.command == "list":
        status = None if args.all else "awaiting_human_confirmation"
        print(format_event_list(store.list_events(status=status)))
        return

    if args.command == "show":
        print(format_event_summary(store.get_event_context(args.event_id)))
        return

    if args.command in {"confirm", "dismiss"}:
        if not args.reviewer or not args.reviewer.strip():
            raise SystemExit("--reviewer is required")
        decision = "human_confirmed" if args.command == "confirm" else "dismissed"
        result = store.record_event_review(
            args.event_id,
            reviewer=args.reviewer,
            decision=decision,
            note=args.note,
        )
        print(f"Event {result['event_id']} status: {result['decision']}")
        print(f"Review: {result['review_id']}")
        print(f"Journal: {result['journal_id']}")
        print(f"Agent handoff: {result['handoff_id']} (report_only)")
        return

    if args.command == "journal":
        entries = store.list_journal_entries(args.event_id)
        print(format_journal(args.event_id, entries))
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


if __name__ == "__main__":
    main()
