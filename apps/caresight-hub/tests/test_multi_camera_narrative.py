import tempfile
import unittest
from pathlib import Path
import subprocess
import sys

from caresight.events.floor_stay import FloorStayDetector
from caresight.runtime.config import CareSightConfig
from caresight.runtime.demo_surface.multi_camera_narrative import (
    build_multi_camera_narrative,
    render_multi_camera_narrative_markdown,
)
from caresight.storage.sqlite_store import SQLiteStore
from caresight.vision.detections import Detection


class MultiCameraNarrativeTest(unittest.TestCase):
    def test_narrative_is_sqlite_derived_and_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = SQLiteStore(Path(tmpdir) / "caresight.sqlite3")
            store.initialize()
            config = CareSightConfig.default()
            store.upsert_config(config)
            event = build_event(config)
            store.insert_event(event)

            narrative = build_multi_camera_narrative(store, event["event_id"])
            markdown = render_multi_camera_narrative_markdown(narrative)

            self.assertEqual(narrative["schema"], "multi-camera-narrative")
            self.assertEqual(narrative["source_of_truth"], "sqlite")
            self.assertEqual(narrative["claim_boundary"], "likely_continuity_not_identity")
            self.assertEqual(narrative["event"]["camera_id"], "living_room")
            self.assertIn("named_identity", narrative["not_claimed"])
            self.assertIn("likely continuity, not identity", markdown)
            self.assertNotIn("face match", markdown.lower())
            self.assertNotIn("fall confirmed", markdown.lower())

    def test_care_console_renders_narrative_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "caresight.sqlite3"
            store = SQLiteStore(db_path)
            store.initialize()
            config = CareSightConfig.default()
            store.upsert_config(config)
            event = build_event(config)
            store.insert_event(event)

            result = subprocess.run(
                [
                    sys.executable,
                    "apps/caresight-hub/scripts/care_console.py",
                    "--db",
                    str(db_path),
                    "narrative",
                    event["event_id"],
                    "--format",
                    "markdown",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("Multi-Camera Narrative", result.stdout)
            self.assertIn("likely continuity, not identity", result.stdout)


def build_event(config: CareSightConfig) -> dict:
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
