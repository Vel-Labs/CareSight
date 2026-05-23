import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

from caresight.runtime.config import CareSightConfig

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


if __name__ == "__main__":
    unittest.main()
