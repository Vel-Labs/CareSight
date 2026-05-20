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
            self.assertTrue(payload["view"]["focused_event_found"])
            self.assertEqual(len(payload["journal_preview"]), 1)
            self.assertEqual(payload["caregiver_alert_draft"]["event_id"], seed.event_id)

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
            bbox_xyxy=(360, 520, 640, 710),
            frame_width=1280,
            frame_height=720,
        )
        detector.update([detection], now=100.0)
        event = detector.update([detection], now=109.0)
        assert event is not None
        self.event_id = event["event_id"]
        self.store.insert_event(event)
        self.service = ReviewService(self.store)

    def __enter__(self) -> "Seed":
        return self

    def __exit__(self, *_args: object) -> None:
        self.tmpdir.cleanup()


def seeded_review_service() -> Seed:
    return Seed(tempfile.TemporaryDirectory())


if __name__ == "__main__":
    unittest.main()
