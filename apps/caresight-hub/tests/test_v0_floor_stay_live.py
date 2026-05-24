import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from caresight.runtime.config import CareSightConfig
from caresight.runtime.escalation import plan_escalation

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "v0_floor_stay_live.py"
spec = importlib.util.spec_from_file_location("v0_floor_stay_live", SCRIPT)
assert spec is not None
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class V0FloorStayLiveTest(unittest.TestCase):
    def test_help_does_not_require_live_runtime_imports(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True,
            check=False,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--stop-after-event", result.stdout)
        self.assertIn("--auto-agent-dry-run", result.stdout)
        self.assertIn("--auto-agent-live-run", result.stdout)
        self.assertIn("--live-approved", result.stdout)
        self.assertIn("--obs-live-preview", result.stdout)
        self.assertIn("--obs-browser-feed", result.stdout)
        self.assertIn("--allow-lan-preview", result.stdout)
        self.assertIn("--preview-token", result.stdout)
        self.assertIn("--ack-lan-preview-risk", result.stdout)
        self.assertIn("--appearance-overlay", result.stdout)
        self.assertIn("--missing-off-camera-events", result.stdout)
        self.assertIn("--auto-facetime-on-reply", result.stdout)
        self.assertIn("--no-response-escalation-seconds", result.stdout)
        self.assertIn("--play-tts-after-facetime", result.stdout)
        self.assertIn("--tts-audio-route", result.stdout)
        self.assertIn("--tts-volume", result.stdout)
        self.assertIn("--tts-after-facetime-delay-seconds", result.stdout)
        self.assertIn("--post-facetime-hold-seconds", result.stdout)
        self.assertIn("--max-seconds", result.stdout)
        self.assertIn("--camera-id", result.stdout)
        self.assertIn("--source-type", result.stdout)
        self.assertIn("--site-name", result.stdout)

    def test_stop_after_event_when_event_persisted(self) -> None:
        self.assertTrue(
            module.should_stop_loop(
                started_at=10.0,
                now=11.0,
                max_seconds=None,
                event_persisted=True,
                stop_after_event=True,
            )
        )

    def test_max_seconds_stops_loop(self) -> None:
        self.assertTrue(
            module.should_stop_loop(
                started_at=10.0,
                now=20.1,
                max_seconds=10.0,
                event_persisted=False,
                stop_after_event=False,
            )
        )

    def test_continues_when_no_stop_condition_is_met(self) -> None:
        self.assertFalse(
            module.should_stop_loop(
                started_at=10.0,
                now=11.0,
                max_seconds=10.0,
                event_persisted=False,
                stop_after_event=True,
            )
        )

    def test_started_line_labels_dwell_as_required_threshold(self) -> None:
        config = CareSightConfig.default()
        line = module.format_started_line(config, Path("/tmp/caresight.sqlite3"))

        self.assertIn("required_dwell_seconds=8.0", line)
        self.assertNotIn(" dwell_seconds=", line)

    def test_no_event_line_is_machine_readable_receipt(self) -> None:
        config = CareSightConfig.default()
        check = module.build_no_event_check(
            started_at="2026-05-21T18:00:00Z",
            completed_at="2026-05-21T18:01:00Z",
            elapsed_seconds=60.123,
            frame_count=42,
            config=config,
        )
        line = module.format_no_event_line(check)

        prefix, payload_text = line.split(" ", 1)
        payload = json.loads(payload_text)
        self.assertEqual(prefix, "no_event_persisted")
        self.assertTrue(payload["check_id"].startswith("check_"))
        self.assertEqual(payload["status"], "no_possible_floor_stay_event")
        self.assertEqual(payload["required_dwell_seconds"], 8.0)
        self.assertEqual(payload["frame_count"], 42)
        self.assertEqual(check["schema"], "observation-check")
        self.assertEqual(check["status"], "no_event_persisted")
        self.assertIsNone(check["event_id"])

    def test_relative_runtime_paths_resolve_to_repo_root(self) -> None:
        resolved = module.resolve_runtime_path("apps/caresight-hub/data/caresight-v0.sqlite3")

        self.assertEqual(resolved, module.REPO_ROOT / "apps/caresight-hub/data/caresight-v0.sqlite3")

    def test_missing_candidates_use_last_seen_cache(self) -> None:
        candidates = module.missing_candidates_from_last_seen(
            {
                "track_1": {
                    "bbox_xyxy": (10.0, 20.0, 110.0, 220.0),
                    "confidence": 0.82,
                    "first_seen_at": 100.0,
                    "frame_height": 720,
                    "frame_width": 1280,
                    "last_seen_at": 120.0,
                },
                "track_2": {
                    "bbox_xyxy": (200.0, 20.0, 300.0, 220.0),
                    "confidence": 0.9,
                    "first_seen_at": 101.0,
                    "frame_height": 720,
                    "frame_width": 1280,
                    "last_seen_at": 149.0,
                },
            },
            now=151.0,
            missing_seconds=30.0,
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].track_id, "track_1")
        self.assertEqual(candidates[0].missed_seconds, 31.0)
        self.assertEqual(candidates[0].detection.class_name, "person")

    def test_post_event_agent_receipt_line_is_machine_readable(self) -> None:
        line = module.format_post_event_agent_line(
            {
                "event_id": "evt_123",
                "draft_id": "draft_123",
                "request_id": "action_req_123",
                "attempt_id": "attempt_123",
                "execution_state": "dry_run",
                "external_action_performed": False,
                "obs_overlay_updated": True,
            }
        )

        prefix, payload_text = line.split(" ", 1)
        payload = json.loads(payload_text)
        self.assertEqual(prefix, "post_event_agent_dry_run")
        self.assertEqual(payload["event_id"], "evt_123")
        self.assertFalse(payload["external_action_performed"])

    def test_post_event_agent_live_receipt_line_is_machine_readable(self) -> None:
        line = module.format_post_event_agent_live_line(
            {
                "event_id": "evt_123",
                "request_id": "action_req_123",
                "live_attempt_id": "attempt_live_123",
                "external_action_performed": True,
                "facetime_started": False,
            }
        )

        prefix, payload_text = line.split(" ", 1)
        payload = json.loads(payload_text)
        self.assertEqual(prefix, "post_event_agent_live_run")
        self.assertEqual(payload["event_id"], "evt_123")
        self.assertTrue(payload["external_action_performed"])

    def test_post_event_agent_error_line_is_machine_readable(self) -> None:
        line = module.format_post_event_agent_error_line("evt_123", RuntimeError("no gemma"))

        prefix, payload_text = line.split(" ", 1)
        payload = json.loads(payload_text)
        self.assertEqual(prefix, "post_event_agent_dry_run_failed")
        self.assertEqual(payload["event_id"], "evt_123")
        self.assertEqual(payload["status"], "post_event_agent_dry_run_failed")
        self.assertFalse(payload["external_action_performed"])

    def test_obs_overlay_draw_filter_keeps_people_and_home_pets(self) -> None:
        self.assertTrue(module.should_draw_detection_label("person"))
        self.assertTrue(module.should_draw_detection_label("dog"))
        self.assertTrue(module.should_draw_detection_label("cat"))
        self.assertTrue(module.should_draw_detection_label("bird"))

    def test_obs_overlay_draw_filter_hides_furniture_and_household_objects(self) -> None:
        for label in ["chair", "couch", "tv", "bottle", "cup", "remote"]:
            self.assertFalse(module.should_draw_detection_label(label), label)

    def test_live_handoff_runs_only_for_approved_floor_stay_events(self) -> None:
        self.assertTrue(
            module.should_run_live_handoff(
                {
                    "event_type": "possible_floor_stay",
                    "status": "awaiting_human_confirmation",
                    "allowed_actions": ["journal_entry", "caregiver_alert", "facetime_handoff"],
                }
            )
        )
        self.assertFalse(
            module.should_run_live_handoff(
                {
                    "event_type": "missing_off_camera_extended",
                    "status": "awaiting_human_confirmation",
                    "allowed_actions": ["journal_entry", "caregiver_alert", "facetime_handoff"],
                }
            )
        )
        self.assertFalse(
            module.should_run_live_handoff(
                {
                    "event_type": "missing_off_camera_extended",
                    "status": "awaiting_human_confirmation",
                    "allowed_actions": ["journal_entry"],
                }
            )
        )

    def test_live_message_uses_floor_stay_context(self) -> None:
        message = module.live_message_for_event(
            {
                "event_type": "possible_floor_stay",
                "camera_id": "tapo_living_room",
                "evidence": {"room_name": "Living Room"},
            }
        )

        self.assertIn("possible floor-stay event", message)
        self.assertIn("Living Room", message)
        self.assertIn("not a medical or emergency claim", message)
        self.assertIn("yes connect", message)
        self.assertIn("yes FaceTime", message)

    def test_no_response_message_uses_explicit_facetime_approval_phrase(self) -> None:
        with patch.object(sys, "argv", [str(SCRIPT)]):
            parser = module.parse_args()

        self.assertIn("yes connect", parser.no_response_escalation_message)
        self.assertIn("yes FaceTime", parser.no_response_escalation_message)
        self.assertNotIn("reply yes to see a live feed", parser.no_response_escalation_message)

    def test_live_message_override_is_preserved(self) -> None:
        self.assertEqual(
            module.live_message_for_event({"event_type": "missing_off_camera_extended"}, "Approved operator text."),
            "Approved operator text.",
        )

    def test_default_config_resolution_falls_back_to_tracked_example(self) -> None:
        self.assertEqual(module.resolve_default_config_path().name, "v0.example.json")

    def test_escalation_orchestrator_selects_floor_stay_methods(self) -> None:
        plan = plan_escalation(
            {
                "event_id": "evt_floor",
                "event_type": "possible_floor_stay",
                "severity": "high",
                "status": "awaiting_human_confirmation",
            }
        )

        self.assertEqual(plan.escalation_level, "urgent_handoff")
        self.assertIn("no_send_agent_dry_run", [method.method_id for method in plan.methods])
        self.assertIn("obs_overlay_update", [method.method_id for method in plan.methods])

    def test_missing_off_camera_can_be_review_only(self) -> None:
        plan = plan_escalation(
            {
                "event_id": "evt_missing",
                "event_type": "missing_off_camera_extended",
                "severity": "medium",
                "status": "awaiting_human_confirmation",
            },
            missing_off_camera_review_only=True,
        )

        self.assertEqual(plan.escalation_level, "review_only")
        self.assertEqual([method.method_id for method in plan.methods], ["review_only"])

    def test_default_loopback_preview_exposure_is_allowed(self) -> None:
        receipt = module.validate_preview_exposure(
            host="127.0.0.1",
            allow_lan=False,
            token=None,
            acknowledged=False,
        )

        self.assertEqual(receipt["schema"], "local-feed-exposure")
        self.assertEqual(receipt["bind_scope"], "loopback")
        self.assertFalse(receipt["auth_required"])

    def test_lan_preview_bind_is_blocked_without_override(self) -> None:
        with self.assertRaises(SystemExit):
            module.validate_preview_exposure(
                host="0.0.0.0",
                allow_lan=False,
                token=None,
                acknowledged=False,
            )

    def test_lan_preview_override_requires_token(self) -> None:
        with self.assertRaises(SystemExit):
            module.validate_preview_exposure(
                host="0.0.0.0",
                allow_lan=True,
                token=None,
                acknowledged=True,
            )

    def test_lan_preview_override_requires_privacy_acknowledgement(self) -> None:
        with self.assertRaises(SystemExit):
            module.validate_preview_exposure(
                host="0.0.0.0",
                allow_lan=True,
                token="test-token",
                acknowledged=False,
            )

    def test_lan_preview_with_token_emits_exposure_receipt(self) -> None:
        receipt = module.validate_preview_exposure(
            host="0.0.0.0",
            allow_lan=True,
            token="test-token",
            acknowledged=True,
        )

        self.assertEqual(receipt["bind_scope"], "lan")
        self.assertTrue(receipt["auth_required"])
        self.assertTrue(receipt["token_required"])
        self.assertTrue(receipt["privacy_warning_acknowledged"])

    def test_obs_browser_live_html_renders_css_without_interpreting_braces(self) -> None:
        server = object.__new__(module.MjpegPreviewServer)
        server.token = None
        body = server._html_body("/live.html").decode("utf-8")

        self.assertIn("html, body { width: 100%;", body)
        self.assertIn('src="/stream.mjpg"', body)

    def test_obs_browser_live_html_preserves_preview_token_for_stream(self) -> None:
        server = object.__new__(module.MjpegPreviewServer)
        server.token = "secret-token"
        body = server._html_body("/live.html?token=secret-token").decode("utf-8")

        self.assertIn('src="/stream.mjpg?token=secret-token"', body)


if __name__ == "__main__":
    unittest.main()
