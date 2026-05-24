import tempfile
import threading
import unittest
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from caresight.events.floor_stay import FloorStayDetector
from caresight.runtime.agent_assist import (
    build_agent_draft,
    build_execution_attempt,
    build_harness_plan,
    build_hermes_config_plan,
    build_hermes_handoff_payload,
    GemmaLocalProvider,
    execute_facetime_if_yes,
    execute_live_imessage,
    is_yes_like_reply,
    wait_for_yes_reply,
    run_hermes_dry_run,
    stage_action_request,
    validate_draft_text,
)
from caresight.runtime.config import CareSightConfig
from caresight.runtime.agent_assist.live_handoff import (
    _imessage_command,
    send_imessage,
    switch_aitum_vertical_scene,
    switch_obs_to_facetime_scene,
)
from caresight.storage.sqlite_store import SQLiteStore
from caresight.vision.detections import Detection


class AgentAssistTest(unittest.TestCase):
    def test_fake_provider_persists_validated_draft_to_sqlite(self) -> None:
        with seeded_store() as seed:
            draft = build_agent_draft(seed.store, seed.event_id)
            stored = seed.store.list_agent_drafts(seed.event_id)

            self.assertEqual(draft["provider"], "fake")
            self.assertEqual(draft["validation_status"], "validated")
            self.assertEqual(draft["blocked_claims"], [])
            self.assertIn("draft_only", draft["safety_boundaries"])
            self.assertEqual(stored[0]["draft_id"], draft["draft_id"])
            self.assertEqual(stored[0]["source_of_truth"], "sqlite")
            self.assertEqual(stored[0]["provenance"]["source"], "sqlite_audit_chain")

    def test_blocked_draft_is_persisted_with_reasons_and_safe_rewrite(self) -> None:
        with seeded_store() as seed:
            draft = build_agent_draft(
                seed.store,
                seed.event_id,
                override_text="CareSight called 911 because a fall detected diagnosis was made.",
            )
            stored = seed.store.list_agent_drafts(seed.event_id)[0]

            self.assertEqual(draft["validation_status"], "blocked")
            self.assertIn("autonomous_emergency_dispatch", draft["blocked_claims"])
            self.assertIn("vision_overcertainty", draft["blocked_claims"])
            self.assertIn("possible event", draft["safe_rewrite"])
            self.assertEqual(stored["validation_status"], "blocked")
            self.assertEqual(stored["blocked_claims"], draft["blocked_claims"])

    def test_forbidden_claim_vocabulary_blocks_sprint_02_claims(self) -> None:
        blocked = validate_draft_text(
            "This HIPAA compliant medical device confirmed medication and dispatched emergency services."
        )

        self.assertIn("hipaa_compliance", blocked)
        self.assertIn("medical_device", blocked)
        self.assertIn("medication_administration", blocked)
        self.assertIn("autonomous_emergency_dispatch", blocked)

    def test_action_request_staging_persists_without_execution(self) -> None:
        with seeded_store() as seed:
            draft = build_agent_draft(seed.store, seed.event_id)
            request = stage_action_request(
                seed.store,
                event_id=seed.event_id,
                source_draft_id=draft["draft_id"],
                requested_action="create_apple_note",
                destination="apple_notes",
            )
            stored = seed.store.list_agent_action_requests(seed.event_id)

            self.assertEqual(request["stage"], "staged")
            self.assertEqual(request["execution_state"], "not_executed")
            self.assertTrue(request["requires_human_approval"])
            self.assertIn("no_external_execution", request["safety_boundaries"])
            self.assertEqual(stored[0]["request_id"], request["request_id"])
            self.assertEqual(stored[0]["execution_state"], "not_executed")
            self.assertEqual(stored[0]["escalation_level"], "attention")

    def test_blocked_draft_cannot_stage_action_request(self) -> None:
        with seeded_store() as seed:
            draft = build_agent_draft(
                seed.store,
                seed.event_id,
                override_text="CareSight called 911 for a diagnosed fall detected event.",
            )

            with self.assertRaises(ValueError):
                stage_action_request(
                    seed.store,
                    event_id=seed.event_id,
                    source_draft_id=draft["draft_id"],
                    requested_action="send_caregiver_message",
                )

    def test_harness_plan_routes_imessage_to_hermes_without_execution(self) -> None:
        with seeded_store() as seed:
            draft = build_agent_draft(seed.store, seed.event_id)
            request = stage_action_request(
                seed.store,
                event_id=seed.event_id,
                source_draft_id=draft["draft_id"],
                requested_action="send_imessage_draft",
                destination="imessage",
                escalation_level="urgent_handoff",
                recipient_role="emergency_contact",
                allowed_contact_ids=["contact_emergency_primary"],
            )
            plan = build_harness_plan(request, draft=draft)

            self.assertEqual(plan["selected_harness"], "hermes")
            self.assertEqual(plan["execution_state"], "plan_only")
            self.assertEqual(plan["external_execution"], "not_allowed_by_this_command")
            self.assertEqual(plan["model_lane"]["provider"], "gemma_mlx")
            self.assertIn("no_raw_video_to_agent", plan["safety_boundaries"])
            self.assertIn("allowlisted_recipient_only", request["safety_boundaries"])

    def test_contact_allowlist_blocks_unknown_live_contact_destinations(self) -> None:
        with seeded_store() as seed:
            draft = build_agent_draft(seed.store, seed.event_id)

            with self.assertRaises(ValueError):
                stage_action_request(
                    seed.store,
                    event_id=seed.event_id,
                    source_draft_id=draft["draft_id"],
                    requested_action="send_imessage_draft",
                    destination="imessage",
                    recipient_role="emergency_contact",
                    allowed_contact_ids=["contact_not_allowlisted"],
                    contact_allowlist={"contact_emergency_primary"},
                )

            request = stage_action_request(
                seed.store,
                event_id=seed.event_id,
                source_draft_id=draft["draft_id"],
                requested_action="prepare_facetime_handoff",
                destination="facetime",
                recipient_role="emergency_contact",
                allowed_contact_ids=["contact_emergency_primary"],
                contact_allowlist={"contact_emergency_primary"},
            )

            self.assertEqual(request["allowed_contact_ids"], ["contact_emergency_primary"])
            self.assertIn("allowlisted_recipient_only", request["safety_boundaries"])

    def test_imessage_staging_requires_allowlisted_contact(self) -> None:
        with seeded_store() as seed:
            draft = build_agent_draft(seed.store, seed.event_id)

            with self.assertRaises(ValueError):
                stage_action_request(
                    seed.store,
                    event_id=seed.event_id,
                    source_draft_id=draft["draft_id"],
                    requested_action="send_imessage_draft",
                    destination="imessage",
                )

    def test_hermes_handoff_payload_offers_screen_capture_or_facetime_without_execution(self) -> None:
        with seeded_store() as seed:
            draft = build_agent_draft(seed.store, seed.event_id, purpose="alert_draft")
            request = stage_action_request(
                seed.store,
                event_id=seed.event_id,
                source_draft_id=draft["draft_id"],
                requested_action="send_imessage_draft",
                destination="imessage",
                escalation_level="urgent_handoff",
                recipient_role="emergency_contact",
                allowed_contact_ids=["contact_emergency_primary"],
                response_options=["request_local_screen_capture", "request_facetime_handoff"],
            )
            payload = build_hermes_handoff_payload(request, draft=draft)

            self.assertEqual(payload["execution_state"], "payload_only")
            self.assertEqual(payload["recipient_role"], "emergency_contact")
            self.assertIn("possible urgent event", payload["message_text"])
            self.assertIn("screen capture", payload["message_text"])
            self.assertIn("FaceTime handoff", payload["message_text"])
            self.assertEqual(payload["media_options"]["obs_virtual_camera"], "operator_configured_only")
            self.assertIn("no_raw_video_to_agent", payload["safety_boundaries"])

    def test_execution_attempt_logs_dry_run_without_external_execution(self) -> None:
        with seeded_store() as seed:
            draft = build_agent_draft(seed.store, seed.event_id, purpose="alert_draft")
            request = stage_action_request(
                seed.store,
                event_id=seed.event_id,
                source_draft_id=draft["draft_id"],
                requested_action="send_imessage_draft",
                destination="imessage",
                recipient_role="emergency_contact",
                allowed_contact_ids=["contact_emergency_primary"],
            )
            payload = build_hermes_handoff_payload(request, draft=draft)
            attempt = build_execution_attempt(
                seed.store,
                request=request,
                payload=payload,
                harness="hermes",
                attempt_kind="dry_run",
                result="payload_logged_no_send",
            )
            stored = seed.store.list_agent_execution_attempts(request["request_id"])

            self.assertEqual(attempt["schema"], "agent-execution-attempt")
            self.assertEqual(attempt["execution_state"], "dry_run")
            self.assertEqual(attempt["result"], "payload_logged_no_send")
            self.assertFalse(attempt["external_action_performed"])
            self.assertIn("no_external_execution", attempt["safety_boundaries"])
            self.assertEqual(stored[0]["attempt_id"], attempt["attempt_id"])
            self.assertEqual(stored[0]["payload"]["schema"], "hermes-handoff-payload")

    def test_hermes_dry_run_records_no_send_preflight_attempt(self) -> None:
        with seeded_store() as seed:
            draft = build_agent_draft(seed.store, seed.event_id, purpose="alert_draft")
            request = stage_action_request(
                seed.store,
                event_id=seed.event_id,
                source_draft_id=draft["draft_id"],
                requested_action="send_imessage_draft",
                destination="imessage",
                recipient_role="emergency_contact",
                allowed_contact_ids=["contact_emergency_primary"],
            )
            attempt = run_hermes_dry_run(seed.store, request=request, draft=draft)

            self.assertEqual(attempt["schema"], "agent-execution-attempt")
            self.assertIn(attempt["execution_state"], {"dry_run", "blocked"})
            self.assertFalse(attempt["external_action_performed"])
            self.assertIn("hermes_preflight", attempt["payload"])
            self.assertNotIn("targets", attempt["payload"]["hermes_preflight"])
            self.assertEqual(seed.store.list_agent_execution_attempts(request["request_id"])[0]["attempt_id"], attempt["attempt_id"])

    def test_live_imessage_dry_run_requires_staged_allowlisted_request_and_redacts_target(self) -> None:
        with seeded_store() as seed:
            draft = build_agent_draft(seed.store, seed.event_id, purpose="alert_draft")
            request = stage_action_request(
                seed.store,
                event_id=seed.event_id,
                source_draft_id=draft["draft_id"],
                requested_action="send_imessage_draft",
                destination="imessage",
                recipient_role="emergency_contact",
                allowed_contact_ids=["contact_emergency_primary"],
            )
            attempt = execute_live_imessage(
                seed.store,
                request_id=request["request_id"],
                message="CareSight alert. Possible floor stay observed. Would you like to connect to CareSight?",
                contact_id="contact_emergency_primary",
                allowlist_config="/does/not/need/to/exist.json",
                target="+15555550123",
                dry_run=True,
            )

            self.assertEqual(attempt["harness"], "local_macos_live_handoff")
            self.assertEqual(attempt["result"], "imessage_live_dry_run")
            self.assertFalse(attempt["external_action_performed"])
            self.assertEqual(attempt["payload"]["target"]["redacted"], True)
            self.assertNotIn("+15555550123", json.dumps(attempt))

    def test_live_imessage_dry_run_can_include_redacted_local_snapshot_attachment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, seeded_store() as seed:
            snapshot = Path(tmp) / "evt_snapshot.jpg"
            snapshot.write_bytes(b"fake image")
            draft = build_agent_draft(seed.store, seed.event_id, purpose="alert_draft")
            request = stage_action_request(
                seed.store,
                event_id=seed.event_id,
                source_draft_id=draft["draft_id"],
                requested_action="send_imessage_draft",
                destination="imessage",
                recipient_role="emergency_contact",
                allowed_contact_ids=["contact_emergency_primary"],
            )

            attempt = execute_live_imessage(
                seed.store,
                request_id=request["request_id"],
                message="This is CareSight Hub escalation. Please see the image attached.",
                contact_id="contact_emergency_primary",
                allowlist_config="/does/not/need/to/exist.json",
                target="+15555550123",
                attachment_path=snapshot,
                result_name="imessage_no_response_escalation_sent",
                dry_run=True,
            )

            delivery = attempt["payload"]["delivery"]
            self.assertEqual(attempt["result"], "imessage_no_response_escalation_sent")
            self.assertEqual(delivery["attachment"]["name"], "evt_snapshot.jpg")
            self.assertTrue(delivery["attachment"]["redacted"])
            self.assertNotIn(str(snapshot), json.dumps(attempt))

    def test_live_imessage_attachment_command_uses_alias_file_send(self) -> None:
        command = _imessage_command("+15555550123", "CareSight follow-up", Path("/tmp/evt_snapshot.jpg"))
        script = command[2]

        self.assertIn('activate', script)
        self.assertIn("POSIX file attachmentPath as alias", script)
        self.assertIn("send attachmentFile to targetBuddy", script)
        self.assertIn("delay 2", script)
        self.assertEqual(command[-1], "/tmp/evt_snapshot.jpg")

    def test_facetime_handoff_is_reply_gated(self) -> None:
        with seeded_store() as seed:
            draft = build_agent_draft(seed.store, seed.event_id, purpose="alert_draft")
            request = stage_action_request(
                seed.store,
                event_id=seed.event_id,
                source_draft_id=draft["draft_id"],
                requested_action="send_imessage_draft",
                destination="imessage",
                recipient_role="emergency_contact",
                allowed_contact_ids=["contact_emergency_primary"],
                response_options=["request_facetime_handoff"],
            )

            self.assertTrue(is_yes_like_reply("yes please connect"))
            self.assertFalse(is_yes_like_reply("no not now"))

            no_attempt = execute_facetime_if_yes(
                seed.store,
                request_id=request["request_id"],
                reply_text="no not now",
                contact_id="contact_emergency_primary",
                allowlist_config="/does/not/need/to/exist.json",
                target="+15555550123",
                live_approved=True,
            )
            yes_attempt = execute_facetime_if_yes(
                seed.store,
                request_id=request["request_id"],
                reply_text="yes please",
                contact_id="contact_emergency_primary",
                allowlist_config="/does/not/need/to/exist.json",
                target="+15555550123",
                live_approved=True,
                dry_run=True,
            )

            self.assertEqual(no_attempt["result"], "facetime_not_requested_reply_not_yes_like")
            self.assertFalse(no_attempt["external_action_performed"])
            self.assertEqual(yes_attempt["result"], "facetime_live_dry_run")
            self.assertTrue(yes_attempt["payload"]["delivery"]["reply_interpreted_as_yes"])

    def test_aitum_vertical_switch_falls_back_when_optional_plugin_missing(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        with patch.dict("os.environ", {"CARESIGHT_AITUM_VERTICAL_MODE": "auto"}, clear=False):
            with patch("subprocess.run") as run:
                run.return_value.returncode = 2
                run.return_value.stdout = ""
                run.return_value.stderr = "vendor not found"

                result = switch_aitum_vertical_scene(repo_root, "CareSight Hub - FaceTime Mobile")

            self.assertEqual(result["status"], "fallback")
            self.assertEqual(result["path"], "aitum_vertical")

    def test_aitum_vertical_switch_can_be_required_for_handoff(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        with patch.dict("os.environ", {"CARESIGHT_AITUM_VERTICAL_MODE": "required"}, clear=False):
            with patch("subprocess.run") as run:
                run.return_value.returncode = 2
                run.return_value.stdout = ""
                run.return_value.stderr = "vendor not found"

                result = switch_aitum_vertical_scene(repo_root, "CareSight Hub - FaceTime Mobile")

            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["path"], "aitum_vertical")

    def test_facetime_landscape_scene_does_not_force_portrait_output(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "CARESIGHT_AITUM_VERTICAL_MODE": "off",
                "CARESIGHT_OBS_FACETIME_SCENE": "CareSight Hub - Escalation",
            },
            clear=False,
        ):
            with patch("subprocess.run") as run:
                run.return_value.returncode = 0
                run.return_value.stdout = "ready"
                run.return_value.stderr = ""

                result = switch_obs_to_facetime_scene()

            self.assertEqual(result["status"], "scene_requested")
            self.assertEqual(result["scene"], "CareSight Hub - Escalation")
            self.assertEqual(result["video_mode"], "landscape")
            self.assertIn("--video-mode", run.call_args.args[0])
            self.assertIn("landscape", run.call_args.args[0])

    def test_facetime_default_preserves_operator_selected_obs_scene(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "CARESIGHT_AITUM_VERTICAL_MODE": "off",
            },
            clear=False,
        ):
            os.environ.pop("CARESIGHT_OBS_FACETIME_SCENE", None)
            os.environ.pop("CARESIGHT_OBS_FACETIME_VIDEO_MODE", None)
            with patch("subprocess.run") as run:
                run.return_value.returncode = 0
                run.return_value.stdout = "ready"
                run.return_value.stderr = ""

                result = switch_obs_to_facetime_scene()

            self.assertEqual(result["status"], "not_requested")
            run.assert_not_called()

    def test_imessage_auto_backend_uses_imsg_file_for_snapshot_attachment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            snapshot = Path(tmp) / "evt_snapshot.jpg"
            snapshot.write_bytes(b"fake image")
            with patch.dict("os.environ", {"CARESIGHT_IMESSAGE_BACKEND": "auto"}, clear=False):
                with patch("shutil.which", return_value="/opt/homebrew/bin/imsg"):
                    with patch("subprocess.run") as run:
                        run.return_value.returncode = 0
                        run.return_value.stdout = ""
                        run.return_value.stderr = ""

                        delivery = send_imessage("+15555550123", "CareSight follow-up", attachment_path=snapshot)

            command = run.call_args.args[0]
            self.assertEqual(delivery["platform"], "imsg")
            self.assertEqual(delivery["attachment"]["name"], "evt_snapshot.jpg")
            self.assertIn("--file", command)
            self.assertIn(str(snapshot), command)

    def test_reply_watch_times_out_without_messages_access_or_reply(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "messages.sqlite3"
            import sqlite3

            conn = sqlite3.connect(db_path)
            try:
                conn.executescript(
                    """
                    CREATE TABLE handle (ROWID INTEGER PRIMARY KEY, id TEXT);
                    CREATE TABLE message (
                      ROWID INTEGER PRIMARY KEY,
                      handle_id INTEGER,
                      text TEXT,
                      date INTEGER,
                      is_from_me INTEGER
                    );
                    """
                )
            finally:
                conn.close()

            result = wait_for_yes_reply(
                target="+15555550123",
                since_unix_seconds=1000.0,
                timeout_seconds=0.01,
                poll_interval_seconds=0.01,
                messages_db=db_path,
            )

            self.assertEqual(result["status"], "timeout")
            self.assertFalse(result["reply_interpreted_as_yes"])

    def test_harness_plan_routes_tts_to_holler_lane(self) -> None:
        with seeded_store() as seed:
            draft = build_agent_draft(seed.store, seed.event_id)
            request = stage_action_request(
                seed.store,
                event_id=seed.event_id,
                source_draft_id=draft["draft_id"],
                requested_action="play_tts_utterance",
                destination="local_tts",
            )
            plan = build_harness_plan(request, draft=draft, preferred_harness="openclaw")

            self.assertEqual(plan["selected_harness"], "openclaw")
            self.assertEqual(plan["model_lane"]["provider"], "holler_mlx")
            self.assertEqual(plan["model_lane"]["default_model"], "holler-0.6b-6bit")

    def test_hermes_config_plan_uses_local_endpoint_not_openrouter(self) -> None:
        plan = build_hermes_config_plan()

        self.assertEqual(plan["schema"], "hermes-config-plan")
        self.assertEqual(plan["vendor"]["pinned_tag"], "v2026.5.16")
        self.assertFalse(plan["vendor"]["global_install_performed"])
        self.assertEqual(plan["local_model_serving"]["default"], "local_openai_compatible_endpoint")
        self.assertEqual(plan["local_model_serving"]["base_url"], "http://127.0.0.1:8080/v1")
        self.assertFalse(plan["local_model_serving"]["openrouter_required"])
        self.assertIn("no_cloud_router_by_default", plan["safety_boundaries"])

    def test_gemma_provider_persists_validated_draft_without_raw_media(self) -> None:
        server = LocalGemmaServer("Please review a possible floor stay in the Living Room. Human review is in progress.")
        with server, seeded_store() as seed:
            draft = build_agent_draft(
                seed.store,
                seed.event_id,
                purpose="alert_draft",
                provider=GemmaLocalProvider(endpoint=server.base_url, model="local-test-model"),
            )

            self.assertEqual(draft["provider"], "gemma_mlx")
            self.assertTrue(draft["draft_id"].endswith("_gemma_mlx"))
            self.assertEqual(draft["validation_status"], "validated")
            self.assertEqual(draft["blocked_claims"], [])
            self.assertIn("possible floor stay", draft["draft_text"])
            self.assertNotIn("data/snapshots", server.last_request_text)
            self.assertIn("snapshot_path_present", server.last_request_text)


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
        self.event_id = event["event_id"]
        self.store.insert_event(event)

    def __enter__(self) -> "Seed":
        return self

    def __exit__(self, *_args: object) -> None:
        self.tmpdir.cleanup()


def seeded_store() -> Seed:
    return Seed(tempfile.TemporaryDirectory())


class LocalGemmaServer:
    def __init__(self, response_text: str):
        self.response_text = response_text
        self.last_request_text = ""
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), self._handler())
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self.base_url = f"http://127.0.0.1:{self._server.server_port}/v1"

    def __enter__(self) -> "LocalGemmaServer":
        self._thread.start()
        return self

    def __exit__(self, *_args: object) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2)

    def _handler(self):
        parent = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length", "0"))
                parent.last_request_text = self.rfile.read(length).decode("utf-8")
                body = json.dumps({"choices": [{"message": {"content": parent.response_text}}]}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, _format: str, *_args: object) -> None:
                return

        return Handler


if __name__ == "__main__":
    unittest.main()
