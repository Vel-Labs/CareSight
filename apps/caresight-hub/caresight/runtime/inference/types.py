from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import re
from typing import Any


@dataclass(frozen=True)
class BoundingBox:
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    def normalized(self, width: int, height: int) -> "BoundingBox":
        if width <= 0 or height <= 0:
            raise ValueError("frame dimensions must be positive")
        return BoundingBox(
            x_min=max(0.0, min(1.0, self.x_min / width)),
            y_min=max(0.0, min(1.0, self.y_min / height)),
            x_max=max(0.0, min(1.0, self.x_max / width)),
            y_max=max(0.0, min(1.0, self.y_max / height)),
        )

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class CameraMetadata:
    camera_id: str
    name: str
    source_type: str
    source_uri: int | str
    width: int
    height: int
    fps: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RoomMetadata:
    room_id: str
    name: str
    floor: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Detection:
    detection_id: str
    model_id: str
    class_id: int
    label: str
    confidence: float
    bbox: BoundingBox
    frame_width: int
    frame_height: int
    camera_id: str
    captured_at: str
    raw_index: int

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["bbox"] = self.bbox.to_dict()
        return data


@dataclass(frozen=True)
class Observation:
    observation_id: str
    detection_id: str
    observation_type: str
    class_id: int
    label: str
    confidence: float
    bbox_normalized: BoundingBox
    camera: CameraMetadata
    room: RoomMetadata
    captured_at: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["bbox_normalized"] = self.bbox_normalized.to_dict()
        data["camera"] = self.camera.to_dict()
        data["room"] = self.room.to_dict()
        return data


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_detections(
    detections: list[Detection],
    *,
    camera: CameraMetadata,
    room: RoomMetadata,
) -> list[Observation]:
    observations: list[Observation] = []
    for detection in detections:
        if detection.camera_id != camera.camera_id:
            raise ValueError("detection camera_id does not match camera metadata")
        observations.append(
            Observation(
                observation_id=f"obs_{detection.detection_id}",
                detection_id=detection.detection_id,
                observation_type=f"{observation_label(detection.label)}_likely_observed",
                class_id=detection.class_id,
                label=detection.label,
                confidence=detection.confidence,
                bbox_normalized=detection.bbox.normalized(
                    detection.frame_width,
                    detection.frame_height,
                ),
                camera=camera,
                room=room,
                captured_at=detection.captured_at,
            )
        )
    return observations


def observation_label(label: str) -> str:
    normalized = label.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    normalized = normalized.strip("_")
    return normalized or "unknown_object"
