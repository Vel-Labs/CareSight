import tempfile
import unittest
from pathlib import Path

from caresight.runtime.inference import (
    BoundingBox,
    CareSightInferenceHarness,
    CameraMetadata,
    Detection,
    InferenceRuntimeConfig,
    RoomMetadata,
    normalize_detections,
)
from caresight.runtime.inference.adapter import ModelLoadError, Yolo26MlxAdapter, parse_yolo_result


class InferenceHarnessTest(unittest.TestCase):
    def test_config_loads_model_camera_and_room_metadata(self) -> None:
        config = InferenceRuntimeConfig.load(
            Path(__file__).resolve().parents[1] / "config" / "v0.local.json"
        )

        self.assertEqual(config.model.model_id, "yolo26n")
        self.assertEqual(config.model.adapter, "yolo26_mlx")
        self.assertEqual(config.camera.camera_id, "living_room")
        self.assertEqual(config.room.room_id, "living_room")

    def test_missing_model_fails_closed_before_importing_yolo(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_model = Path(tmpdir) / "missing.npz"
            adapter = Yolo26MlxAdapter(
                InferenceRuntimeConfig.from_dict(
                    {
                        "camera": _camera().to_dict(),
                        "room": _room().to_dict(),
                        "inference": {
                            "model_id": "missing",
                            "model_name": "Missing",
                            "model_path": str(missing_model),
                            "adapter": "yolo26_mlx",
                            "confidence_threshold": 0.25,
                        },
                    }
                ).model
            )

            with self.assertRaises(ModelLoadError):
                adapter.load()

    def test_no_boxes_return_no_detections_or_observations(self) -> None:
        class EmptyBoxes:
            def __len__(self) -> int:
                return 0

        class EmptyResult:
            boxes = EmptyBoxes()
            names = {0: "person"}

        detections = parse_yolo_result(
            EmptyResult(),
            model_id="yolo26n",
            camera_id="living_room",
            frame_width=1280,
            frame_height=720,
            captured_at="2026-05-19T00:00:00Z",
        )

        self.assertEqual(detections, [])
        self.assertEqual(normalize_detections(detections, camera=_camera(), room=_room()), [])

    def test_harness_separates_raw_detections_from_normalized_observations(self) -> None:
        config = InferenceRuntimeConfig.from_dict(
            {
                "camera": _camera().to_dict(),
                "room": _room().to_dict(),
                "inference": {
                    "model_id": "test-model",
                    "model_name": "Test Model",
                    "model_path": "unused.npz",
                    "adapter": "test",
                    "confidence_threshold": 0.25,
                },
            }
        )
        harness = CareSightInferenceHarness(config, adapter=StaticAdapter())

        result = harness.run(image=object())

        self.assertEqual(len(result.detections), 1)
        self.assertEqual(result.detections[0].bbox.x_min, 320)
        self.assertEqual(len(result.observations), 1)
        self.assertEqual(result.observations[0].observation_type, "person_likely_observed")
        self.assertEqual(result.observations[0].class_id, 0)
        self.assertEqual(result.observations[0].bbox_normalized.x_min, 0.25)
        self.assertEqual(result.observations[0].camera.name, "Living Room")
        self.assertEqual(result.observations[0].room.name, "Living Room")

    def test_placeholder_model_names_fall_back_to_coco_labels(self) -> None:
        class Boxes:
            xyxy = [(0, 0, 100, 100), (10, 10, 200, 200)]
            conf = [0.92, 0.91]
            cls = [0, 5]

            def __len__(self) -> int:
                return 2

        class PlaceholderResult:
            boxes = Boxes()
            names = {0: "class0", 5: "class5"}

        detections = parse_yolo_result(
            PlaceholderResult(),
            model_id="yolo26n",
            camera_id="living_room",
            frame_width=1280,
            frame_height=720,
            captured_at="2026-05-20T00:00:00Z",
        )
        observations = normalize_detections(detections, camera=_camera(), room=_room())

        self.assertEqual(detections[0].label, "person")
        self.assertEqual(detections[1].label, "bus")
        self.assertEqual(observations[0].observation_type, "person_likely_observed")
        self.assertEqual(observations[1].observation_type, "bus_likely_observed")
        self.assertEqual(observations[0].class_id, 0)


class StaticAdapter:
    def predict(self, image, *, camera: CameraMetadata) -> list[Detection]:
        return [
            Detection(
                detection_id="det_1",
                model_id="test-model",
                class_id=0,
                label="person",
                confidence=0.91,
                bbox=BoundingBox(320, 360, 640, 720),
                frame_width=camera.width,
                frame_height=camera.height,
                camera_id=camera.camera_id,
                captured_at="2026-05-19T00:00:00Z",
                raw_index=0,
            )
        ]


def _camera() -> CameraMetadata:
    return CameraMetadata(
        camera_id="living_room",
        name="Living Room",
        source_type="webcam",
        source_uri=0,
        width=1280,
        height=720,
        fps=30,
    )


def _room() -> RoomMetadata:
    return RoomMetadata(room_id="living_room", name="Living Room", floor="main")


if __name__ == "__main__":
    unittest.main()
