from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class CameraConfig:
    camera_id: str
    name: str
    source_type: str
    source_uri: int | str
    width: int
    height: int
    fps: int


@dataclass(frozen=True)
class ZoneConfig:
    zone_id: str
    camera_id: str
    name: str
    kind: str
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    def contains_normalized_point(self, x: float, y: float) -> bool:
        return self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max


@dataclass(frozen=True)
class FloorStayConfig:
    dwell_seconds: float
    severity: str
    confidence: str


@dataclass(frozen=True)
class StorageConfig:
    database_path: str


@dataclass(frozen=True)
class CareSightConfig:
    camera: CameraConfig
    floor_zone: ZoneConfig
    floor_stay: FloorStayConfig
    storage: StorageConfig

    @classmethod
    def default(cls) -> "CareSightConfig":
        return cls(
            camera=CameraConfig(
                camera_id="living_room",
                name="Living Room",
                source_type="webcam",
                source_uri=0,
                width=1280,
                height=720,
                fps=30,
            ),
            floor_zone=ZoneConfig(
                zone_id="floor_zone",
                camera_id="living_room",
                name="Floor / Low Zone",
                kind="floor_low",
                x_min=0.0,
                y_min=0.66,
                x_max=1.0,
                y_max=1.0,
            ),
            floor_stay=FloorStayConfig(
                dwell_seconds=8.0,
                severity="high",
                confidence="high",
            ),
            storage=StorageConfig(
                database_path="apps/caresight-hub/data/caresight-v0.sqlite3",
            ),
        )

    @classmethod
    def load(cls, path: str | Path) -> "CareSightConfig":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> "CareSightConfig":
        return cls(
            camera=CameraConfig(**data["camera"]),
            floor_zone=ZoneConfig(**data["floor_zone"]),
            floor_stay=FloorStayConfig(**data["floor_stay"]),
            storage=StorageConfig(**data["storage"]),
        )

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")

    def to_dict(self) -> dict:
        return asdict(self)
