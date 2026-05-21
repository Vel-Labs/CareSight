import gc
import tempfile
import unittest
import warnings
from pathlib import Path
import sqlite3

from caresight.events.floor_stay import FloorStayDetector
from caresight.runtime.config import CareSightConfig
from caresight.storage.sqlite_store import SQLiteStore
from caresight.vision.detections import Detection


class SQLiteStoreTest(unittest.TestCase):
    def test_stores_config_snapshot_and_event_readback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "caresight.sqlite3"
            config = CareSightConfig.default()
            store = SQLiteStore(db_path)
            store.initialize()
            store.upsert_config(config)

            detector = FloorStayDetector(config)
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

            store.insert_event(event)
            stored = store.get_event(event["event_id"])

            self.assertEqual(stored["event_id"], event["event_id"])
            self.assertEqual(stored["event_type"], "possible_floor_stay")
            self.assertEqual(stored["zone_id"], "floor_zone")
            self.assertEqual(stored["evidence"]["raw_video_stays_local"], True)
            self.assertEqual(store.list_zones()[0]["zone_id"], "floor_zone")
            observations = store.list_event_observations(event["event_id"])
            self.assertEqual(len(observations), 1)
            self.assertEqual(observations[0]["class_name"], "person")
            self.assertEqual(observations[0]["zone_id"], "floor_zone")
            self.assertEqual(observations[0]["track_id"], event["evidence"]["track_id"])
            self.assertEqual(observations[0]["bbox_json"], event["evidence"]["bbox_xyxy"])

    def test_initialize_adds_track_id_to_existing_observations_without_deleting_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "legacy.sqlite3"
            conn = sqlite3.connect(db_path)
            conn.executescript(
                """
                CREATE TABLE event_observations (
                  observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  event_id TEXT NOT NULL,
                  observed_at TEXT NOT NULL,
                  class_name TEXT NOT NULL,
                  confidence REAL NOT NULL,
                  bbox_json TEXT NOT NULL,
                  zone_id TEXT
                );
                INSERT INTO event_observations (
                  event_id,
                  observed_at,
                  class_name,
                  confidence,
                  bbox_json,
                  zone_id
                )
                VALUES (
                  'evt_legacy',
                  '2026-05-19T03:20:36Z',
                  'person',
                  0.91,
                  '[1, 2, 3, 4]',
                  'floor_zone'
                );
                """
            )
            conn.close()

            store = SQLiteStore(db_path)
            store.initialize()

            conn = sqlite3.connect(db_path)
            columns = {row[1] for row in conn.execute("PRAGMA table_info(event_observations)")}
            row = conn.execute(
                "SELECT event_id, class_name, track_id FROM event_observations WHERE event_id = 'evt_legacy'"
            ).fetchone()
            conn.close()

            self.assertIn("track_id", columns)
            self.assertEqual(row, ("evt_legacy", "person", None))

    def test_stores_observation_check_without_event_review_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "caresight.sqlite3"
            config = CareSightConfig.default()
            store = SQLiteStore(db_path)
            store.initialize()
            store.upsert_config(config)
            check = {
                "check_id": "check_normal_desk",
                "check_type": "normal_presence_no_event",
                "started_at": "2026-05-21T18:00:00Z",
                "completed_at": "2026-05-21T18:01:00Z",
                "camera_id": "living_room",
                "zone_id": "floor_zone",
                "status": "no_event_persisted",
                "frame_count": 1800,
                "elapsed_seconds": 60.0,
                "required_dwell_seconds": 8.0,
                "event_id": None,
                "result": {
                    "status": "no_possible_floor_stay_event",
                    "camera_id": "living_room",
                    "zone_id": "floor_zone",
                },
            }

            store.insert_observation_check(check)
            stored = store.get_observation_check("check_normal_desk")

            self.assertEqual(stored["schema"], "observation-check")
            self.assertEqual(stored["status"], "no_event_persisted")
            self.assertIsNone(stored["event_id"])
            self.assertEqual(stored["frame_count"], 1800)
            self.assertEqual(stored["result"]["status"], "no_possible_floor_stay_event")
            self.assertEqual(store.list_events(), [])
            self.assertEqual(store.list_observation_checks()[0]["check_id"], "check_normal_desk")

    def test_stores_agent_execution_attempt_without_changing_action_request_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "caresight.sqlite3"
            config = CareSightConfig.default()
            store = SQLiteStore(db_path)
            store.initialize()
            store.upsert_config(config)
            event = _floor_stay_event(config)
            store.insert_event(event)
            draft = {
                "draft_id": "draft_exec_attempt",
                "event_id": event["event_id"],
                "created_at": "2026-05-21T19:00:00Z",
                "provider": "fake",
                "purpose": "alert_draft",
                "validation_status": "validated",
                "draft_text": "CareSight recorded a possible event.",
                "safe_rewrite": None,
                "blocked_claims": [],
                "safety_boundaries": ["draft_only"],
                "provenance": {"source": "test"},
            }
            request = {
                "request_id": "action_req_exec_attempt",
                "event_id": event["event_id"],
                "created_at": "2026-05-21T19:00:01Z",
                "requested_action": "send_imessage_draft",
                "stage": "staged",
                "execution_state": "not_executed",
                "requires_human_approval": True,
                "source_draft_id": draft["draft_id"],
                "destination": "imessage",
                "escalation_level": "urgent_handoff",
                "recipient_role": "emergency_contact",
                "allowed_contact_ids": ["contact_emergency_primary"],
                "response_options": ["acknowledge_text_update"],
                "safety_boundaries": ["stage_only", "no_external_execution"],
                "provenance": {"source": "test"},
            }
            attempt = {
                "attempt_id": "attempt_exec_attempt",
                "request_id": request["request_id"],
                "event_id": event["event_id"],
                "created_at": "2026-05-21T19:00:02Z",
                "harness": "hermes",
                "attempt_kind": "dry_run",
                "execution_state": "dry_run",
                "result": "payload_logged_no_send",
                "external_action_performed": False,
                "payload": {"schema": "hermes-handoff-payload"},
                "safety_boundaries": ["no_external_execution"],
                "provenance": {"source": "test"},
            }

            store.insert_agent_draft(draft)
            store.insert_agent_action_request(request)
            store.insert_agent_execution_attempt(attempt)
            stored = store.list_agent_execution_attempts(request["request_id"])[0]

            self.assertEqual(stored["schema"], "agent-execution-attempt")
            self.assertEqual(stored["attempt_id"], "attempt_exec_attempt")
            self.assertEqual(stored["execution_state"], "dry_run")
            self.assertFalse(stored["external_action_performed"])
            self.assertEqual(stored["payload"]["schema"], "hermes-handoff-payload")
            self.assertEqual(
                store.get_agent_action_request(request["request_id"])["execution_state"],
                "not_executed",
            )

    def test_store_operations_do_not_leave_unclosed_sqlite_connections(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "caresight.sqlite3"
            store = SQLiteStore(db_path)

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", ResourceWarning)
                store.initialize()
                store.upsert_config(CareSightConfig.default())
                self.assertEqual(store.list_zones()[0]["zone_id"], "floor_zone")
                gc.collect()

            sqlite_warnings = [
                warning
                for warning in caught
                if issubclass(warning.category, ResourceWarning)
                and "sqlite" in str(warning.message).lower()
                and "unclosed" in str(warning.message).lower()
            ]
            self.assertEqual(sqlite_warnings, [])


def _floor_stay_event(config: CareSightConfig) -> dict:
    detector = FloorStayDetector(config)
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
    return event


if __name__ == "__main__":
    unittest.main()
