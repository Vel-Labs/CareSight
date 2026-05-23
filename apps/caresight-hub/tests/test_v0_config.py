import tempfile
import unittest
from pathlib import Path

from caresight.runtime.cameras import camera_source_for_opencv, select_configured_camera
from caresight.runtime.config import CareSightConfig, ZoneConfig


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

    def test_select_configured_camera_uses_matching_floor_zone_when_available(self) -> None:
        payload = CareSightConfig.default().to_dict()
        payload["camera"] = {
            **payload["camera"],
            "camera_id": "living_room",
        }
        payload["cameras"] = [
            {
                **payload["camera"],
                "camera_id": "living_room",
                "room_id": "living_room",
                "room_label": "Living Room",
            },
            {
                **payload["camera"],
                "camera_id": "kitchen",
                "name": "Kitchen",
                "room_id": "kitchen",
                "room_label": "Kitchen",
            },
        ]
        payload["active_camera_id"] = "kitchen"
        payload["floor_zones"] = [
            {
                **payload["floor_zone"],
                "camera_id": "living_room",
                "vertices": [[0.0, 0.6], [1.0, 0.6], [1.0, 1.0], [0.0, 1.0]],
            },
            {
                **payload["floor_zone"],
                "camera_id": "kitchen",
                "vertices": [[0.2, 0.5], [0.8, 0.5], [1.0, 1.0], [0.0, 1.0]],
            },
        ]

        config = CareSightConfig.from_dict(payload)

        self.assertEqual(config.camera.camera_id, "kitchen")
        self.assertEqual(config.floor_zone.camera_id, "kitchen")
        self.assertEqual(config.floor_zone.vertices[0], (0.2, 0.5))

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

    def test_polygon_floor_zone_round_trips_and_contains_points(self) -> None:
        zone = ZoneConfig(
            zone_id="floor_zone",
            camera_id="living_room",
            name="Calibrated Floor Plane",
            kind="floor_low",
            x_min=0.0,
            y_min=0.45,
            x_max=1.0,
            y_max=1.0,
            vertices=((0.25, 0.55), (0.75, 0.55), (1.0, 1.0), (0.0, 1.0)),
        )
        config = CareSightConfig.default()
        config = config.__class__(
            camera=config.camera,
            room=config.room,
            floor_zone=zone,
            floor_stay=config.floor_stay,
            tracking=config.tracking,
            routines=config.routines,
            storage=config.storage,
            cameras=config.cameras,
            active_camera_id=config.active_camera_id,
            floor_zones=(zone,),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "v0.local.json"
            config.save(config_path)
            loaded = CareSightConfig.load(config_path)

        self.assertEqual(loaded.floor_zone.vertices[0], (0.25, 0.55))
        self.assertTrue(loaded.floor_zone.contains_normalized_point(0.5, 0.8))
        self.assertFalse(loaded.floor_zone.contains_normalized_point(0.05, 0.5))


if __name__ == "__main__":
    unittest.main()
