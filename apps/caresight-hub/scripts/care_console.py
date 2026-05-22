import argparse
import json
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
DEFAULT_DB_PATH = ROOT_DIR / "data" / "caresight-v0.sqlite3"
DEFAULT_ALLOWLIST_PATH = ROOT_DIR / "config" / "hermes" / "allowlisted-contacts.example.json"
DEFAULT_RUNTIME_PYTHON = ROOT_DIR / ".venv" / "bin" / "python"
DEFAULT_OBS_STATE_PATH = ROOT_DIR.parents[1] / "apps" / "obs-hub" / "config" / "current_event.json"
DEFAULT_OBS_PREVIEW_PATH = ROOT_DIR.parents[1] / "apps" / "obs-hub" / "config" / "live_preview.jpg"


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
    escalation_receipt_parser = subparsers.add_parser(
        "escalation-receipt",
        help="Render read-only escalation evidence for one event as JSON or Markdown.",
    )
    escalation_receipt_parser.add_argument("event_id")
    escalation_receipt_parser.add_argument("--format", choices=["json", "markdown"], default="json")
    escalation_receipt_parser.add_argument("--output", help="Optional local output path.")
    escalation_receipt_parser.add_argument("--obs-state", default=str(DEFAULT_OBS_STATE_PATH))
    escalation_receipt_parser.add_argument("--live-preview", default=str(DEFAULT_OBS_PREVIEW_PATH))
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
    agent_draft_parser.add_argument("--provider", choices=["fake", "gemma"], default="fake")
    agent_draft_parser.add_argument("--gemma-base-url", default="http://127.0.0.1:8080/v1")
    agent_draft_parser.add_argument(
        "--gemma-model",
        default="apps/caresight-hub/models/reasoning/gemma/gemma-4-e2b-it-4bit",
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
    stage_parser.add_argument("--escalation-level", choices=["routine", "attention", "urgent_handoff"], default="attention")
    stage_parser.add_argument("--recipient-role", choices=["caregiver", "emergency_contact"])
    stage_parser.add_argument("--allowed-contact-id", action="append", default=[])
    stage_parser.add_argument(
        "--allowlist-config",
        default=os.environ.get("CARESIGHT_CONTACT_ALLOWLIST_PATH", str(DEFAULT_ALLOWLIST_PATH)),
        help="Redacted local contact allowlist JSON for iMessage/FaceTime staging.",
    )
    stage_parser.add_argument(
        "--response-option",
        action="append",
        choices=[
            "acknowledge_text_update",
            "request_local_screen_capture",
            "request_facetime_handoff",
            "dismiss_after_review",
        ],
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
    payload_parser = subparsers.add_parser(
        "hermes-handoff-payload",
        help="Render the non-executing Hermes handoff payload for one staged action request.",
    )
    payload_parser.add_argument("request_id")
    attempt_parser = subparsers.add_parser(
        "record-execution-attempt",
        help="Record a local dry-run execution attempt for one staged action request.",
    )
    attempt_parser.add_argument("request_id")
    attempt_parser.add_argument("--harness", choices=["hermes"], default="hermes")
    attempt_parser.add_argument("--kind", choices=["dry_run"], default="dry_run")
    hermes_dry_run_parser = subparsers.add_parser(
        "hermes-dry-run",
        help="Invoke Hermes no-send preflight and record a local execution-attempt receipt.",
    )
    hermes_dry_run_parser.add_argument("request_id")
    hermes_dry_run_parser.add_argument(
        "--vendor-path",
        default=str(ROOT_DIR / "vendor" / "hermes-agent"),
        help="Vendored Hermes path.",
    )
    list_attempts_parser = subparsers.add_parser(
        "list-execution-attempts",
        help="List local execution attempts for one staged action request.",
    )
    list_attempts_parser.add_argument("request_id")
    subparsers.add_parser(
        "hermes-config-plan",
        help="Render the workspace-local Hermes and local model serving plan.",
    )
    return parser.parse_args()


def main() -> None:
    if (
        "hermes-dry-run" in sys.argv
        and DEFAULT_RUNTIME_PYTHON.exists()
        and os.environ.get("CARESIGHT_CONSOLE_REEXEC") != "1"
    ):
        env = {**os.environ, "CARESIGHT_CONSOLE_REEXEC": "1"}
        os.execve(str(DEFAULT_RUNTIME_PYTHON), [str(DEFAULT_RUNTIME_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]], env)

    from caresight.runtime.alerts import draft_caregiver_alert
    from caresight.runtime.dashboard import build_dashboard_state
    from caresight.runtime.demo_surface import (
        build_blackbox_receipt,
        build_escalation_receipt,
        build_human_review_packet,
        render_blackbox_receipt_markdown,
        render_escalation_receipt_markdown,
        render_review_packet_markdown,
    )
    from caresight.runtime.agent_assist import (
        build_agent_draft,
        build_execution_attempt,
        build_harness_plan,
        build_hermes_config_plan,
        build_hermes_handoff_payload,
        contact_ids,
        GemmaLocalProvider,
        load_contact_allowlist,
        run_hermes_dry_run,
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

    if args.command == "escalation-receipt":
        receipt = build_escalation_receipt(
            store,
            args.event_id,
            overlay_state_path=args.obs_state,
            live_preview_path=args.live_preview,
        )
        _print_or_write(_render_payload(receipt, args.format, render_escalation_receipt_markdown), args.output)
        return

    if args.command == "agent-draft":
        provider = None
        if args.provider == "gemma":
            provider = GemmaLocalProvider(endpoint=args.gemma_base_url, model=args.gemma_model)
        draft = build_agent_draft(store, args.event_id, purpose=args.purpose, provider=provider)
        print(json.dumps(draft, indent=2, sort_keys=True))
        return

    if args.command == "stage-action-request":
        allowlist = load_contact_allowlist(args.allowlist_config)
        request = stage_action_request(
            store,
            event_id=args.event_id,
            source_draft_id=args.draft_id,
            requested_action=args.action,
            destination=args.destination,
            escalation_level=args.escalation_level,
            recipient_role=args.recipient_role,
            allowed_contact_ids=args.allowed_contact_id,
            response_options=args.response_option,
            contact_allowlist=contact_ids(allowlist),
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

    if args.command == "hermes-handoff-payload":
        request = store.get_agent_action_request(args.request_id)
        draft = store.get_agent_draft(request["source_draft_id"])
        print(json.dumps(build_hermes_handoff_payload(request, draft=draft), indent=2, sort_keys=True))
        return

    if args.command == "record-execution-attempt":
        request = store.get_agent_action_request(args.request_id)
        draft = store.get_agent_draft(request["source_draft_id"])
        payload = build_hermes_handoff_payload(request, draft=draft)
        attempt = build_execution_attempt(
            store,
            request=request,
            payload=payload,
            harness=args.harness,
            attempt_kind=args.kind,
            result="payload_logged_no_send",
        )
        print(json.dumps(attempt, indent=2, sort_keys=True))
        return

    if args.command == "hermes-dry-run":
        request = store.get_agent_action_request(args.request_id)
        draft = store.get_agent_draft(request["source_draft_id"])
        attempt = run_hermes_dry_run(store, request=request, draft=draft, vendor_path=args.vendor_path)
        print(json.dumps(attempt, indent=2, sort_keys=True))
        return

    if args.command == "list-execution-attempts":
        print(json.dumps(store.list_agent_execution_attempts(args.request_id), indent=2, sort_keys=True))
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
