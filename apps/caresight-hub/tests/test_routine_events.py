from datetime import UTC, datetime
import unittest

from caresight.events.routine import RoutineEventDetector
from caresight.runtime.config import CareSightConfig
from caresight.vision.detections import Detection


class RoutineEventDetectorTest(unittest.TestCase):
    def test_medication_routine_likely_observed_needs_person_object_and_window(self) -> None:
        detector = RoutineEventDetector(CareSightConfig.default())

        events = detector.update(
            [
                detection("person", 0.91, (360, 320, 640, 680)),
                detection("bottle", 0.82, (700, 360, 760, 620)),
            ],
            now=datetime(2026, 5, 18, 8, 30, tzinfo=UTC),
        )

        medication = [event for event in events if event["event_type"] == "medication_routine_likely_observed"]
        self.assertEqual(len(medication), 1)
        event = medication[0]
        self.assertEqual(event["status"], "awaiting_human_confirmation")
        self.assertTrue(event["requires_human_confirmation"])
        self.assertEqual(event["evidence"]["object_label"], "bottle")
        self.assertEqual(event["evidence"]["wording"], "likely observed")
        self.assertIn("specific_medication_taken", event["evidence"]["not_claimed"])
        self.assertIn("medication_confirmed_without_authorized_human", event["blocked_actions"])

    def test_hydration_routine_likely_observed_accepts_cup_label(self) -> None:
        detector = RoutineEventDetector(CareSightConfig.default())

        events = detector.update(
            [
                detection("person", 0.91, (360, 320, 640, 680)),
                detection("cup", 0.84, (700, 360, 760, 620)),
            ],
            now=datetime(2026, 5, 18, 18, 30, tzinfo=UTC),
        )

        hydration = [event for event in events if event["event_type"] == "hydration_routine_likely_observed"]
        self.assertEqual(len(hydration), 1)
        self.assertEqual(hydration[0]["evidence"]["object_label"], "cup")
        self.assertEqual(hydration[0]["status"], "awaiting_human_confirmation")

    def test_routine_does_not_emit_outside_window_or_without_object(self) -> None:
        detector = RoutineEventDetector(CareSightConfig.default())

        outside_window = detector.update(
            [
                detection("person", 0.91, (360, 320, 640, 680)),
                detection("bottle", 0.82, (700, 360, 760, 620)),
            ],
            now=datetime(2026, 5, 18, 3, 30, tzinfo=UTC),
        )
        missing_object = detector.update(
            [detection("person", 0.91, (360, 320, 640, 680))],
            now=datetime(2026, 5, 18, 8, 30, tzinfo=UTC),
        )

        self.assertEqual(outside_window, [])
        self.assertEqual(missing_object, [])


def detection(label: str, confidence: float, bbox: tuple[float, float, float, float]) -> Detection:
    return Detection(
        class_name=label,
        confidence=confidence,
        bbox_xyxy=bbox,
        frame_width=1280,
        frame_height=720,
    )


if __name__ == "__main__":
    unittest.main()
