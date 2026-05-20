from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from caresight.vision.coco import coco_name

from .config import ModelMetadata
from .types import CameraMetadata, Detection, BoundingBox, utc_now_iso


class InferenceError(RuntimeError):
    pass


class InferenceUnavailableError(InferenceError):
    pass


class ModelLoadError(InferenceUnavailableError):
    pass


class Yolo26MlxAdapter:
    def __init__(self, model: ModelMetadata) -> None:
        self.model = model
        self._runner: Any | None = None

    def load(self) -> None:
        model_path = Path(self.model.model_path)
        if not model_path.exists():
            raise ModelLoadError(f"YOLO26 MLX model file not found: {model_path}")
        try:
            from yolo26mlx import YOLO
        except ImportError as error:
            raise ModelLoadError("yolo26mlx is not importable in this environment") from error

        try:
            self._runner = YOLO(str(model_path))
        except Exception as error:  # pragma: no cover - depends on MLX runtime internals.
            raise ModelLoadError(f"YOLO26 MLX model failed to load: {error}") from error

    def predict(self, image: Any, *, camera: CameraMetadata) -> list[Detection]:
        if self._runner is None:
            self.load()
        if self._runner is None:
            raise InferenceUnavailableError("YOLO26 MLX runner is unavailable")

        try:
            results = self._runner.predict(image, conf=self.model.confidence_threshold)
        except Exception as error:  # pragma: no cover - depends on MLX runtime internals.
            raise InferenceUnavailableError(f"YOLO26 MLX prediction failed: {error}") from error

        frame_width, frame_height = frame_dimensions(image, camera)
        captured_at = utc_now_iso()
        return parse_yolo_result(
            results[0],
            model_id=self.model.model_id,
            camera_id=camera.camera_id,
            frame_width=frame_width,
            frame_height=frame_height,
            captured_at=captured_at,
        )


def frame_dimensions(image: Any, camera: CameraMetadata) -> tuple[int, int]:
    shape = getattr(image, "shape", None)
    if shape is not None and len(shape) >= 2:
        return int(shape[1]), int(shape[0])
    return camera.width, camera.height


def parse_yolo_result(
    result: Any,
    *,
    model_id: str,
    camera_id: str,
    frame_width: int,
    frame_height: int,
    captured_at: str,
) -> list[Detection]:
    boxes = getattr(result, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return []

    names = getattr(result, "names", {})
    detections: list[Detection] = []
    for index, (box, confidence, class_id) in enumerate(
        zip(boxes.xyxy, boxes.conf, boxes.cls, strict=False)
    ):
        cls = int(_scalar(class_id))
        detections.append(
            Detection(
                detection_id=f"{camera_id}_{captured_at}_{index}",
                model_id=model_id,
                class_id=cls,
                label=class_name(names, cls),
                confidence=float(_scalar(confidence)),
                bbox=BoundingBox(*[float(value) for value in _sequence(box)]),
                frame_width=frame_width,
                frame_height=frame_height,
                camera_id=camera_id,
                captured_at=captured_at,
                raw_index=index,
            )
        )
    return detections


def class_name(names: Any, class_id: int) -> str:
    fallback = coco_name(class_id)
    if isinstance(names, dict):
        name = str(names.get(class_id, names.get(str(class_id), fallback)))
        return fallback if is_placeholder_name(name) else name
    if isinstance(names, list | tuple) and 0 <= class_id < len(names):
        name = str(names[class_id])
        return fallback if is_placeholder_name(name) else name
    return fallback


def is_placeholder_name(name: str) -> bool:
    return re.fullmatch(r"(?i)class[_ -]?\d+", name.strip()) is not None


def _scalar(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    return value


def _sequence(value: Any) -> list[Any]:
    if hasattr(value, "tolist"):
        return list(value.tolist())
    return list(value)
