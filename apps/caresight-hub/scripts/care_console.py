import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
DEFAULT_DB_PATH = ROOT_DIR / "data" / "caresight-v0.sqlite3"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render local CareSight demo console state.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="CareSight SQLite database.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    dashboard_parser = subparsers.add_parser("dashboard", help="Render local dashboard read model as JSON.")
    dashboard_parser.add_argument("--event-id", help="Focus dashboard journal and alert draft on one event.")
    alert_parser = subparsers.add_parser("alert-draft", help="Render caregiver alert draft as JSON.")
    alert_parser.add_argument("event_id")
    return parser.parse_args()


def main() -> None:
    from caresight.runtime.alerts import draft_caregiver_alert
    from caresight.runtime.dashboard import build_dashboard_state
    from caresight.runtime.review import ReviewService
    from caresight.storage.sqlite_store import SQLiteStore

    args = parse_args()
    store = SQLiteStore(args.db)
    store.initialize()
    service = ReviewService(store)

    if args.command == "dashboard":
        print(json.dumps(build_dashboard_state(service, event_id=args.event_id), indent=2, sort_keys=True))
        return

    if args.command == "alert-draft":
        print(json.dumps(draft_caregiver_alert(service.get_audit_chain(args.event_id)), indent=2, sort_keys=True))
        return


if __name__ == "__main__":
    main()
