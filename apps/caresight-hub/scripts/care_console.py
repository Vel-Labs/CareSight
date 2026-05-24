import argparse
from datetime import UTC, datetime, timedelta
import json
import os
import sys
from pathlib import Path
from uuid import uuid4

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
DEFAULT_DB_PATH = ROOT_DIR / "data" / "caresight-v0.sqlite3"
DEFAULT_ALLOWLIST_PATH = ROOT_DIR / "config" / "hermes" / "allowlisted-contacts.example.json"
DEFAULT_RUNTIME_PYTHON = ROOT_DIR / ".venv" / "bin" / "python"
DEFAULT_OBS_STATE_PATH = ROOT_DIR.parents[1] / "apps" / "obs-hub" / "config" / "current_event.json"
DEFAULT_OBS_PREVIEW_PATH = ROOT_DIR.parents[1] / "apps" / "obs-hub" / "config" / "live_preview.jpg"
DEFAULT_MODEL_MANIFESTS_PATH = ROOT_DIR / "config" / "model-manifests.example.json"


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
    narrative_parser = subparsers.add_parser(
        "narrative",
        help="Render a SQLite-derived multi-camera narrative as JSON or Markdown.",
    )
    narrative_parser.add_argument("event_id")
    narrative_parser.add_argument("--format", choices=["json", "markdown"], default="json")
    narrative_parser.add_argument("--output", help="Optional local output path.")
    appearance_parser = subparsers.add_parser(
        "appearance-profile",
        help="Inspect or derive local non-biometric daily appearance profiles.",
    )
    appearance_subparsers = appearance_parser.add_subparsers(dest="appearance_command", required=True)
    appearance_list = appearance_subparsers.add_parser("list", help="List active appearance profiles.")
    appearance_list.add_argument("--active-date", help="YYYY-MM-DD active date. Defaults to today/now.")
    appearance_show = appearance_subparsers.add_parser("show", help="Show one appearance profile.")
    appearance_show.add_argument("appearance_profile_id")
    appearance_samples = appearance_subparsers.add_parser("list-samples", help="List retained appearance samples for one profile.")
    appearance_samples.add_argument("appearance_profile_id")
    appearance_summary = appearance_subparsers.add_parser("summarize-today", help="Summarize same-day appearance sample support.")
    appearance_summary.add_argument("--active-date", help="YYYY-MM-DD active date. Defaults to today/now.")
    appearance_describe = appearance_subparsers.add_parser(
        "describe-image",
        help="Describe one local still image and bbox without writing a profile.",
    )
    appearance_describe.add_argument("image_path")
    appearance_describe.add_argument("--bbox", required=True, help="Bounding box as x1,y1,x2,y2.")
    appearance_describe.add_argument("--visual-output", help="Optional annotated local image path.")
    appearance_derive = appearance_subparsers.add_parser(
        "derive-from-event",
        help="Derive/update an unassigned appearance profile from a real event observation and local snapshot.",
    )
    appearance_derive.add_argument("event_id")
    appearance_derive.add_argument(
        "--role",
        choices=[
            "resident_primary",
            "resident_secondary",
            "caregiver_known",
            "visitor_unknown",
            "unknown_person",
            "pet_context",
        ],
        default="unknown_person",
    )
    appearance_assign = appearance_subparsers.add_parser(
        "assign-role",
        help="Assign a same-day role to an appearance profile. Requires authorized human reviewer.",
    )
    appearance_assign.add_argument("appearance_profile_id")
    appearance_assign.add_argument(
        "--role",
        required=True,
        choices=[
            "resident_primary",
            "resident_secondary",
            "caregiver_known",
            "visitor_unknown",
            "unknown_person",
            "pet_context",
        ],
    )
    appearance_assign.add_argument("--reviewer", required=True)
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
    model_doctor_parser = subparsers.add_parser(
        "model-doctor",
        help="Validate local model manifests, paths, checksums, licenses, and purpose lanes.",
    )
    model_doctor_parser.add_argument("--manifest", default=str(DEFAULT_MODEL_MANIFESTS_PATH))
    model_doctor_parser.add_argument("--model-id", action="append", default=[])
    model_doctor_parser.add_argument("--run-validation-command", action="store_true")
    journal_redact_parser = subparsers.add_parser(
        "journal-redact",
        help="Classify and locally redact one journal entry before any external export.",
    )
    journal_redact_parser.add_argument("event_id")
    journal_redact_parser.add_argument("--journal-id", required=True)
    journal_redact_parser.add_argument(
        "--export-classification",
        choices=["local-only", "caregiver-shareable", "clinical-review", "do-not-share"],
        default="local-only",
    )
    journal_redact_parser.add_argument(
        "--engine",
        choices=["local_rules", "openai_privacy_filter", "human_review_only"],
        default="local_rules",
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
        build_multi_camera_narrative,
        render_multi_camera_narrative_markdown,
        render_review_packet_markdown,
    )
    from caresight.runtime.appearance import (
        AppearanceProfileService,
        descriptor_attributes,
        render_appearance_summary,
        summarize_appearance_samples,
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
    from caresight.runtime.model_doctor import check_model_manifest, load_model_manifests
    from caresight.runtime.privacy import (
        build_privacy_redaction_receipt,
        classify_journal_export,
        redact_text_for_export,
    )
    from caresight.runtime.review import ReviewService
    from caresight.storage.sqlite_store import SQLiteStore

    args = parse_args()

    if args.command == "model-doctor":
        manifests = load_model_manifests(args.manifest)
        selected = set(args.model_id)
        if selected:
            manifests = [manifest for manifest in manifests if manifest.get("model_id") in selected]
        if selected and not manifests:
            raise SystemExit("No matching model manifests found.")
        results = [
            check_model_manifest(manifest, run_validation=args.run_validation_command)
            for manifest in manifests
        ]
        print(
            json.dumps(
                {
                    "schema": "model-doctor-report",
                    "manifest": args.manifest,
                    "status": "pass" if all(result["status"] == "pass" for result in results) else "blocked",
                    "results": results,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return

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

    if args.command == "narrative":
        narrative = build_multi_camera_narrative(store, args.event_id)
        _print_or_write(
            _render_payload(narrative, args.format, render_multi_camera_narrative_markdown),
            args.output,
        )
        return

    if args.command == "appearance-profile":
        if args.appearance_command == "list":
            print(json.dumps(store.list_active_appearance_profiles(active_date=args.active_date), indent=2, sort_keys=True))
            return
        if args.appearance_command == "show":
            profile = store.get_appearance_profile(args.appearance_profile_id)
            payload = {
                **profile,
                "summary": render_appearance_summary(_profile_for_render(profile)),
                "observations": store.list_appearance_profile_observations(args.appearance_profile_id),
                "samples": store.list_appearance_profile_samples(args.appearance_profile_id),
            }
            print(json.dumps(payload, indent=2, sort_keys=True))
            return
        if args.appearance_command == "list-samples":
            print(json.dumps(store.list_appearance_profile_samples(args.appearance_profile_id), indent=2, sort_keys=True))
            return
        if args.appearance_command == "summarize-today":
            active_date = args.active_date or utc_now()[:10]
            samples = store.list_appearance_samples_for_date(active_date)
            by_profile = {}
            for sample in samples:
                by_profile.setdefault(sample["appearance_profile_id"], []).append(sample)
            payload = {
                "schema": "appearance-profile-daily-sample-summary",
                "active_date": active_date,
                "profile_count": len(by_profile),
                "profiles": {
                    profile_id: summarize_appearance_samples(profile_samples)
                    for profile_id, profile_samples in sorted(by_profile.items())
                },
                "source_of_truth": "sqlite",
            }
            print(json.dumps(payload, indent=2, sort_keys=True))
            return
        if args.appearance_command == "describe-image":
            from caresight.runtime.appearance import write_appearance_annotation

            bbox_xyxy = _parse_bbox(args.bbox)
            descriptor = AppearanceProfileService().describe_observation(
                bbox_xyxy=bbox_xyxy,
                snapshot_path=args.image_path,
                frame_source="still_image",
                descriptor_source="runtime_observation",
            )
            payload = {
                "schema": "appearance-profile-still-image-descriptor",
                "source_of_truth": "still_image",
                "image_path": args.image_path,
                "bbox_xyxy": list(bbox_xyxy),
                "descriptor_status": descriptor.descriptor_status,
                "descriptor_source": descriptor.descriptor_source,
                "frame_source": descriptor.frame_source,
                "attributes": descriptor_attributes(descriptor),
                "safety_boundaries": [
                    "non_biometric_daily_appearance_only",
                    "same_day_only",
                    "no_named_person_identity",
                    "no_face_recognition",
                    "no_cross_day_identity",
                ],
            }
            if args.visual_output:
                payload["visual_evidence"] = write_appearance_annotation(
                    snapshot_path=args.image_path,
                    output_path=args.visual_output,
                    bbox_xyxy=bbox_xyxy,
                    descriptor=descriptor,
                    label="person 1",
                )
            print(json.dumps(payload, indent=2, sort_keys=True))
            return
        if args.appearance_command == "derive-from-event":
            payload = _derive_appearance_profile_from_event(store, args.event_id, role_assignment=args.role)
            print(json.dumps(payload, indent=2, sort_keys=True))
            return
        if args.appearance_command == "assign-role":
            assignment = store.assign_appearance_profile_role(
                args.appearance_profile_id,
                role_assignment=args.role,
                reviewer=args.reviewer,
            )
            profile = store.get_appearance_profile(args.appearance_profile_id)
            print(json.dumps({**assignment, "profile": profile}, indent=2, sort_keys=True))
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

    if args.command == "journal-redact":
        entries = store.list_journal_entries(args.event_id)
        entry = next((item for item in entries if item["journal_id"] == args.journal_id), None)
        if entry is None:
            raise SystemExit(f"journal entry not found for event: {args.journal_id}")
        classification = classify_journal_export(entry, args.export_classification)
        receipt = build_privacy_redaction_receipt(
            text=entry["body"],
            engine=args.engine,
            model_manifest_id="model_openai_privacy_filter" if args.engine == "openai_privacy_filter" else None,
        )
        redacted_text, _labels = redact_text_for_export(entry["body"])
        store.update_journal_redaction(
            entry["journal_id"],
            export_classification=args.export_classification,
            redaction_receipt=receipt,
        )
        print(
            json.dumps(
                {
                    "schema": "journal-redaction-preview",
                    "event_id": args.event_id,
                    "journal_id": entry["journal_id"],
                    "classification": classification,
                    "redaction_receipt": receipt,
                    "redacted_text": redacted_text,
                    "canonical_text_preserved": True,
                    "not_claimed": receipt["not_claimed"],
                },
                indent=2,
                sort_keys=True,
            )
        )
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


def _derive_appearance_profile_from_event(
    store,
    event_id: str,
    *,
    role_assignment: str,
) -> dict:
    from caresight.runtime.appearance import AppearanceProfileService, descriptor_attributes, render_appearance_summary

    event = store.get_event_context(event_id)
    observations = store.list_event_observations(event_id)
    if not observations:
        raise ValueError(f"event has no observations: {event_id}")
    observation = observations[0]
    evidence = event["evidence"]
    snapshot_path = evidence.get("snapshot_path")
    descriptor = AppearanceProfileService().describe_observation(
        bbox_xyxy=tuple(observation["bbox_json"]),
        snapshot_path=_resolve_snapshot_path(snapshot_path),
        frame_source="event_snapshot" if snapshot_path else None,
        descriptor_source="runtime_observation",
        event_id=event_id,
        observation_id=str(observation["observation_id"]),
    )
    occurred_at = _parse_datetime(event["occurred_at"])
    active_date = occurred_at.date().isoformat()
    expires_at = datetime.combine(
        occurred_at.date() + timedelta(days=1),
        datetime.min.time(),
        tzinfo=UTC,
    ).replace(hour=4)
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    track_id = observation.get("track_id") or evidence.get("track_id")
    profile_id = _appearance_profile_id(active_date, track_id or event_id)
    attributes = descriptor_attributes(descriptor)
    assignment_source = "unassigned" if role_assignment == "unknown_person" else "operator_demo_seed"
    profile = {
        "appearance_profile_id": profile_id,
        "active_date": active_date,
        "created_at": now,
        "updated_at": now,
        "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
        "descriptor_source": descriptor.descriptor_source,
        "created_from": descriptor.descriptor_source,
        "descriptor_status": descriptor.descriptor_status,
        "source_event_id": event_id,
        "source_observation_id": observation["observation_id"],
        "snapshot_path": snapshot_path,
        "frame_source": descriptor.frame_source,
        "last_seen_at": event["occurred_at"],
        "last_seen_camera_id": event["camera_id"],
        "last_seen_room": evidence.get("room_name") or event.get("camera_name") or event["camera_id"],
        "role_assignment": role_assignment,
        "assignment_source": assignment_source,
        "assigned_by": None,
        "assigned_at": None,
        "attributes": attributes,
    }
    observation_record = {
        "profile_observation_id": f"appearance_obs_{uuid4().hex}",
        "appearance_profile_id": profile_id,
        "observed_at": event["occurred_at"],
        "camera_id": event["camera_id"],
        "room": profile["last_seen_room"],
        "track_id": track_id,
        "source_event_id": event_id,
        "source_observation_id": observation["observation_id"],
        "snapshot_path": snapshot_path,
        "frame_source": descriptor.frame_source,
        "descriptor_source": descriptor.descriptor_source,
        "created_from": descriptor.descriptor_source,
        "descriptor_status": descriptor.descriptor_status,
        "confidence": max(attribute["confidence"] for attribute in attributes.values()),
        "attributes": attributes,
    }
    store.upsert_appearance_profile(profile)
    store.insert_appearance_profile_observation(observation_record)
    stored = store.get_appearance_profile(profile_id)
    return {
        "schema": "appearance-profile-derivation",
        "source_of_truth": "sqlite",
        "event_id": event_id,
        "observation_id": observation["observation_id"],
        "track_id": track_id,
        "snapshot_path": snapshot_path,
        "descriptor_status": descriptor.descriptor_status,
        "descriptor_source": descriptor.descriptor_source,
        "profile": stored,
        "summary": render_appearance_summary(_profile_for_render(stored)),
        "observation": observation_record,
        "safety_boundaries": [
            "non_biometric_daily_appearance_only",
            "same_day_only",
            "no_named_person_identity",
            "no_face_recognition",
            "no_cross_day_identity",
        ],
    }


def _profile_for_render(profile: dict):
    from caresight.runtime.appearance import AppearanceProfile

    attributes = profile.get("attributes", {})
    return AppearanceProfile(
        appearance_profile_id=profile["appearance_profile_id"],
        active_date=profile["active_date"],
        expires_at=profile["expires_at"],
        role_assignment=profile["role_assignment"],
        assignment_source=profile["assignment_source"],
        track_id=None,
        upper_body_color=attributes.get("upper_body_color", {}).get("value", "unknown"),
        lower_body_color=attributes.get("lower_body_color", {}).get("value", "unknown"),
        headwear=attributes.get("headwear", {}).get("value", "unknown"),
        footwear=attributes.get("footwear", {}).get("value", "unknown"),
        last_seen_camera_id=profile.get("last_seen_camera_id") or "",
        last_seen_room=profile.get("last_seen_room") or "",
        last_seen_at=profile.get("last_seen_at") or "",
        last_seen_event_id=profile.get("source_event_id"),
    )


def _resolve_snapshot_path(snapshot_path: str | None) -> str | None:
    if not snapshot_path:
        return None
    path = Path(snapshot_path)
    if path.is_absolute():
        return str(path)
    return str(ROOT_DIR.parents[1] / path)


def _parse_bbox(value: str) -> tuple[float, float, float, float]:
    parts = value.split(",")
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("bbox must be x1,y1,x2,y2")
    try:
        x1, y1, x2, y2 = (float(part.strip()) for part in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("bbox values must be numbers") from exc
    return x1, y1, x2, y2


def _parse_datetime(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _appearance_profile_id(active_date: str, source: str) -> str:
    suffix = "".join(ch if ch.isalnum() else "_" for ch in source.lower()).strip("_")
    return f"appearance_{active_date.replace('-', '_')}_{suffix[:32]}"


if __name__ == "__main__":
    main()
