import json
import subprocess
import sys
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from caresight.events.floor_stay import FloorStayDetector
from caresight.runtime.audit.live_proof import (
    LiveProofAuditCollector,
    ReadinessInputs,
    build_readiness_report,
)
from caresight.runtime.config import CareSightConfig
from caresight.storage.sqlite_store import SQLiteStore
from caresight.vision.detections import Detection

ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT = ROOT_DIR / "scripts" / "live_proof_audit.py"


class LiveProofAuditTest(unittest.TestCase):
    def test_readiness_reports_camera_authorization_blocker_without_camera_access(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CareSightConfig.default()
            config_path = Path(tmpdir) / "v0.local.json"
            model_path = Path(tmpdir) / "yolo26n.npz"
            config.save(config_path)
            model_path.write_text("placeholder", encoding="utf-8")

            report = build_readiness_report(
                ReadinessInputs(
                    config_path=config_path,
                    model_path=model_path,
                    camera_authorization="blocked",
                )
            )

            self.assertEqual(report["status"], "not_ready")
            self.assertIn("camera_authorization_blocked", report["blockers"])
            self.assertEqual(report["checks"]["config"]["camera_source_type"], "webcam")
            self.assertEqual(report["checks"]["config"]["room_label"], "Living Room")
            self.assertIn(
                {
                    "camera_id": "living_room",
                    "camera_name": "Living Room",
                    "room_id": "living_room",
                    "room_label": "Living Room",
                    "source_type": "webcam",
                },
                report["checks"]["config"]["configured_cameras"],
            )
            self.assertEqual(report["checks"]["config"]["status"], "ready")
            self.assertTrue(report["checks"]["model"]["exists"])

    def test_collector_reads_complete_sqlite_backed_provenance(self) -> None:
        occurred_at = datetime(2026, 5, 20, 14, 0, 9, tzinfo=UTC)
        with seeded_live_event(occurred_at=occurred_at, reviewed=True) as seed:
            collector = LiveProofAuditCollector(
                seed.store,
                now=occurred_at + timedelta(minutes=1),
                max_event_age=timedelta(minutes=15),
            )

            bundle = collector.collect(seed.event_id)

            self.assertEqual(bundle["status"], "complete")
            self.assertEqual(bundle["source_of_truth"], "sqlite")
            self.assertEqual(bundle["checks"]["blockers"], [])
            self.assertEqual(bundle["bundle"]["event"]["event_id"], seed.event_id)
            self.assertEqual(bundle["bundle"]["observations"][0]["track_id"], seed.track_id)
            self.assertEqual(bundle["bundle"]["reviews"][0]["reviewer"], "Casey Caregiver")
            self.assertEqual(bundle["bundle"]["journal_entries"][0]["created_by"], "Casey Caregiver")
            self.assertEqual(bundle["bundle"]["agent_handoffs"][0]["status"], "report_only")
            self.assertEqual(bundle["bundle"]["dashboard"]["source_of_truth"], "sqlite")
            self.assertEqual(
                bundle["bundle"]["dashboard"]["timeline_entry"]["event_id"],
                seed.event_id,
            )
            self.assertEqual(bundle["bundle"]["caregiver_alert_draft"]["event_id"], seed.event_id)
            self.assertEqual(
                bundle["bundle"]["caregiver_alert_draft"]["provenance"]["source"],
                "sqlite_audit_chain",
            )

    def test_missing_review_journal_handoff_yields_not_complete(self) -> None:
        occurred_at = datetime(2026, 5, 20, 14, 0, 9, tzinfo=UTC)
        with seeded_live_event(occurred_at=occurred_at, reviewed=False) as seed:
            collector = LiveProofAuditCollector(
                seed.store,
                now=occurred_at + timedelta(minutes=1),
            )

            bundle = collector.collect(seed.event_id)

            self.assertEqual(bundle["status"], "not_complete")
            self.assertIn("missing_human_review", bundle["checks"]["blockers"])
            self.assertIn("missing_journal_entry", bundle["checks"]["blockers"])
            self.assertIn("missing_report_only_handoff", bundle["checks"]["blockers"])

    def test_stale_event_id_yields_not_complete(self) -> None:
        occurred_at = datetime(2026, 5, 20, 14, 0, 9, tzinfo=UTC)
        with seeded_live_event(occurred_at=occurred_at, reviewed=True) as seed:
            collector = LiveProofAuditCollector(
                seed.store,
                now=occurred_at + timedelta(hours=1),
                max_event_age=timedelta(minutes=15),
            )

            bundle = collector.collect(seed.event_id)

            self.assertEqual(bundle["status"], "not_complete")
            self.assertIn("stale_event_id", bundle["checks"]["blockers"])

    def test_live_proof_audit_help_does_not_require_runtime_camera_access(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True,
            check=False,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("readiness", result.stdout)
        self.assertIn("bundle", result.stdout)

    def test_live_proof_audit_cli_bundle_outputs_not_complete_for_unreviewed_event(self) -> None:
        occurred_at = datetime.now(UTC)
        with seeded_live_event(occurred_at=occurred_at, reviewed=False) as seed:
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--db",
                    str(seed.db_path),
                    "bundle",
                    seed.event_id,
                    "--max-event-age-minutes",
                    "60",
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "not_complete")
            self.assertIn("missing_human_review", payload["checks"]["blockers"])


class Seed:
    def __init__(self, tmpdir: tempfile.TemporaryDirectory[str], *, occurred_at: datetime, reviewed: bool):
        self.tmpdir = tmpdir
        self.db_path = Path(tmpdir.name) / "caresight.sqlite3"
        self.config = CareSightConfig.default()
        self.store = SQLiteStore(self.db_path)
        self.store.initialize()
        self.store.upsert_config(self.config)
        event = build_floor_stay_event(self.config, occurred_at)
        self.event_id = event["event_id"]
        self.track_id = event["evidence"]["track_id"]
        self.store.insert_event(event)
        if reviewed:
            self.store.record_event_review(
                self.event_id,
                reviewer="Casey Caregiver",
                decision="human_confirmed",
                note="Resident was helped back to the chair.",
            )

    def __enter__(self) -> "Seed":
        return self

    def __exit__(self, *_args: object) -> None:
        self.tmpdir.cleanup()


def seeded_live_event(*, occurred_at: datetime, reviewed: bool) -> Seed:
    return Seed(tempfile.TemporaryDirectory(), occurred_at=occurred_at, reviewed=reviewed)


def build_floor_stay_event(config: CareSightConfig, occurred_at: datetime) -> dict:
    detector = FloorStayDetector(config)
    detection = Detection(
        class_name="person",
        confidence=0.91,
        bbox_xyxy=(200, 430, 1080, 715),
        frame_width=1280,
        frame_height=720,
    )
    start = occurred_at.timestamp() - config.floor_stay.dwell_seconds - 1
    detector.update([detection], now=start)
    event = detector.update([detection], now=occurred_at.timestamp())
    assert event is not None
    event["evidence"]["snapshot_path"] = "data/snapshots/fresh-live-event.jpg"
    return event


if __name__ == "__main__":
    unittest.main()
