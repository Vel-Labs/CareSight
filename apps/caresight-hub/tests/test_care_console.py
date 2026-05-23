import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from caresight.events.floor_stay import FloorStayDetector
from caresight.runtime.alerts import draft_caregiver_alert
from caresight.runtime.config import CareSightConfig
from caresight.runtime.dashboard import build_dashboard_state
from caresight.runtime.review import ReviewService
from caresight.storage.sqlite_store import SQLiteStore
from caresight.vision.detections import Detection

ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT = ROOT_DIR / "scripts" / "care_console.py"
CONTACTS_SCRIPT = ROOT_DIR / "scripts" / "caresight_contacts_config.py"
PREFLIGHT_SCRIPT = ROOT_DIR / "scripts" / "caresight_demo_preflight.py"
preflight_spec = importlib.util.spec_from_file_location("caresight_demo_preflight", PREFLIGHT_SCRIPT)
assert preflight_spec is not None
preflight_module = importlib.util.module_from_spec(preflight_spec)
assert preflight_spec.loader is not None
preflight_spec.loader.exec_module(preflight_module)


class CareConsoleTest(unittest.TestCase):
    def test_dashboard_state_reads_sqlite_without_becoming_truth(self) -> None:
        with seeded_review_service() as seed:
            state = build_dashboard_state(seed.service)

            self.assertEqual(state["source_of_truth"], "sqlite")
            self.assertEqual(state["current_state"]["awaiting_review"], 1)
            self.assertEqual(state["timeline"][0]["event_id"], seed.event_id)
            self.assertEqual(state["review_controls"]["confirm"], "ReviewService.confirm_event")
            self.assertEqual(state["review_controls"]["delete"], "forbidden")
            self.assertEqual(state["live_feed"]["raw_video_stays_local"], True)

    def test_alert_draft_includes_provenance_and_forbidden_boundaries(self) -> None:
        with seeded_review_service() as seed:
            alert = draft_caregiver_alert(seed.service.get_audit_chain(seed.event_id))

            self.assertEqual(alert["event_id"], seed.event_id)
            self.assertEqual(alert["purpose"], "caregiver_alert_draft")
            self.assertEqual(alert["channel_sequence"], ["text", "facetime"])
            self.assertIn("sqlite_audit_chain", alert["provenance"]["source"])
            self.assertIn("event.event_id", alert["provenance"]["source_fields"])
            self.assertIn("no_autonomous_dispatch", alert["boundaries"])

    def test_dashboard_cli_outputs_json_read_model(self) -> None:
        with seeded_review_service() as seed:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--db", str(seed.db_path), "dashboard"],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["source_of_truth"], "sqlite")
            self.assertEqual(payload["current_state"]["current_event_id"], seed.event_id)
            self.assertTrue(payload["view"]["focused_event_found"])

    def test_dashboard_cli_can_focus_one_event(self) -> None:
        with seeded_review_service() as seed:
            seed.service.confirm_event(
                seed.event_id,
                reviewer="Steven",
                note="Confirmed for focused dashboard demo.",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "dashboard",
                    "--event-id",
                    seed.event_id,
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["current_state"]["current_event_id"], seed.event_id)
            self.assertEqual(payload["view"]["requested_event_id"], seed.event_id)
            self.assertEqual(payload["view"]["mode"], "focused_event")
            self.assertTrue(payload["view"]["focused_event_found"])
            self.assertEqual(payload["focused_event"]["event_id"], seed.event_id)
            self.assertEqual(payload["awaiting_review_backlog"]["count"], 0)
            self.assertEqual(len(payload["journal_preview"]), 1)
            self.assertEqual(payload["caregiver_alert_draft"]["event_id"], seed.event_id)

    def test_dashboard_focus_separates_awaiting_review_backlog(self) -> None:
        with seeded_review_service() as seed:
            seed.service.confirm_event(seed.event_id, reviewer="Steven")
            backlog_event_id = seed.insert_backlog_event()

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "dashboard",
                    "--event-id",
                    seed.event_id,
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["focused_event"]["event_id"], seed.event_id)
            self.assertEqual(payload["awaiting_review_backlog"]["count"], 1)
            self.assertEqual(payload["awaiting_review_backlog"]["events"][0]["event_id"], backlog_event_id)
            self.assertEqual(payload["awaiting_review_backlog"]["events"][0]["status"], "awaiting_human_confirmation")

    def test_alert_cli_outputs_provenance(self) -> None:
        with seeded_review_service() as seed:
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "alert-draft",
                    seed.event_id,
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["event_id"], seed.event_id)
            self.assertEqual(payload["provenance"]["source"], "sqlite_audit_chain")

    def test_review_packet_cli_outputs_read_only_packet(self) -> None:
        with seeded_review_service() as seed:
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "review-packet",
                    seed.event_id,
                    "--format",
                    "json",
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["schema"], "human-review-packet")
            self.assertEqual(payload["event_id"], seed.event_id)
            self.assertEqual(payload["source_of_truth"], "sqlite")
            self.assertEqual(payload["provenance"]["source"], "sqlite_audit_chain")

    def test_blackbox_receipt_cli_outputs_complete_receipt_after_review(self) -> None:
        with seeded_review_service() as seed:
            seed.service.confirm_event(seed.event_id, reviewer="Steven")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "blackbox-receipt",
                    seed.event_id,
                    "--format",
                    "json",
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["schema"], "blackbox-receipt")
            self.assertEqual(payload["completion_status"], "complete")
            self.assertEqual(payload["event_id"], seed.event_id)
            self.assertTrue(payload["derived_outputs"]["dashboard_includes_event"])

    def test_review_packet_cli_can_write_markdown(self) -> None:
        with seeded_review_service() as seed:
            output = Path(seed.tmpdir.name) / "packet.md"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "review-packet",
                    seed.event_id,
                    "--format",
                    "markdown",
                    "--output",
                    str(output),
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertIn("Human Review Packet", output.read_text(encoding="utf-8"))

    def test_agent_draft_cli_persists_fake_provider_draft(self) -> None:
        with seeded_review_service() as seed:
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "agent-draft",
                    seed.event_id,
                    "--purpose",
                    "caregiver_summary",
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["schema"], "agent-draft")
            self.assertEqual(payload["provider"], "fake")
            self.assertEqual(payload["validation_status"], "validated")
            self.assertEqual(len(seed.store.list_agent_drafts(seed.event_id)), 1)

    def test_action_request_cli_stages_without_execution(self) -> None:
        with seeded_review_service() as seed:
            draft_result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "agent-draft",
                    seed.event_id,
                ],
                capture_output=True,
                check=False,
                text=True,
            )
            self.assertEqual(draft_result.returncode, 0, draft_result.stderr)
            draft = json.loads(draft_result.stdout)

            stage_result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "stage-action-request",
                    seed.event_id,
                    "--draft-id",
                    draft["draft_id"],
                    "--action",
                    "create_apple_note",
                    "--destination",
                    "apple_notes",
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(stage_result.returncode, 0, stage_result.stderr)
            request = json.loads(stage_result.stdout)
            self.assertEqual(request["stage"], "staged")
            self.assertEqual(request["execution_state"], "not_executed")
            self.assertTrue(request["requires_human_approval"])
            self.assertEqual(request["escalation_level"], "attention")

            list_result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "list-action-requests",
                    seed.event_id,
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(list_result.returncode, 0, list_result.stderr)
            staged = json.loads(list_result.stdout)
            self.assertEqual(staged[0]["request_id"], request["request_id"])
            self.assertEqual(staged[0]["execution_state"], "not_executed")

    def test_action_request_cli_blocks_unconfigured_contact_id(self) -> None:
        with seeded_review_service() as seed:
            draft_result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "agent-draft",
                    seed.event_id,
                ],
                capture_output=True,
                check=False,
                text=True,
            )
            self.assertEqual(draft_result.returncode, 0, draft_result.stderr)
            draft = json.loads(draft_result.stdout)

            stage_result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "stage-action-request",
                    seed.event_id,
                    "--draft-id",
                    draft["draft_id"],
                    "--action",
                    "send_imessage_draft",
                    "--destination",
                    "imessage",
                    "--recipient-role",
                    "emergency_contact",
                    "--allowed-contact-id",
                    "contact_not_allowlisted",
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertNotEqual(stage_result.returncode, 0)
            self.assertIn("not allowlisted", stage_result.stderr)

    def test_agent_harness_plan_cli_is_non_executing(self) -> None:
        with seeded_review_service() as seed:
            draft = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "agent-draft",
                    seed.event_id,
                ],
                capture_output=True,
                check=False,
                text=True,
            )
            self.assertEqual(draft.returncode, 0, draft.stderr)
            draft_payload = json.loads(draft.stdout)
            staged = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "stage-action-request",
                    seed.event_id,
                    "--draft-id",
                    draft_payload["draft_id"],
                    "--action",
                    "send_imessage_draft",
                    "--destination",
                    "imessage",
                    "--escalation-level",
                    "urgent_handoff",
                    "--recipient-role",
                    "emergency_contact",
                    "--allowed-contact-id",
                    "contact_emergency_primary",
                    "--response-option",
                    "request_local_screen_capture",
                    "--response-option",
                    "request_facetime_handoff",
                ],
                capture_output=True,
                check=False,
                text=True,
            )
            self.assertEqual(staged.returncode, 0, staged.stderr)
            request = json.loads(staged.stdout)
            planned = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "agent-harness-plan",
                    request["request_id"],
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(planned.returncode, 0, planned.stderr)
            plan = json.loads(planned.stdout)
            self.assertEqual(plan["selected_harness"], "hermes")
            self.assertEqual(plan["execution_state"], "plan_only")
            self.assertEqual(plan["external_execution"], "not_allowed_by_this_command")

            payload_result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "hermes-handoff-payload",
                    request["request_id"],
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(payload_result.returncode, 0, payload_result.stderr)
            payload = json.loads(payload_result.stdout)
            self.assertEqual(payload["execution_state"], "payload_only")
            self.assertEqual(payload["recipient_role"], "emergency_contact")
            self.assertIn("screen capture", payload["message_text"])
            self.assertIn("FaceTime handoff", payload["message_text"])

            attempt_result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "record-execution-attempt",
                    request["request_id"],
                    "--harness",
                    "hermes",
                    "--kind",
                    "dry_run",
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(attempt_result.returncode, 0, attempt_result.stderr)
            attempt = json.loads(attempt_result.stdout)
            self.assertEqual(attempt["schema"], "agent-execution-attempt")
            self.assertEqual(attempt["execution_state"], "dry_run")
            self.assertEqual(attempt["result"], "payload_logged_no_send")
            self.assertFalse(attempt["external_action_performed"])

            hermes_result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "hermes-dry-run",
                    request["request_id"],
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(hermes_result.returncode, 0, hermes_result.stderr)
            hermes_attempt = json.loads(hermes_result.stdout)
            self.assertIn(hermes_attempt["execution_state"], {"dry_run", "blocked"})
            self.assertFalse(hermes_attempt["external_action_performed"])
            self.assertIn("hermes_preflight", hermes_attempt["payload"])
            self.assertNotIn("targets", hermes_attempt["payload"]["hermes_preflight"])

            listed_result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "list-execution-attempts",
                    request["request_id"],
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(listed_result.returncode, 0, listed_result.stderr)
            attempts = json.loads(listed_result.stdout)
            self.assertEqual(attempts[0]["attempt_id"], attempt["attempt_id"])

    def test_hermes_config_plan_cli_reports_local_model_route(self) -> None:
        with seeded_review_service() as seed:
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "hermes-config-plan",
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["schema"], "hermes-config-plan")
            self.assertEqual(payload["harness"], "hermes")
            self.assertFalse(payload["local_model_serving"]["openrouter_required"])
            self.assertEqual(payload["local_model_serving"]["base_url"], "http://127.0.0.1:8080/v1")

    def test_escalation_receipt_links_event_requests_and_attempts(self) -> None:
        with seeded_review_service() as seed:
            draft_result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "agent-draft",
                    seed.event_id,
                ],
                capture_output=True,
                check=False,
                text=True,
            )
            self.assertEqual(draft_result.returncode, 0, draft_result.stderr)
            draft = json.loads(draft_result.stdout)
            staged_result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "stage-action-request",
                    seed.event_id,
                    "--draft-id",
                    draft["draft_id"],
                    "--action",
                    "send_imessage_draft",
                    "--destination",
                    "imessage",
                    "--recipient-role",
                    "emergency_contact",
                    "--allowed-contact-id",
                    "contact_emergency_primary",
                ],
                capture_output=True,
                check=False,
                text=True,
            )
            self.assertEqual(staged_result.returncode, 0, staged_result.stderr)
            request = json.loads(staged_result.stdout)
            attempt_result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "record-execution-attempt",
                    request["request_id"],
                ],
                capture_output=True,
                check=False,
                text=True,
            )
            self.assertEqual(attempt_result.returncode, 0, attempt_result.stderr)

            receipt_result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "escalation-receipt",
                    seed.event_id,
                    "--format",
                    "json",
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(receipt_result.returncode, 0, receipt_result.stderr)
            receipt = json.loads(receipt_result.stdout)
            self.assertEqual(receipt["schema"], "care-escalation-receipt")
            self.assertEqual(receipt["event_id"], seed.event_id)
            self.assertEqual(receipt["escalation_counts"]["action_requests"], 1)
            self.assertEqual(receipt["escalation_counts"]["execution_attempts"], 1)
            self.assertEqual(receipt["execution_attempts"][0]["result"], "payload_logged_no_send")

    def test_appearance_profile_cli_derives_from_event_snapshot_and_lists_profile(self) -> None:
        with seeded_review_service() as seed:
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "appearance-profile",
                    "derive-from-event",
                    seed.event_id,
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["schema"], "appearance-profile-derivation")
            self.assertEqual(payload["descriptor_source"], "runtime_observation")
            self.assertEqual(payload["descriptor_status"], "posture_limited")
            self.assertEqual(payload["profile"]["descriptor_source"], "runtime_observation")
            self.assertEqual(payload["profile"]["source_event_id"], seed.event_id)
            self.assertEqual(payload["profile"]["attributes"]["upper_body_color"]["value"], "blue")
            self.assertEqual(payload["profile"]["attributes"]["lower_body_color"]["value"], "cream")
            self.assertNotIn("identity", payload["summary"].casefold())

            shown = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "appearance-profile",
                    "show",
                    payload["profile"]["appearance_profile_id"],
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(shown.returncode, 0, shown.stderr)
            profile = json.loads(shown.stdout)
            self.assertEqual(profile["appearance_profile_id"], payload["profile"]["appearance_profile_id"])
            self.assertEqual(profile["observations"][0]["source_event_id"], seed.event_id)

    def test_appearance_profile_cli_describes_still_image_without_writing_profile(self) -> None:
        with seeded_review_service() as seed:
            image_path = Path(seed.tmpdir.name) / "still-accessories.ppm"
            annotation_path = Path(seed.tmpdir.name) / "still-accessories.annotated.png"
            write_ppm(
                image_path,
                width=100,
                height=100,
                fills=[
                    ((42, 22, 58, 31), (20, 20, 20)),
                    ((38, 47, 62, 63), (42, 96, 180)),
                    ((38, 63, 62, 83), (245, 248, 248)),
                    ((42, 84, 58, 89), (245, 248, 248)),
                ],
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "appearance-profile",
                    "describe-image",
                    str(image_path),
                    "--bbox",
                    "20,20,80,90",
                    "--visual-output",
                    str(annotation_path),
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["schema"], "appearance-profile-still-image-descriptor")
            self.assertEqual(payload["source_of_truth"], "still_image")
            self.assertEqual(payload["descriptor_status"], "available")
            self.assertEqual(payload["attributes"]["upper_body_color"]["value"], "blue")
            self.assertEqual(payload["attributes"]["lower_body_color"]["value"], "white")
            self.assertEqual(payload["attributes"]["headwear"]["value"], "black")
            self.assertEqual(payload["attributes"]["footwear"]["value"], "white")
            self.assertEqual(payload["visual_evidence"]["annotated_image_path"], str(annotation_path))
            self.assertTrue(annotation_path.exists())
            self.assertEqual(seed.store.list_active_appearance_profiles(active_date="2026-05-22"), [])

    def test_appearance_profile_cli_summarizes_daily_sample_support(self) -> None:
        with seeded_review_service() as seed:
            profile = {
                "appearance_profile_id": "appearance_2026_05_22_track_1",
                "active_date": "2026-05-22",
                "created_at": "2026-05-22T14:00:00Z",
                "updated_at": "2026-05-22T14:00:00Z",
                "expires_at": "2026-05-23T04:00:00Z",
                "descriptor_source": "runtime_observation",
                "descriptor_status": "available",
                "last_seen_at": "2026-05-22T14:00:00Z",
                "last_seen_camera_id": "living_room",
                "last_seen_room": "Living Room",
                "attributes": {
                    "upper_body_color": {"value": "blue", "confidence": 0.78},
                    "lower_body_color": {"value": "white", "confidence": 0.78},
                    "headwear": {"value": "black", "confidence": 0.62},
                    "footwear": {"value": "white", "confidence": 0.78},
                },
            }
            seed.store.upsert_appearance_profile(profile)
            for sample_id, upper, lower, headwear, footwear, quality in [
                ("sample_1", "blue", "white", "black", "white", 0.82),
                ("sample_2", "blue", "white", "black", "white", 0.76),
                ("sample_3", "gray", "unknown", "unknown", "unknown", 0.68),
            ]:
                seed.store.insert_appearance_profile_sample(
                    {
                        "sample_id": sample_id,
                        "appearance_profile_id": profile["appearance_profile_id"],
                        "active_date": "2026-05-22",
                        "captured_at": "2026-05-22T14:00:00Z",
                        "camera_id": "living_room",
                        "room": "Living Room",
                        "track_id": "track_1",
                        "snapshot_path": str(seed.snapshot_path),
                        "frame_source": "periodic_live_sample",
                        "descriptor_status": "available",
                        "quality_score": quality,
                        "quality_reasons": ["accepted"],
                        "detection_confidence": 0.9,
                        "bbox_xyxy": [10, 10, 50, 70],
                        "attributes": {
                            "upper_body_color": {"value": upper, "confidence": 0.78},
                            "lower_body_color": {"value": lower, "confidence": 0.78 if lower != "unknown" else 0.0},
                            "headwear": {"value": headwear, "confidence": 0.62 if headwear != "unknown" else 0.0},
                            "footwear": {"value": footwear, "confidence": 0.78 if footwear != "unknown" else 0.0},
                        },
                        "created_at": "2026-05-22T14:00:00Z",
                    }
                )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "appearance-profile",
                    "summarize-today",
                    "--active-date",
                    "2026-05-22",
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            summary = payload["profiles"]["appearance_2026_05_22_track_1"]
            self.assertEqual(summary["upper_body_color"]["value"], "blue")
            self.assertEqual(summary["upper_body_color"]["support_ratio"], 0.667)
            self.assertEqual(summary["lower_body_color"]["value"], "white")
            self.assertEqual(summary["headwear"]["value"], "black")
            self.assertEqual(summary["footwear"]["value"], "white")
            self.assertIn("no_named_person_identity", summary["safety_boundaries"])

    def test_dashboard_includes_bounded_appearance_context_after_derivation(self) -> None:
        with seeded_review_service() as seed:
            derive = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "appearance-profile",
                    "derive-from-event",
                    seed.event_id,
                    "--role",
                    "resident_primary",
                ],
                capture_output=True,
                check=False,
                text=True,
            )
            self.assertEqual(derive.returncode, 0, derive.stderr)

            state = build_dashboard_state(seed.service, event_id=seed.event_id)

            context = state["appearance_context"]
            self.assertEqual(context["identity_boundary"], "non_biometric_daily_appearance_only")
            self.assertEqual(context["descriptor_source"], "runtime_observation")
            self.assertIn("resident-assigned profile for today", context["summary"])
            self.assertIn("face_recognition", context["forbidden_claims"])
            forbidden = ["this is", "face match", "biometric identity", "resident identity verified"]
            for phrase in forbidden:
                self.assertNotIn(phrase, json.dumps(context).casefold())

    def test_contacts_config_writes_ignored_local_allowlist_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "allowlisted-contacts.local.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(CONTACTS_SCRIPT),
                    "--output",
                    str(output),
                    "--imessage",
                    "+15555550123",
                    "--display-label",
                    "Demo contact",
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema"], "care-contact-allowlist")
            self.assertEqual(payload["contacts"][0]["contact_id"], "contact_emergency_primary")
            self.assertEqual(payload["contacts"][0]["channel_refs"]["facetime"], "+15555550123")

    def test_preflight_reads_local_demo_env_exports(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / "live-demo.local"
            env_path.write_text(
                'export OBS_WEBSOCKET_PASSWORD="local-secret"\n'
                "export CARESIGHT_OBS_BROWSER_FEED_URL='http://127.0.0.1:8766/live.html'\n",
                encoding="utf-8",
            )

            values = preflight_module.read_local_env(env_path)

            self.assertEqual(values["OBS_WEBSOCKET_PASSWORD"], "local-secret")
            self.assertEqual(values["CARESIGHT_OBS_BROWSER_FEED_URL"], "http://127.0.0.1:8766/live.html")

    def test_preflight_model_check_names_actual_model(self) -> None:
        model_path = preflight_module.REPO_ROOT / "apps" / "caresight-hub" / "models" / "reasoning" / "gemma" / "gemma-4-e2b-it-4bit"

        check = preflight_module.model_file_check(
            "gemma_model",
            model_path,
            model_id="gemma-4-e2b-it-4bit",
            required=True,
        )

        self.assertEqual(check["model"], "gemma-4-e2b-it-4bit")
        self.assertEqual(
            check["display_path"],
            "apps/caresight-hub/models/reasoning/gemma/gemma-4-e2b-it-4bit",
        )
        self.assertIn("gemma-4-e2b-it-4bit", check["detail"])
        self.assertNotIn(str(preflight_module.REPO_ROOT), check["detail"])


class Seed:
    def __init__(self, tmpdir: tempfile.TemporaryDirectory[str]):
        self.tmpdir = tmpdir
        self.db_path = Path(tmpdir.name) / "caresight.sqlite3"
        self.config = CareSightConfig.default()
        self.store = SQLiteStore(self.db_path)
        self.store.initialize()
        self.store.upsert_config(self.config)
        detector = FloorStayDetector(self.config)
        detection = Detection(
            class_name="person",
            confidence=0.91,
            bbox_xyxy=(200, 430, 1080, 715),
            frame_width=1280,
            frame_height=720,
        )
        detector.update([detection], now=100.0)
        event = detector.update([detection], now=109.0)
        assert event is not None
        self.snapshot_path = Path(tmpdir.name) / "event-snapshot.ppm"
        write_ppm(
            self.snapshot_path,
            width=1280,
            height=720,
            fills=[
                ((200, 430, 1080, 715), (80, 80, 80)),
                ((270, 504, 508, 652), (220, 210, 190)),
                ((622, 444, 922, 550), (42, 96, 180)),
            ],
        )
        event["evidence"]["snapshot_path"] = str(self.snapshot_path)
        event["evidence"]["room_name"] = "Living Room"
        self.event_id = event["event_id"]
        self.store.insert_event(event)
        self.service = ReviewService(self.store)

    def __enter__(self) -> "Seed":
        return self

    def __exit__(self, *_args: object) -> None:
        self.tmpdir.cleanup()

    def insert_backlog_event(self) -> str:
        detector = FloorStayDetector(self.config)
        detection = Detection(
            class_name="person",
            confidence=0.91,
            bbox_xyxy=(200, 430, 1080, 715),
            frame_width=1280,
            frame_height=720,
        )
        detector.update([detection], now=200.0)
        event = detector.update([detection], now=209.0)
        assert event is not None
        event["event_id"] = "evt_awaiting_backlog_demo"
        event["occurred_at"] = "2026-05-20T14:01:09Z"
        event["evidence"]["track_id"] = "track_backlog"
        self.store.insert_event(event)
        return event["event_id"]


def seeded_review_service() -> Seed:
    return Seed(tempfile.TemporaryDirectory())


def write_ppm(
    path: Path,
    width: int,
    height: int,
    fills: list[tuple[tuple[int, int, int, int], tuple[int, int, int]]],
) -> None:
    pixels = [[(255, 255, 255) for _ in range(width)] for _ in range(height)]
    for (x1, y1, x2, y2), color in fills:
        for y in range(y1, y2):
            for x in range(x1, x2):
                pixels[y][x] = color
    data = bytearray(f"P6\n{width} {height}\n255\n".encode("ascii"))
    for row in pixels:
        for red, green, blue in row:
            data.extend(bytes((red, green, blue)))
    path.write_bytes(data)


if __name__ == "__main__":
    unittest.main()
