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
            bbox_xyxy=(200, 430, 1080, 715),
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
        self.assertEqual(event["evidence"]["track_id"], "track_1")
        self.assertEqual(event["evidence"]["room_id"], "living_room")

    def test_does_not_emit_repeated_events_during_same_dwell(self) -> None:
        config = CareSightConfig.default()
        detector = FloorStayDetector(config)
        detection = Detection(
            class_name="person",
            confidence=0.91,
            bbox_xyxy=(200, 430, 1080, 715),
            frame_width=1280,
            frame_height=720,
        )

        detector.update([detection], now=100.0)
        first_event = detector.update([detection], now=109.0)
        second_event = detector.update([detection], now=112.0)

        self.assertIsNotNone(first_event)
        self.assertIsNone(second_event)

    def test_same_track_survives_short_occlusion_before_dwell_event(self) -> None:
        config = CareSightConfig.default()
        detector = FloorStayDetector(config)
        detection = Detection(
            class_name="person",
            confidence=0.91,
            bbox_xyxy=(200, 430, 1080, 715),
            frame_width=1280,
            frame_height=720,
        )

        detector.update([detection], now=100.0)
        self.assertIsNone(detector.update([], now=100.5))
        event = detector.update([detection], now=109.0)

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event["evidence"]["track_id"], "track_1")

    def test_floor_stay_dwell_survives_jittery_candidate_track_ids(self) -> None:
        config = CareSightConfig.default()
        detector = FloorStayDetector(config)
        first = Detection(
            class_name="person",
            confidence=0.91,
            bbox_xyxy=(50, 430, 650, 715),
            frame_width=1280,
            frame_height=720,
        )
        shifted = Detection(
            class_name="person",
            confidence=0.88,
            bbox_xyxy=(680, 430, 1280, 715),
            frame_width=1280,
            frame_height=720,
        )

        detector.update([first], now=100.0)
        event = detector.update([shifted], now=109.0)

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event["event_type"], "possible_floor_stay")
        self.assertEqual(event["evidence"]["track_id"], "track_2")
        self.assertGreaterEqual(event["evidence"]["dwell_seconds"], 8.0)

    def test_long_occlusion_resets_floor_stay_dwell(self) -> None:
        config = CareSightConfig.default()
        detector = FloorStayDetector(config)
        detection = Detection(
            class_name="person",
            confidence=0.91,
            bbox_xyxy=(200, 430, 1080, 715),
            frame_width=1280,
            frame_height=720,
        )

        detector.update([detection], now=100.0)
        detector.update([], now=102.0)
        self.assertIsNone(detector.update([detection], now=109.0))

    def test_new_track_after_reset_can_emit_new_event(self) -> None:
        config = CareSightConfig.default()
        detector = FloorStayDetector(config)
        detection = Detection(
            class_name="person",
            confidence=0.91,
            bbox_xyxy=(200, 430, 1080, 715),
            frame_width=1280,
            frame_height=720,
        )

        detector.update([detection], now=100.0)
        first_event = detector.update([detection], now=109.0)
        detector.update([], now=112.0)
        detector.update([detection], now=200.0)
        second_event = detector.update([detection], now=209.0)

        self.assertIsNotNone(first_event)
        self.assertIsNotNone(second_event)
        assert first_event is not None
        assert second_event is not None
        self.assertEqual(first_event["evidence"]["track_id"], "track_1")
        self.assertEqual(second_event["evidence"]["track_id"], "track_2")

    def test_seated_desk_posture_does_not_emit_floor_stay(self) -> None:
        config = CareSightConfig.default()
        detector = FloorStayDetector(config)
        detection = Detection(
            class_name="person",
            confidence=0.95,
            bbox_xyxy=(153, 225, 937, 719),
            frame_width=1280,
            frame_height=720,
        )

        detector.update([detection], now=100.0)
        event = detector.update([detection], now=109.0)

        self.assertIsNone(event)

    def test_diagnostic_explains_non_floor_stay_person(self) -> None:
        config = CareSightConfig.default()
        detector = FloorStayDetector(config)
        detection = Detection(
            class_name="person",
            confidence=0.95,
            bbox_xyxy=(500, 0, 1000, 720),
            frame_width=1280,
            frame_height=720,
        )

        detector.update([detection], now=100.0)
        diagnostic = detector.diagnostic()

        self.assertEqual(diagnostic["status"], "person_detected_but_not_floor_stay_candidate")
        self.assertEqual(diagnostic["required_dwell_seconds"], 8.0)
        self.assertEqual(diagnostic["selected_track_id"], None)
        self.assertEqual(len(diagnostic["people"]), 1)
        self.assertTrue(diagnostic["people"][0]["in_floor_zone"])
        self.assertFalse(diagnostic["people"][0]["low_posture"])


if __name__ == "__main__":
    unittest.main()
