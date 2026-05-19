import tempfile
import unittest
from pathlib import Path

from caresight.events.snapshots import attach_local_snapshot


class EventSnapshotsTest(unittest.TestCase):
    def test_attach_local_snapshot_records_local_path_in_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            event = {
                "event_id": "evt_test_snapshot",
                "evidence": {
                    "raw_video_stays_local": True,
                },
            }

            updated = attach_local_snapshot(
                event=event,
                snapshot_dir=Path(tmpdir) / "snapshots",
                write_snapshot=lambda path: path.write_bytes(b"fake-jpeg"),
            )

            snapshot_path = Path(updated["evidence"]["snapshot_path"])
            self.assertTrue(snapshot_path.exists())
            self.assertEqual(snapshot_path.name, "evt_test_snapshot.jpg")
            self.assertTrue(updated["evidence"]["snapshot_stays_local"])


if __name__ == "__main__":
    unittest.main()
