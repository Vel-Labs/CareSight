import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
