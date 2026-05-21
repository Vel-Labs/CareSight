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
    review_packet_parser = subparsers.add_parser(
        "review-packet",
        help="Render a read-only human review packet as JSON or Markdown.",
    )
    review_packet_parser.add_argument("event_id")
    review_packet_parser.add_argument("--format", choices=["json", "markdown"], default="json")
    review_packet_parser.add_argument("--output", help="Optional local output path.")
    receipt_parser = subparsers.add_parser(
        "blackbox-receipt",
        help="Render a read-only blackbox receipt as JSON or Markdown.",
    )
    receipt_parser.add_argument("event_id")
    receipt_parser.add_argument("--format", choices=["json", "markdown"], default="json")
    receipt_parser.add_argument("--output", help="Optional local output path.")
    agent_draft_parser = subparsers.add_parser(
        "agent-draft",
        help="Create and persist a fake-provider agent draft as JSON.",
    )
    agent_draft_parser.add_argument("event_id")
    agent_draft_parser.add_argument(
        "--purpose",
        choices=["caregiver_summary", "alert_draft", "apple_notes_entry", "handoff_packet", "audit_summary"],
        default="caregiver_summary",
    )
    stage_parser = subparsers.add_parser(
        "stage-action-request",
        help="Stage a local agent action request without executing it.",
    )
    stage_parser.add_argument("event_id")
    stage_parser.add_argument("--draft-id", required=True)
    stage_parser.add_argument(
        "--action",
        required=True,
        choices=[
            "send_caregiver_message",
            "send_imessage_draft",
            "create_apple_note",
            "prepare_handoff_packet",
            "prepare_facetime_handoff",
            "play_tts_utterance",
        ],
    )
    stage_parser.add_argument(
        "--destination",
        choices=["caregiver_console", "imessage", "apple_notes", "facetime", "local_tts", "handoff_packet"],
    )
    list_actions_parser = subparsers.add_parser(
        "list-action-requests",
        help="List staged local action requests for an event.",
    )
    list_actions_parser.add_argument("event_id")
    harness_parser = subparsers.add_parser(
        "agent-harness-plan",
        help="Render a non-executing OpenClaw/Hermes harness plan for one staged action request.",
    )
    harness_parser.add_argument("request_id")
    harness_parser.add_argument("--prefer", choices=["hermes", "openclaw", "auto"], default="auto")
    subparsers.add_parser(
        "hermes-config-plan",
        help="Render the workspace-local Hermes and local model serving plan.",
    )
    return parser.parse_args()


def main() -> None:
    from caresight.runtime.alerts import draft_caregiver_alert
    from caresight.runtime.dashboard import build_dashboard_state
    from caresight.runtime.demo_surface import (
        build_blackbox_receipt,
        build_human_review_packet,
        render_blackbox_receipt_markdown,
        render_review_packet_markdown,
    )
    from caresight.runtime.agent_assist import (
        build_agent_draft,
        build_harness_plan,
        build_hermes_config_plan,
        stage_action_request,
    )
    from caresight.runtime.review import ReviewService
    from caresight.storage.sqlite_store import SQLiteStore

    args = parse_args()

    if args.command == "hermes-config-plan":
        print(json.dumps(build_hermes_config_plan(), indent=2, sort_keys=True))
        return

    store = SQLiteStore(args.db)
    store.initialize()
    service = ReviewService(store)

    if args.command == "dashboard":
        print(json.dumps(build_dashboard_state(service, event_id=args.event_id), indent=2, sort_keys=True))
        return

    if args.command == "alert-draft":
        print(json.dumps(draft_caregiver_alert(service.get_audit_chain(args.event_id)), indent=2, sort_keys=True))
        return

    if args.command == "review-packet":
        packet = build_human_review_packet(service.get_audit_chain(args.event_id))
        _print_or_write(_render_payload(packet, args.format, render_review_packet_markdown), args.output)
        return

    if args.command == "blackbox-receipt":
        audit = service.get_audit_chain(args.event_id)
        dashboard = build_dashboard_state(service, event_id=args.event_id)
        alert = draft_caregiver_alert(audit)
        receipt = build_blackbox_receipt(audit, dashboard_state=dashboard, alert_draft=alert)
        _print_or_write(_render_payload(receipt, args.format, render_blackbox_receipt_markdown), args.output)
        return

    if args.command == "agent-draft":
        draft = build_agent_draft(store, args.event_id, purpose=args.purpose)
        print(json.dumps(draft, indent=2, sort_keys=True))
        return

    if args.command == "stage-action-request":
        request = stage_action_request(
            store,
            event_id=args.event_id,
            source_draft_id=args.draft_id,
            requested_action=args.action,
            destination=args.destination,
        )
        print(json.dumps(request, indent=2, sort_keys=True))
        return

    if args.command == "list-action-requests":
        print(json.dumps(store.list_agent_action_requests(args.event_id), indent=2, sort_keys=True))
        return

    if args.command == "agent-harness-plan":
        request = store.get_agent_action_request(args.request_id)
        draft = store.get_agent_draft(request["source_draft_id"])
        plan = build_harness_plan(request, draft=draft, preferred_harness=args.prefer)
        print(json.dumps(plan, indent=2, sort_keys=True))
        return


def _render_payload(payload: dict, output_format: str, markdown_renderer) -> str:
    if output_format == "markdown":
        return markdown_renderer(payload) + "\n"
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _print_or_write(rendered: str, output: str | None) -> None:
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(rendered, encoding="utf-8")
        return
    print(rendered, end="")


if __name__ == "__main__":
    main()
