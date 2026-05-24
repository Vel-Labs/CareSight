import unittest
from dataclasses import replace

from caresight.events.floor_stay import FloorStayDetector
from caresight.runtime.config import CareSightConfig, ZoneConfig
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
        self.assertEqual(event["evidence"]["escalation_stage"], "early_concern")
        self.assertEqual(event["evidence"]["same_track_dwell_seconds"], 9.0)
        self.assertEqual(event["evidence"]["occlusion_grace_seconds"], 5.0)
        self.assertEqual(event["evidence"]["dedupe_window_seconds"], 90.0)
        self.assertEqual(event["evidence"]["policy_version"], "floor_stay_v1_tracking_reliability")
        self.assertEqual(
            event["evidence"]["not_claimed"],
            [
                "fall_confirmed",
                "injury_detected",
                "medical_emergency",
                "sitting_on_floor_not_floor_stay_by_itself",
            ],
        )

    def test_emits_prolonged_and_critical_escalation_stages_from_same_track_dwell(self) -> None:
        config = replace(
            CareSightConfig.default(),
            floor_stay=replace(
                CareSightConfig.default().floor_stay,
                dwell_seconds=30.0,
                prolonged_dwell_seconds=90.0,
                critical_dwell_seconds=180.0,
            ),
        )
        detector = FloorStayDetector(config)
        detection = Detection(
            class_name="person",
            confidence=0.91,
            bbox_xyxy=(200, 430, 1080, 715),
            frame_width=1280,
            frame_height=720,
        )

        detector.update([detection], now=100.0)
        prolonged = detector.update([detection], now=191.0)
        detector.update([], now=300.0)
        detector.update([detection], now=500.0)
        critical = detector.update([detection], now=681.0)

        self.assertIsNotNone(prolonged)
        self.assertIsNotNone(critical)
        assert prolonged is not None
        assert critical is not None
        self.assertEqual(prolonged["evidence"]["escalation_stage"], "prolonged_concern")
        self.assertEqual(critical["evidence"]["escalation_stage"], "critical_attention")

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

    def test_different_track_cannot_inherit_floor_stay_dwell_when_same_track_required(self) -> None:
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

        self.assertIsNone(event)
        diagnostic = detector.diagnostic()
        self.assertEqual(diagnostic["selected_track_id"], "track_2")
        self.assertEqual(diagnostic["people"][0]["dwell_seconds"], 0.0)

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
        detector.update([], now=106.0)
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
        detector.update([], now=120.0)
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

    def test_seated_on_floor_is_labeled_but_does_not_emit_floor_stay(self) -> None:
        config = CareSightConfig.default()
        detector = FloorStayDetector(config)
        detection = Detection(
            class_name="person",
            confidence=0.95,
            bbox_xyxy=(440, 360, 760, 715),
            frame_width=1280,
            frame_height=720,
        )

        detector.update([detection], now=100.0)
        event = detector.update([detection], now=109.0)

        self.assertIsNone(event)
        diagnostic = detector.diagnostic()
        self.assertEqual(diagnostic["people"][0]["posture_label"], "seated_on_floor_possible")
        self.assertFalse(diagnostic["people"][0]["floor_stay_eligible"])

    def test_laying_low_candidate_reports_posture_and_active_dwell(self) -> None:
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
        detector.update([detection], now=104.0)
        diagnostic = detector.diagnostic()

        self.assertEqual(diagnostic["status"], "floor_stay_candidate_tracking")
        self.assertEqual(diagnostic["people"][0]["posture_label"], "laying_low_possible")
        self.assertTrue(diagnostic["people"][0]["floor_stay_eligible"])
        self.assertEqual(diagnostic["people"][0]["dwell_seconds"], 4.0)

    def test_floor_stay_event_evidence_includes_posture_boundary(self) -> None:
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
        event = detector.update([detection], now=109.0)

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event["evidence"]["posture_label"], "laying_low_possible")
        self.assertEqual(event["evidence"]["posture_basis"], "yolo_box_geometry")
        self.assertIn("sitting_on_floor_not_floor_stay_by_itself", event["evidence"]["not_claimed"])

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

    def test_complexity_grade_far_small_low_posture_can_emit_bounded_event(self) -> None:
        config = CareSightConfig.default()
        detector = FloorStayDetector(config)
        detection = Detection(
            class_name="person",
            confidence=0.46,
            bbox_xyxy=(760, 600, 1040, 700),
            frame_width=1280,
            frame_height=720,
        )

        detector.update([detection], now=100.0)
        event = detector.update([detection], now=109.0)

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event["event_type"], "possible_floor_stay")
        self.assertEqual(event["evidence"]["escalation_stage"], "early_concern")
        self.assertEqual(event["evidence"]["detection_confidence"], 0.46)
        self.assertIn("fall_confirmed", event["evidence"]["not_claimed"])

    def test_complexity_grade_multiple_people_uses_floor_candidate_not_standing_person(self) -> None:
        config = CareSightConfig.default()
        detector = FloorStayDetector(config)
        standing = Detection(
            class_name="person",
            confidence=0.98,
            bbox_xyxy=(260, 80, 520, 700),
            frame_width=1280,
            frame_height=720,
        )
        low_posture = Detection(
            class_name="person",
            confidence=0.74,
            bbox_xyxy=(560, 545, 1180, 710),
            frame_width=1280,
            frame_height=720,
        )

        detector.update([standing, low_posture], now=100.0)
        event = detector.update([standing, low_posture], now=109.0)

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event["evidence"]["detection_confidence"], 0.74)
        diagnostic = detector.diagnostic()
        selected = [
            person for person in diagnostic["people"]
            if person["track_id"] == diagnostic["selected_track_id"]
        ][0]
        self.assertTrue(selected["low_posture"])
        self.assertTrue(selected["in_floor_zone"])

    def test_complexity_grade_far_standing_person_remains_non_event(self) -> None:
        config = CareSightConfig.default()
        detector = FloorStayDetector(config)
        detection = Detection(
            class_name="person",
            confidence=0.88,
            bbox_xyxy=(900, 120, 1050, 700),
            frame_width=1280,
            frame_height=720,
        )

        detector.update([detection], now=100.0)
        event = detector.update([detection], now=109.0)

        self.assertIsNone(event)
        diagnostic = detector.diagnostic()
        self.assertEqual(diagnostic["status"], "person_detected_but_not_floor_stay_candidate")
        self.assertFalse(diagnostic["people"][0]["low_posture"])

    def test_calibrated_polygon_floor_zone_excludes_non_floor_area_inside_rectangle(self) -> None:
        config = replace(
            CareSightConfig.default(),
            floor_zone=ZoneConfig(
                zone_id="floor_zone",
                camera_id="living_room",
                name="Calibrated Floor Plane",
                kind="floor_low",
                x_min=0.0,
                y_min=0.45,
                x_max=1.0,
                y_max=1.0,
                vertices=((0.25, 0.55), (0.75, 0.55), (1.0, 1.0), (0.0, 1.0)),
            ),
        )
        detector = FloorStayDetector(config)
        outside_polygon = Detection(
            class_name="person",
            confidence=0.91,
            bbox_xyxy=(0, 400, 300, 530),
            frame_width=1280,
            frame_height=720,
        )
        inside_polygon = Detection(
            class_name="person",
            confidence=0.91,
            bbox_xyxy=(300, 430, 980, 715),
            frame_width=1280,
            frame_height=720,
        )

        detector.update([outside_polygon], now=100.0)
        self.assertIsNone(detector.update([outside_polygon], now=109.0))
        diagnostic = detector.diagnostic()
        self.assertFalse(diagnostic["people"][0]["in_floor_zone"])

        detector = FloorStayDetector(config)
        detector.update([inside_polygon], now=100.0)
        event = detector.update([inside_polygon], now=109.0)

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event["evidence"]["zone_shape"], "polygon")
        self.assertEqual(len(event["evidence"]["zone_vertices"]), 4)


if __name__ == "__main__":
    unittest.main()
