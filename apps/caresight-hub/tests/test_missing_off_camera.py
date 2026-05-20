import unittest

from caresight.events.missing_off_camera import MissingOffCameraDetector
from caresight.runtime.config import CareSightConfig
from caresight.runtime.tracking import TrackState
from caresight.vision.detections import Detection


class MissingOffCameraDetectorTest(unittest.TestCase):
    def test_emits_after_known_track_is_missing_for_configured_window(self) -> None:
        config = CareSightConfig.default()
        tracker = TrackState(occlusion_grace_seconds=config.tracking.occlusion_grace_seconds)
        detector = MissingOffCameraDetector(config)
        detection = Detection(
            class_name="person",
            confidence=0.91,
            bbox_xyxy=(360, 300, 640, 620),
            frame_width=1280,
            frame_height=720,
        )

        tracker.update([detection], now=100.0)
        missing = tracker.missing_tracks(now=131.0, missing_seconds=config.tracking.missing_seconds)
        event = detector.update(missing, now=131.0)

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event["event_type"], "missing_off_camera_extended")
        self.assertEqual(event["status"], "awaiting_human_confirmation")
        self.assertEqual(event["severity"], "medium")
        self.assertEqual(event["evidence"]["track_id"], "track_1")
        self.assertEqual(event["evidence"]["missed_seconds"], 31.0)
        self.assertIn("autonomous_emergency_dispatch", event["blocked_actions"])

    def test_does_not_emit_duplicate_missing_event_for_same_track(self) -> None:
        config = CareSightConfig.default()
        tracker = TrackState(occlusion_grace_seconds=config.tracking.occlusion_grace_seconds)
        detector = MissingOffCameraDetector(config)
        detection = Detection(
            class_name="person",
            confidence=0.91,
            bbox_xyxy=(360, 300, 640, 620),
            frame_width=1280,
            frame_height=720,
        )

        tracker.update([detection], now=100.0)
        missing = tracker.missing_tracks(now=131.0, missing_seconds=config.tracking.missing_seconds)
        first_event = detector.update(missing, now=131.0)
        second_event = detector.update(missing, now=140.0)

        self.assertIsNotNone(first_event)
        self.assertIsNone(second_event)


if __name__ == "__main__":
    unittest.main()
