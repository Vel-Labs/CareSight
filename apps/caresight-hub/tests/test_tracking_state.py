import unittest

from caresight.runtime.tracking import TrackState
from caresight.vision.detections import Detection


class TrackStateTest(unittest.TestCase):
    def test_reuses_track_id_for_overlapping_person_detection(self) -> None:
        tracker = TrackState()
        first = person_box(360, 300, 640, 620)
        second = person_box(370, 310, 650, 630)

        first_tracks = tracker.update([first], now=100.0)
        second_tracks = tracker.update([second], now=101.0)

        self.assertEqual(first_tracks[0].track_id, "track_1")
        self.assertEqual(second_tracks[0].track_id, "track_1")

    def test_expires_track_after_occlusion_grace(self) -> None:
        tracker = TrackState(occlusion_grace_seconds=1.0)
        detection = person_box(360, 300, 640, 620)

        tracker.update([detection], now=100.0)
        tracker.update([], now=102.0)
        tracks = tracker.update([detection], now=103.0)

        self.assertEqual(tracks[0].track_id, "track_2")


def person_box(x1: float, y1: float, x2: float, y2: float) -> Detection:
    return Detection(
        class_name="person",
        confidence=0.9,
        bbox_xyxy=(x1, y1, x2, y2),
        frame_width=1280,
        frame_height=720,
    )


if __name__ == "__main__":
    unittest.main()
