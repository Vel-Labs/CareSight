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
                bbox_xyxy=(360, 520, 640, 710),
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


if __name__ == "__main__":
    unittest.main()
