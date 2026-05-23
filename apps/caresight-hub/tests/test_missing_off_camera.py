import unittest
from dataclasses import replace

from caresight.events.missing_off_camera import MissingOffCameraDetector
from caresight.runtime.config import CareSightConfig
from caresight.runtime.tracking import TrackSnapshot, TrackState
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
        missing = tracker.missing_tracks(now=221.0, missing_seconds=config.tracking.missing_seconds)
        event = detector.update(missing, now=221.0)

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event["event_type"], "missing_off_camera_extended")
        self.assertEqual(event["status"], "awaiting_human_confirmation")
        self.assertEqual(event["severity"], "low")
        self.assertEqual(event["evidence"]["track_id"], "track_1")
        self.assertEqual(event["evidence"]["missed_seconds"], 121.0)
        self.assertEqual(event["evidence"]["escalation_stage"], "check_in_suggested")
        self.assertEqual(event["evidence"]["policy_version"], "missing_off_camera_v1_tracking_reliability")
        language = event["evidence"]["caregiver_language"].lower()
        self.assertIn("a tracked person", language)
        self.assertNotIn("resident is missing", language)
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
        missing = tracker.missing_tracks(now=221.0, missing_seconds=config.tracking.missing_seconds)
        first_event = detector.update(missing, now=221.0)
        second_event = detector.update(missing, now=240.0)

        self.assertIsNotNone(first_event)
        self.assertIsNone(second_event)

    def test_observe_only_before_two_minutes(self) -> None:
        detector = MissingOffCameraDetector(CareSightConfig.default())

        event = detector.update([missing_track(119.0)], now=220.0)

        self.assertIsNone(event)

    def test_attention_language_after_recent_concern(self) -> None:
        detector = MissingOffCameraDetector(CareSightConfig.default())

        event = detector.update(
            [missing_track(360.0)],
            now=500.0,
            recent_concern_severity="medium",
        )

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event["severity"], "medium")
        self.assertEqual(event["evidence"]["escalation_stage"], "attention_suggested")
        self.assertIn("caregiver attention", event["evidence"]["caregiver_language"])

    def test_urgent_handoff_language_after_recent_high_concern(self) -> None:
        detector = MissingOffCameraDetector(CareSightConfig.default())

        event = detector.update(
            [missing_track(720.0)],
            now=900.0,
            recent_concern_severity="high",
        )

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event["severity"], "high")
        self.assertEqual(event["evidence"]["escalation_stage"], "urgent_handoff_suggested")
        language = event["evidence"]["caregiver_language"].lower()
        self.assertIn("urgent handoff", language)
        for forbidden in [
            "resident is missing",
            "person is in danger",
            "medical emergency",
            "dispatching help",
        ]:
            self.assertNotIn(forbidden, language)


def missing_track(missed_seconds: float) -> TrackSnapshot:
    return TrackSnapshot(
        track_id="track_99",
        detection=Detection(
            class_name="person",
            confidence=0.9,
            bbox_xyxy=(360, 300, 640, 620),
            frame_width=1280,
            frame_height=720,
        ),
        first_seen_at=100.0,
        last_seen_at=100.0,
        missed_seconds=missed_seconds,
    )


if __name__ == "__main__":
    unittest.main()
