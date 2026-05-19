import tempfile
import unittest
from pathlib import Path

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
            self.assertEqual(observations[0]["bbox_json"], event["evidence"]["bbox_xyxy"])


if __name__ == "__main__":
    unittest.main()
