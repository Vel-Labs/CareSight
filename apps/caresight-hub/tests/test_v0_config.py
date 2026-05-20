import tempfile
import unittest
from pathlib import Path

from caresight.runtime.cameras import camera_source_for_opencv, select_configured_camera
from caresight.runtime.config import CareSightConfig


class V0ConfigTest(unittest.TestCase):
    def test_default_config_can_be_saved_and_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "v0.local.json"
            original = CareSightConfig.default()

            original.save(config_path)
            loaded = CareSightConfig.load(config_path)

            self.assertEqual(loaded.camera.camera_id, "living_room")
            self.assertEqual(loaded.floor_zone.zone_id, "floor_zone")
            self.assertEqual(loaded.floor_stay.dwell_seconds, 8.0)
            self.assertEqual(loaded.storage.database_path, "apps/caresight-hub/data/caresight-v0.sqlite3")

    def test_select_configured_camera_preserves_camera_room_and_source_metadata(self) -> None:
        config = CareSightConfig.load(Path("apps/caresight-hub/config/v0.local.json"))

        selected = select_configured_camera(config, camera_id="kitchen_rtsp")

        self.assertEqual(selected.camera.camera_id, "kitchen_rtsp")
        self.assertEqual(selected.camera.source_type, "rtsp")
        self.assertEqual(selected.room.room_id, "kitchen")
        self.assertEqual(selected.room.name, "Kitchen")
        self.assertEqual(selected.floor_zone.camera_id, "kitchen_rtsp")
        self.assertEqual(camera_source_for_opencv(selected.camera), "rtsp://192.0.2.10/local-demo")

    def test_select_configured_camera_rejects_unsupported_source_type(self) -> None:
        config = CareSightConfig.load(Path("apps/caresight-hub/config/v0.local.json"))

        with self.assertRaisesRegex(ValueError, "no configured camera"):
            select_configured_camera(config, source_type="onvif")

    def test_config_rejects_cloud_provider_camera_scope(self) -> None:
        payload = CareSightConfig.default().to_dict()
        payload["camera"] = {
            **payload["camera"],
            "camera_id": "ring_doorbell",
            "name": "Ring Doorbell",
            "source_type": "ring",
            "source_uri": "https://ring.example.invalid/live",
        }

        with self.assertRaisesRegex(ValueError, "unsupported camera source_type"):
            CareSightConfig.from_dict(payload)


if __name__ == "__main__":
    unittest.main()
