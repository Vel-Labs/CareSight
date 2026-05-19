import unittest

from caresight.events.floor_stay import FloorStayDetector
from caresight.runtime.config import CareSightConfig
from caresight.vision.detections import Detection


class FloorStayDetectorTest(unittest.TestCase):
    def test_emits_possible_floor_stay_after_person_dwells_in_floor_zone(self) -> None:
        config = CareSightConfig.default()
        detector = FloorStayDetector(config)
        detection = Detection(
            class_name="person",
            confidence=0.91,
            bbox_xyxy=(360, 520, 640, 710),
            frame_width=1280,
            frame_height=720,
        )

        self.assertIsNone(detector.update([detection], now=100.0))
        event = detector.update([detection], now=109.0)

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event["schema"], "care-event")
        self.assertEqual(event["event_type"], "possible_floor_stay")
        self.assertEqual(event["camera_id"], "living_room")
        self.assertEqual(event["zone_id"], "floor_zone")
        self.assertEqual(event["status"], "awaiting_human_confirmation")
        self.assertTrue(event["requires_human_confirmation"])
        self.assertIn("autonomous_emergency_dispatch", event["blocked_actions"])
        self.assertGreaterEqual(event["evidence"]["dwell_seconds"], 8.0)

    def test_does_not_emit_repeated_events_during_same_dwell(self) -> None:
        config = CareSightConfig.default()
        detector = FloorStayDetector(config)
        detection = Detection(
            class_name="person",
            confidence=0.91,
            bbox_xyxy=(360, 520, 640, 710),
            frame_width=1280,
            frame_height=720,
        )

        detector.update([detection], now=100.0)
        first_event = detector.update([detection], now=109.0)
        second_event = detector.update([detection], now=112.0)

        self.assertIsNotNone(first_event)
        self.assertIsNone(second_event)


if __name__ == "__main__":
    unittest.main()
