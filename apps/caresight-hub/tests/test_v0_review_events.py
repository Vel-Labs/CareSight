import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from caresight.events.floor_stay import FloorStayDetector
from caresight.events.snapshots import attach_local_snapshot
from caresight.runtime.config import CareSightConfig
from caresight.runtime.review import ReviewService, ReviewServiceError
from caresight.storage.sqlite_store import SQLiteStore
from caresight.vision.detections import Detection


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT_DIR / "scripts" / "v0_review_events.py"


class V0ReviewEventsCliTest(unittest.TestCase):
    def test_list_only_shows_awaiting_events_by_default(self) -> None:
        with seeded_store() as seed:
            confirmed_id = seed_event(seed.store, now=120.0)
            seed.store.record_event_review(confirmed_id, reviewer="steven", decision="human_confirmed")

            result = run_cli(seed.db_path, "list")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(seed.event_id, result.stdout)
            self.assertIn("awaiting_human_confirmation", result.stdout)
            self.assertNotIn(confirmed_id, result.stdout)

    def test_show_renders_human_readable_summary(self) -> None:
        with seeded_store() as seed:
            result = run_cli(seed.db_path, "show", seed.event_id)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"Event: {seed.event_id}", result.stdout)
            self.assertIn("Possible floor-stay event in Living Room.", result.stdout)
            self.assertIn("Status: awaiting human confirmation.", result.stdout)
            self.assertIn("Zone: Floor / Low Zone.", result.stdout)
            self.assertIn("Observed in Floor / Low Zone for 8.03 seconds.", result.stdout)
            self.assertIn("Snapshot:", result.stdout)
            self.assertIn("Blocked actions: autonomous emergency dispatch, medical diagnosis.", result.stdout)

    def test_confirm_requires_reviewer(self) -> None:
        with seeded_store() as seed:
            result = run_cli(seed.db_path, "confirm", seed.event_id)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--reviewer is required", result.stderr)
            self.assertEqual(seed.store.get_event(seed.event_id)["status"], "awaiting_human_confirmation")

    def test_confirm_updates_status_review_journal_and_handoff(self) -> None:
        with seeded_store() as seed:
            result = run_cli(
                seed.db_path,
                "confirm",
                seed.event_id,
                "--reviewer",
                "steven",
                "--note",
                "Checked snapshot, person was resting intentionally.",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("human_confirmed", result.stdout)
            self.assertEqual(seed.store.get_event(seed.event_id)["status"], "human_confirmed")

            review = only_row(seed.db_path, "event_reviews")
            self.assertEqual(review["event_id"], seed.event_id)
            self.assertEqual(review["reviewer"], "steven")
            self.assertEqual(review["decision"], "human_confirmed")

            journal = only_row(seed.db_path, "journal_entries")
            self.assertEqual(journal["event_id"], seed.event_id)
            self.assertEqual(journal["entry_type"], "event_review")
            self.assertIn("human confirmed", journal["body"])
            self.assertIn("Checked snapshot", journal["body"])

            handoff = only_row(seed.db_path, "agent_handoffs")
            payload = json.loads(handoff["payload_json"])
            self.assertEqual(payload["event_id"], seed.event_id)
            self.assertEqual(payload["snapshot_path"], seed.snapshot_path)
            self.assertEqual(payload["reviewer"], "steven")
            self.assertEqual(payload["review_id"], review["review_id"])
            self.assertEqual(payload["journal_id"], journal["journal_id"])
            self.assertEqual(payload["reviewed_at"], review["reviewed_at"])
            self.assertIn("autonomous_emergency_dispatch", payload["blocked_actions"])
            self.assertTrue(payload["requires_human_confirmation"])
            self.assertEqual(handoff["status"], "report_only")

    def test_confirm_rejects_automation_reviewer_of_record(self) -> None:
        with seeded_store() as seed:
            result = run_cli(
                seed.db_path,
                "confirm",
                seed.event_id,
                "--reviewer",
                "agent",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("reviewer must be an authorized human", result.stderr)
            self.assertEqual(seed.store.get_event(seed.event_id)["status"], "awaiting_human_confirmation")

    def test_dismiss_updates_status_review_journal_and_handoff(self) -> None:
        with seeded_store() as seed:
            result = run_cli(
                seed.db_path,
                "dismiss",
                seed.event_id,
                "--reviewer",
                "steven",
                "--note",
                "False positive, standing near couch.",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(seed.store.get_event(seed.event_id)["status"], "dismissed")
            review = only_row(seed.db_path, "event_reviews")
            self.assertEqual(review["decision"], "dismissed")
            journal = only_row(seed.db_path, "journal_entries")
            self.assertIn("dismissed", journal["body"])

    def test_journal_command_renders_existing_human_entry(self) -> None:
        with seeded_store() as seed:
            seed.store.record_event_review(
                seed.event_id,
                reviewer="steven",
                decision="dismissed",
                note="False positive, standing near couch.",
            )

            result = run_cli(seed.db_path, "journal", seed.event_id)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Care Journal", result.stdout)
            self.assertIn(seed.event_id, result.stdout)
            self.assertIn("False positive", result.stdout)

    def test_audit_command_renders_blackbox_chain(self) -> None:
        with seeded_store() as seed:
            seed.store.record_event_review(
                seed.event_id,
                reviewer="steven",
                decision="dismissed",
                note="False positive, standing near couch.",
            )

            result = run_cli(seed.db_path, "audit", seed.event_id)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("CareSight SQLite Audit", result.stdout)
            self.assertIn(f"Event ID: {seed.event_id}", result.stdout)
            self.assertIn("Status: dismissed", result.stdout)
            self.assertIn(f"Snapshot path: {seed.snapshot_path}", result.stdout)
            self.assertIn("Observation rows: 1", result.stdout)
            self.assertIn("Review rows: 1", result.stdout)
            self.assertIn("Journal rows: 1", result.stdout)
            self.assertIn("Agent handoff rows: 1", result.stdout)
            self.assertIn("Latest reviewer: steven", result.stdout)
            self.assertIn("Latest handoff status: report_only", result.stdout)
            self.assertIn("agents may summarize or draft but cannot confirm", result.stdout)

    def test_no_command_can_create_emergency_dispatch(self) -> None:
        with seeded_store() as seed:
            result = run_cli(seed.db_path, "emergency_dispatch", seed.event_id)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid choice", result.stderr)

    def test_no_command_can_delete_events(self) -> None:
        with seeded_store() as seed:
            result = run_cli(seed.db_path, "delete", seed.event_id)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid choice", result.stderr)


class ReviewServiceTest(unittest.TestCase):
    def test_confirm_requires_human_reviewer_and_preserves_awaiting_status(self) -> None:
        with seeded_store() as seed:
            service = ReviewService(seed.store)

            with self.assertRaisesRegex(ReviewServiceError, "--reviewer is required"):
                service.confirm_event(seed.event_id, reviewer=" ")

            self.assertEqual(seed.store.get_event(seed.event_id)["status"], "awaiting_human_confirmation")

    def test_confirm_updates_status_review_journal_and_handoff(self) -> None:
        with seeded_store() as seed:
            service = ReviewService(seed.store)

            result = service.confirm_event(
                seed.event_id,
                reviewer="  steven  ",
                note="Checked snapshot, likely observed floor stay.",
            )

            self.assertEqual(result["decision"], "human_confirmed")
            self.assertEqual(seed.store.get_event(seed.event_id)["status"], "human_confirmed")
            review = only_row(seed.db_path, "event_reviews")
            self.assertEqual(review["reviewer"], "steven")
            journal = only_row(seed.db_path, "journal_entries")
            self.assertIn("likely observed", journal["body"])
            handoff = only_row(seed.db_path, "agent_handoffs")
            payload = json.loads(handoff["payload_json"])
            self.assertEqual(payload["review_id"], review["review_id"])
            self.assertEqual(payload["journal_id"], journal["journal_id"])
            self.assertEqual(handoff["status"], "report_only")

    def test_dismiss_updates_status_review_journal_and_handoff(self) -> None:
        with seeded_store() as seed:
            service = ReviewService(seed.store)

            service.dismiss_event(
                seed.event_id,
                reviewer="steven",
                note="Dismissed after human review.",
            )

            self.assertEqual(seed.store.get_event(seed.event_id)["status"], "dismissed")
            review = only_row(seed.db_path, "event_reviews")
            self.assertEqual(review["decision"], "dismissed")
            journal = only_row(seed.db_path, "journal_entries")
            self.assertIn("Dismissed after human review.", journal["body"])
            handoff = only_row(seed.db_path, "agent_handoffs")
            self.assertEqual(handoff["status"], "report_only")

    def test_agent_cannot_confirm_or_dismiss(self) -> None:
        with seeded_store() as seed:
            service = ReviewService(seed.store)

            for reviewer in ("agent", "Codex", "automation", "llm"):
                with self.assertRaisesRegex(ReviewServiceError, "reviewer must be an authorized human"):
                    service.confirm_event(seed.event_id, reviewer=reviewer)
                with self.assertRaisesRegex(ReviewServiceError, "reviewer must be an authorized human"):
                    service.dismiss_event(seed.event_id, reviewer=reviewer)

            self.assertEqual(seed.store.get_event(seed.event_id)["status"], "awaiting_human_confirmation")

    def test_audit_chain_reads_sqlite_blackbox_records(self) -> None:
        with seeded_store() as seed:
            service = ReviewService(seed.store)
            service.dismiss_event(seed.event_id, reviewer="steven")

            audit = service.get_audit_chain(seed.event_id)

            self.assertEqual(audit["event"]["event_id"], seed.event_id)
            self.assertEqual(len(audit["observations"]), 1)
            self.assertEqual(len(audit["reviews"]), 1)
            self.assertEqual(len(audit["journal_entries"]), 1)
            self.assertEqual(len(audit["agent_handoffs"]), 1)


class Seed:
    def __init__(self, tmpdir: tempfile.TemporaryDirectory[str]):
        self._tmpdir = tmpdir
        self.db_path = Path(tmpdir.name) / "caresight.sqlite3"
        self.store = SQLiteStore(self.db_path)
        self.store.initialize()
        self.store.upsert_config(CareSightConfig.default())
        self.event_id = seed_event(self.store, now=100.0)
        self.snapshot_path = self.store.get_event(self.event_id)["evidence"]["snapshot_path"]

    def __enter__(self) -> "Seed":
        return self

    def __exit__(self, *args: object) -> None:
        self._tmpdir.cleanup()


def seeded_store() -> Seed:
    return Seed(tempfile.TemporaryDirectory())


def seed_event(store: SQLiteStore, now: float) -> str:
    detector = FloorStayDetector(CareSightConfig.default())
    detection = Detection(
        class_name="person",
        confidence=0.885,
        bbox_xyxy=(360, 520, 640, 710),
        frame_width=1280,
        frame_height=720,
    )
    detector.update([detection], now=now)
    event = detector.update([detection], now=now + 8.03)
    assert event is not None
    event = attach_local_snapshot(
        event=event,
        snapshot_dir=store.database_path.parent / "snapshots",
        write_snapshot=lambda path: path.write_bytes(b"fake-jpeg"),
    )
    store.insert_event(event)
    return str(event["event_id"])


def run_cli(db_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--db", str(db_path), *args],
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
        check=False,
    )


def only_row(db_path: Path, table_name: str) -> sqlite3.Row:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(f"SELECT * FROM {table_name}").fetchall()
    assert len(rows) == 1
    return rows[0]


if __name__ == "__main__":
    unittest.main()
