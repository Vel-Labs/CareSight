from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .types import CameraMetadata, RoomMetadata


@dataclass(frozen=True)
class ModelMetadata:
    model_id: str
    model_name: str
    model_path: str
    adapter: str
    confidence_threshold: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "model_name": self.model_name,
            "model_path": self.model_path,
            "adapter": self.adapter,
            "confidence_threshold": self.confidence_threshold,
        }


@dataclass(frozen=True)
class InferenceRuntimeConfig:
    model: ModelMetadata
    camera: CameraMetadata
    room: RoomMetadata

    @classmethod
    def load(cls, path: str | Path) -> "InferenceRuntimeConfig":
        config_path = Path(path)
        data = json.loads(config_path.read_text(encoding="utf-8"))
        config = cls.from_dict(data)
        model_path = Path(config.model.model_path)
        if model_path.is_absolute() or model_path.exists():
            return config

        resolved = _resolve_existing_parent_relative_path(config_path, model_path)
        if resolved is None:
            return config
        return cls(
            model=ModelMetadata(
                model_id=config.model.model_id,
                model_name=config.model.model_name,
                model_path=str(resolved),
                adapter=config.model.adapter,
                confidence_threshold=config.model.confidence_threshold,
            ),
            camera=config.camera,
            room=config.room,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InferenceRuntimeConfig":
        inference = data.get("inference")
        room = data.get("room")
        if not isinstance(inference, dict):
            raise ValueError("config must include top-level inference metadata")
        if not isinstance(room, dict):
            raise ValueError("config must include top-level room metadata")

        return cls(
            model=ModelMetadata(
                model_id=str(inference["model_id"]),
                model_name=str(inference["model_name"]),
                model_path=str(inference["model_path"]),
                adapter=str(inference.get("adapter", "yolo26_mlx")),
                confidence_threshold=float(inference.get("confidence_threshold", 0.25)),
            ),
            camera=CameraMetadata(**data["camera"]),
            room=RoomMetadata(
                room_id=str(room["room_id"]),
                name=str(room["name"]),
                floor=room.get("floor"),
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "inference": self.model.to_dict(),
            "camera": self.camera.to_dict(),
            "room": self.room.to_dict(),
        }


def _resolve_existing_parent_relative_path(config_path: Path, relative_path: Path) -> Path | None:
    for parent in config_path.resolve().parents:
        candidate = parent / relative_path
        if candidate.exists():
            return candidate
    return None
