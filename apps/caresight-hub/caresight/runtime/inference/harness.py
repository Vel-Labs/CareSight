from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .adapter import Yolo26MlxAdapter
from .config import InferenceRuntimeConfig
from .types import Detection, Observation, normalize_detections


@dataclass(frozen=True)
class InferenceRunResult:
    detections: list[Detection]
    observations: list[Observation]
    config: InferenceRuntimeConfig

    def to_dict(self) -> dict[str, Any]:
        return {
            "detections": [detection.to_dict() for detection in self.detections],
            "observations": [observation.to_dict() for observation in self.observations],
            "metadata": self.config.to_dict(),
        }


class CareSightInferenceHarness:
    def __init__(self, config: InferenceRuntimeConfig, adapter: Yolo26MlxAdapter | None = None) -> None:
        self.config = config
        self.adapter = adapter or Yolo26MlxAdapter(config.model)

    @classmethod
    def from_config_path(cls, path: str | Path) -> "CareSightInferenceHarness":
        return cls(InferenceRuntimeConfig.load(path))

    def run(self, image: Any) -> InferenceRunResult:
        detections = self.adapter.predict(image, camera=self.config.camera)
        observations = normalize_detections(
            detections,
            camera=self.config.camera,
            room=self.config.room,
        )
        return InferenceRunResult(
            detections=detections,
            observations=observations,
            config=self.config,
        )
