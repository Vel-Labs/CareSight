from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from caresight.runtime.appearance import (
    AppearanceProfile,
    extract_appearance_descriptor,
    match_profile_continuity,
    render_appearance_summary,
    score_appearance_sample,
    summarize_appearance_samples,
)


class AppearanceDescriptorTest(unittest.TestCase):
    def test_extracts_clothing_colors_from_generated_image_bbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = Path(tmpdir) / "person.ppm"
            write_ppm(
                image_path,
                width=100,
                height=100,
                fills=[
                    ((20, 20, 80, 65), (45, 45, 45)),
                    ((20, 65, 80, 90), (42, 96, 180)),
                ],
            )

            descriptor = extract_appearance_descriptor(
                snapshot_path=str(image_path),
                bbox_xyxy=(20, 20, 80, 90),
                event_id="evt_generated",
                observation_id="obs_generated",
            )

            self.assertEqual(descriptor.descriptor_status, "available")
            self.assertEqual(descriptor.upper_body_color.value, "dark gray")
            self.assertEqual(descriptor.lower_body_color.value, "blue")
            self.assertEqual(descriptor.descriptor_source, "runtime_observation")
            self.assertEqual(descriptor.snapshot_path, str(image_path))
            self.assertEqual(descriptor.event_id, "evt_generated")
            self.assertEqual(descriptor.observation_id, "obs_generated")

    def test_generated_images_prove_descriptor_is_not_hard_coded(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            first = Path(tmpdir) / "first.ppm"
            second = Path(tmpdir) / "second.ppm"
            write_ppm(first, 80, 80, [((10, 10, 70, 48), (190, 32, 32)), ((10, 48, 70, 72), (40, 130, 60))])
            write_ppm(second, 80, 80, [((10, 10, 70, 48), (220, 180, 35)), ((10, 48, 70, 72), (95, 58, 32))])

            first_descriptor = extract_appearance_descriptor(snapshot_path=str(first), bbox_xyxy=(10, 10, 70, 72))
            second_descriptor = extract_appearance_descriptor(snapshot_path=str(second), bbox_xyxy=(10, 10, 70, 72))

            self.assertEqual(first_descriptor.upper_body_color.value, "red")
            self.assertEqual(first_descriptor.lower_body_color.value, "green")
            self.assertEqual(second_descriptor.upper_body_color.value, "yellow")
            self.assertEqual(second_descriptor.lower_body_color.value, "brown")

    def test_extracts_headwear_and_footwear_from_generated_image_bbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = Path(tmpdir) / "accessories.ppm"
            write_ppm(
                image_path,
                width=100,
                height=100,
                fills=[
                    ((42, 22, 58, 31), (20, 20, 20)),
                    ((38, 47, 62, 63), (42, 96, 180)),
                    ((38, 63, 62, 83), (245, 248, 248)),
                    ((42, 84, 58, 89), (245, 248, 248)),
                ],
            )

            descriptor = extract_appearance_descriptor(
                snapshot_path=str(image_path),
                bbox_xyxy=(20, 20, 80, 90),
            )

            self.assertEqual(descriptor.descriptor_status, "available")
            self.assertEqual(descriptor.upper_body_color.value, "blue")
            self.assertEqual(descriptor.lower_body_color.value, "white")
            self.assertEqual(descriptor.headwear.value, "black")
            self.assertEqual(descriptor.footwear.value, "white")

    def test_truncated_wide_event_bbox_samples_torso_and_marks_lower_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = Path(tmpdir) / "truncated.ppm"
            write_ppm(
                image_path,
                width=128,
                height=72,
                fills=[
                    ((0, 0, 128, 72), (214, 207, 190)),
                    ((64, 0, 128, 50), (245, 248, 248)),
                    ((42, 28, 68, 42), (18, 20, 25)),
                    ((40, 42, 70, 55), (150, 112, 100)),
                    ((30, 54, 82, 72), (58, 74, 96)),
                ],
            )

            descriptor = extract_appearance_descriptor(
                snapshot_path=str(image_path),
                bbox_xyxy=(0, 28, 94, 72),
            )

            self.assertEqual(descriptor.descriptor_status, "available")
            self.assertEqual(descriptor.upper_body_color.value, "blue")
            self.assertEqual(descriptor.lower_body_color.value, "unknown")

    def test_wide_prone_bottom_truncated_bbox_returns_no_hallucinated_descriptor(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = Path(tmpdir) / "prone.ppm"
            write_ppm(
                image_path,
                width=128,
                height=72,
                fills=[
                    ((0, 0, 128, 72), (140, 130, 115)),
                    ((62, 50, 95, 72), (245, 235, 210)),
                    ((90, 48, 128, 72), (58, 74, 96)),
                ],
            )

            descriptor = extract_appearance_descriptor(
                snapshot_path=str(image_path),
                bbox_xyxy=(47, 49, 128, 72),
            )

            self.assertEqual(descriptor.descriptor_status, "unavailable")
            self.assertEqual(descriptor.upper_body_color.value, "unknown")
            self.assertEqual(descriptor.lower_body_color.value, "unknown")

    def test_missing_or_unreadable_image_returns_no_hallucinated_descriptor(self) -> None:
        descriptor = extract_appearance_descriptor(
            snapshot_path="/tmp/caresight-missing-appearance-image.ppm",
            bbox_xyxy=(10, 10, 30, 40),
        )

        self.assertEqual(descriptor.descriptor_status, "unreadable")
        self.assertEqual(descriptor.upper_body_color.value, "unknown")
        self.assertEqual(descriptor.lower_body_color.value, "unknown")

    def test_invalid_bbox_returns_no_hallucinated_descriptor(self) -> None:
        frame = [[(35, 35, 35) for _ in range(20)] for _ in range(20)]

        descriptor = extract_appearance_descriptor(frame=frame, bbox_xyxy=(15, 15, 15, 18))

        self.assertEqual(descriptor.descriptor_status, "invalid_bbox")
        self.assertEqual(descriptor.upper_body_color.value, "unknown")
        self.assertEqual(descriptor.lower_body_color.value, "unknown")

    def test_sample_quality_accepts_confident_clothing_and_rejects_prone_unknown(self) -> None:
        accepted = extract_appearance_descriptor(
            frame=solid_person_frame((42, 96, 180), (245, 235, 210)),
            bbox_xyxy=(10, 10, 50, 70),
        )
        accepted_quality = score_appearance_sample(
            descriptor=accepted,
            bbox_xyxy=(10, 10, 50, 70),
            frame_width=60,
            frame_height=80,
            detection_confidence=0.92,
        )

        rejected = extract_appearance_descriptor(
            frame=solid_person_frame((42, 96, 180), (245, 235, 210)),
            bbox_xyxy=(0, 58, 59, 80),
        )
        rejected_quality = score_appearance_sample(
            descriptor=rejected,
            bbox_xyxy=(0, 58, 59, 80),
            frame_width=60,
            frame_height=80,
            detection_confidence=0.56,
        )

        self.assertTrue(accepted_quality.accepted)
        self.assertGreaterEqual(accepted_quality.score, 0.62)
        self.assertFalse(rejected_quality.accepted)
        self.assertIn("descriptor_unavailable", rejected_quality.reasons)


class AppearanceContinuityTest(unittest.TestCase):
    def test_same_track_same_day_caps_at_085(self) -> None:
        profile = profile_fixture(track_id="track_7", camera_id="living_room", role_assignment="resident_primary")
        descriptor = extract_appearance_descriptor(
            frame=solid_person_frame((42, 42, 42), (42, 96, 180)),
            bbox_xyxy=(10, 10, 50, 70),
        )

        match = match_profile_continuity(
            profile,
            descriptor,
            observed_at=datetime(2026, 5, 22, 16, 0, tzinfo=timezone.utc),
            track_id="track_7",
            camera_id="living_room",
            role_assignment="resident_primary",
        )

        self.assertTrue(match.matched)
        self.assertEqual(match.confidence, 0.85)
        self.assertEqual(match.reason, "same_track_same_day")

    def test_clothing_only_same_camera_caps_at_065_and_cross_camera_caps_at_055(self) -> None:
        profile = profile_fixture(track_id="track_7", camera_id="living_room")
        descriptor = extract_appearance_descriptor(
            frame=solid_person_frame((42, 42, 42), (42, 96, 180)),
            bbox_xyxy=(10, 10, 50, 70),
        )

        same_camera = match_profile_continuity(
            profile,
            descriptor,
            observed_at=datetime(2026, 5, 22, 16, 0, tzinfo=timezone.utc),
            camera_id="living_room",
        )
        cross_camera = match_profile_continuity(
            profile,
            descriptor,
            observed_at=datetime(2026, 5, 22, 16, 0, tzinfo=timezone.utc),
            camera_id="kitchen",
        )

        self.assertEqual(same_camera.confidence, 0.65)
        self.assertEqual(cross_camera.confidence, 0.55)

    def test_expired_or_cross_day_profile_is_no_match(self) -> None:
        profile = profile_fixture(track_id="track_7", expires_at="2026-05-23T04:00:00Z")
        descriptor = extract_appearance_descriptor(
            frame=solid_person_frame((42, 42, 42), (42, 96, 180)),
            bbox_xyxy=(10, 10, 50, 70),
        )

        match = match_profile_continuity(
            profile,
            descriptor,
            observed_at=datetime(2026, 5, 23, 5, 0, tzinfo=timezone.utc),
            track_id="track_7",
            camera_id="living_room",
        )

        self.assertFalse(match.matched)
        self.assertEqual(match.confidence, 0.0)
        self.assertEqual(match.reason, "expired_profile")

    def test_conflicting_role_caps_at_040(self) -> None:
        profile = profile_fixture(track_id="track_7", role_assignment="resident_primary")
        descriptor = extract_appearance_descriptor(
            frame=solid_person_frame((42, 42, 42), (42, 96, 180)),
            bbox_xyxy=(10, 10, 50, 70),
        )

        match = match_profile_continuity(
            profile,
            descriptor,
            observed_at=datetime(2026, 5, 22, 16, 0, tzinfo=timezone.utc),
            track_id="track_7",
            camera_id="living_room",
            role_assignment="visitor_unknown",
        )

        self.assertTrue(match.matched)
        self.assertEqual(match.confidence, 0.4)
        self.assertEqual(match.reason, "conflicting_role")


class AppearanceRenderTest(unittest.TestCase):
    def test_render_uses_bounded_non_identity_language(self) -> None:
        profile = profile_fixture(
            role_assignment="resident_primary",
            room="Living Room",
            upper_body_color="dark gray",
            lower_body_color="blue",
        )

        summary = render_appearance_summary(profile)

        self.assertIn("resident-assigned profile for today", summary)
        self.assertIn("dark gray upper clothing", summary)
        self.assertIn("last seen in Living Room", summary)
        forbidden = ["identity", "identified", "face", "facial", "biometric", "Steven", "diagnosed"]
        for term in forbidden:
            self.assertNotIn(term, summary)

    def test_sample_summary_reports_support_ratios_without_identity_claims(self) -> None:
        samples = [
            sample_fixture("sample_1", upper="blue", lower="white", headwear="black", footwear="white", quality_score=0.82),
            sample_fixture("sample_2", upper="blue", lower="white", headwear="black", footwear="white", quality_score=0.78),
            sample_fixture("sample_3", upper="gray", lower="unknown", headwear="unknown", footwear="unknown", quality_score=0.70),
            sample_fixture("sample_4", upper="red", lower="black", headwear="blue", footwear="black", quality_score=0.40),
        ]

        summary = summarize_appearance_samples(samples)

        self.assertEqual(summary["upper_body_color"]["value"], "blue")
        self.assertEqual(summary["upper_body_color"]["support_count"], 2)
        self.assertEqual(summary["upper_body_color"]["total_good_samples"], 3)
        self.assertEqual(summary["lower_body_color"]["value"], "white")
        self.assertEqual(summary["headwear"]["value"], "black")
        self.assertEqual(summary["footwear"]["value"], "white")
        self.assertIn("no_face_recognition", summary["safety_boundaries"])


def profile_fixture(
    *,
    track_id: str = "track_1",
    camera_id: str = "living_room",
    role_assignment: str = "resident_primary",
    room: str = "Living Room",
    upper_body_color: str = "dark gray",
    lower_body_color: str = "blue",
    expires_at: str = "2026-05-23T04:00:00Z",
) -> AppearanceProfile:
    return AppearanceProfile(
        appearance_profile_id="appearance_2026_05_22_001",
        active_date="2026-05-22",
        expires_at=expires_at,
        role_assignment=role_assignment,
        assignment_source="human_confirmed",
        track_id=track_id,
        upper_body_color=upper_body_color,
        lower_body_color=lower_body_color,
        last_seen_camera_id=camera_id,
        last_seen_room=room,
        last_seen_at="2026-05-22T15:30:00Z",
        last_seen_event_id="evt_profile",
    )


def sample_fixture(
    sample_id: str,
    *,
    upper: str,
    lower: str,
    headwear: str = "unknown",
    footwear: str = "unknown",
    quality_score: float,
) -> dict:
    return {
        "sample_id": sample_id,
        "appearance_profile_id": "appearance_2026_05_22_track_1",
        "active_date": "2026-05-22",
        "captured_at": "2026-05-22T15:00:00Z",
        "descriptor_status": "available",
        "quality_score": quality_score,
        "attributes": {
            "upper_body_color": {"value": upper, "confidence": 0.78},
            "lower_body_color": {"value": lower, "confidence": 0.78 if lower != "unknown" else 0.0},
            "headwear": {"value": headwear, "confidence": 0.62 if headwear != "unknown" else 0.0},
            "footwear": {"value": footwear, "confidence": 0.78 if footwear != "unknown" else 0.0},
        },
    }


def solid_person_frame(
    upper_color: tuple[int, int, int],
    lower_color: tuple[int, int, int],
) -> list[list[tuple[int, int, int]]]:
    frame = [[(255, 255, 255) for _ in range(60)] for _ in range(80)]
    for y in range(10, 70):
        for x in range(10, 50):
            frame[y][x] = upper_color if y < 48 else lower_color
    return frame


def write_ppm(
    path: Path,
    width: int,
    height: int,
    fills: list[tuple[tuple[int, int, int, int], tuple[int, int, int]]],
) -> None:
    pixels = [[(255, 255, 255) for _ in range(width)] for _ in range(height)]
    for (x1, y1, x2, y2), color in fills:
        for y in range(y1, y2):
            for x in range(x1, x2):
                pixels[y][x] = color
    data = bytearray(f"P6\n{width} {height}\n255\n".encode("ascii"))
    for row in pixels:
        for red, green, blue in row:
            data.extend(bytes((red, green, blue)))
    path.write_bytes(data)


if __name__ == "__main__":
    unittest.main()
