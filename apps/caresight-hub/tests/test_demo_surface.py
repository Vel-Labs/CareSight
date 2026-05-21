import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from caresight.events.floor_stay import FloorStayDetector
from caresight.runtime.alerts import draft_caregiver_alert
from caresight.runtime.config import CareSightConfig
from caresight.runtime.dashboard import build_dashboard_state
from caresight.runtime.demo_surface import (
    build_blackbox_receipt,
    build_human_review_packet,
    render_blackbox_receipt_markdown,
    render_review_packet_markdown,
)
from caresight.runtime.review import ReviewService
from caresight.storage.sqlite_store import SQLiteStore
from caresight.vision.detections import Detection


class DemoSurfaceTest(unittest.TestCase):
    def test_human_review_packet_is_sqlite_derived_and_read_only(self) -> None:
        with seeded_review_service() as seed:
            packet = build_human_review_packet(
                seed.service.get_audit_chain(seed.event_id),
                created_at="2026-05-20T02:37:00Z",
            )

            self.assertEqual(packet["schema"], "human-review-packet")
            self.assertEqual(packet["source_of_truth"], "sqlite")
            self.assertEqual(packet["event_id"], seed.event_id)
            self.assertEqual(packet["review_state"]["review_count"], 0)
            self.assertEqual(packet["evidence"]["track_ids"], [seed.track_id])
            self.assertEqual(packet["available_human_actions"], ["confirm", "dismiss", "needs_followup"])
            self.assertIn("autonomous_emergency_dispatch", packet["blocked_actions"])
            self.assertEqual(packet["provenance"]["source"], "sqlite_audit_chain")

    def test_blackbox_receipt_marks_missing_review_chain_not_complete(self) -> None:
        with seeded_review_service() as seed:
            audit = seed.service.get_audit_chain(seed.event_id)
            receipt = build_blackbox_receipt(
                audit,
                dashboard_state=build_dashboard_state(seed.service, event_id=seed.event_id),
                alert_draft=draft_caregiver_alert(audit),
                created_at="2026-05-20T02:40:00Z",
            )

            self.assertEqual(receipt["schema"], "blackbox-receipt")
            self.assertEqual(receipt["completion_status"], "not_complete")
            self.assertIn("missing_human_review", receipt["blockers"])
            self.assertIn("missing_journal_entry", receipt["blockers"])
            self.assertIn("missing_report_only_handoff", receipt["blockers"])
            self.assertEqual(receipt["counts"]["observations"], 1)

    def test_blackbox_receipt_completes_after_human_review_chain(self) -> None:
        with seeded_review_service() as seed:
            seed.service.confirm_event(
                seed.event_id,
                reviewer="Casey Caregiver",
                note="Confirmed for receipt demo.",
            )
            audit = seed.service.get_audit_chain(seed.event_id)
            receipt = build_blackbox_receipt(
                audit,
                dashboard_state=build_dashboard_state(seed.service, event_id=seed.event_id),
                alert_draft=draft_caregiver_alert(audit),
                created_at="2026-05-20T02:40:00Z",
            )

            self.assertEqual(receipt["completion_status"], "complete")
            self.assertNotIn("blockers", receipt)
            self.assertEqual(receipt["human_review"]["reviewer"], "Casey Caregiver")
            self.assertEqual(receipt["counts"]["reviews"], 1)
            self.assertEqual(receipt["counts"]["journal_entries"], 1)
            self.assertEqual(receipt["counts"]["agent_handoffs"], 1)
            self.assertTrue(receipt["derived_outputs"]["dashboard_includes_event"])
            self.assertTrue(receipt["derived_outputs"]["alert_draft_has_provenance"])

    def test_markdown_renders_boundaries(self) -> None:
        with seeded_review_service() as seed:
            packet = build_human_review_packet(seed.service.get_audit_chain(seed.event_id))
            receipt = build_blackbox_receipt(seed.service.get_audit_chain(seed.event_id))

            self.assertIn("SQLite is source of truth", render_review_packet_markdown(packet))
            self.assertIn("No autonomous emergency dispatch", render_review_packet_markdown(packet))
            self.assertIn("SQLite is source of truth", render_blackbox_receipt_markdown(receipt))
            self.assertIn("No autonomous emergency dispatch", render_blackbox_receipt_markdown(receipt))


class Seed:
    def __init__(self, tmpdir: tempfile.TemporaryDirectory[str]):
        self.tmpdir = tmpdir
        self.db_path = Path(tmpdir.name) / "caresight.sqlite3"
        self.config = CareSightConfig.default()
        self.store = SQLiteStore(self.db_path)
        self.store.initialize()
        self.store.upsert_config(self.config)
        event = build_floor_stay_event(self.config)
        self.event_id = event["event_id"]
        self.track_id = event["evidence"]["track_id"]
        self.store.insert_event(event)
        self.service = ReviewService(self.store)

    def __enter__(self) -> "Seed":
        return self

    def __exit__(self, *_args: object) -> None:
        self.tmpdir.cleanup()


def seeded_review_service() -> Seed:
    return Seed(tempfile.TemporaryDirectory())


def build_floor_stay_event(config: CareSightConfig) -> dict:
    occurred_at = datetime(2026, 5, 20, 14, 0, 9, tzinfo=UTC)
    detector = FloorStayDetector(config)
    detection = Detection(
        class_name="person",
        confidence=0.91,
        bbox_xyxy=(360, 520, 640, 710),
        frame_width=1280,
        frame_height=720,
    )
    detector.update([detection], now=occurred_at.timestamp() - config.floor_stay.dwell_seconds - 1)
    event = detector.update([detection], now=occurred_at.timestamp())
    assert event is not None
    event["evidence"]["snapshot_path"] = "data/snapshots/fresh-live-event.jpg"
    return event


if __name__ == "__main__":
    unittest.main()
