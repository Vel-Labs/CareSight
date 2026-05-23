from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from caresight.runtime.cameras.sources import validate_camera_source


@dataclass(frozen=True)
class CameraPrivacyConfig:
    raw_video_storage: str = "local_only"
    cloud_upload_default: bool = False


@dataclass(frozen=True)
class CameraConfig:
    camera_id: str
    name: str
    source_type: str
    source_uri: int | str
    width: int
    height: int
    fps: int
    room_id: str | None = None
    room_label: str | None = None
    privacy: CameraPrivacyConfig | dict | None = None
    allow_embedded_credentials: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_type", self.source_type.strip().lower())
        if self.privacy is None:
            object.__setattr__(self, "privacy", CameraPrivacyConfig())
        elif isinstance(self.privacy, dict):
            object.__setattr__(self, "privacy", CameraPrivacyConfig(**self.privacy))
        validate_camera_source(self)


@dataclass(frozen=True)
class RoomConfig:
    room_id: str
    name: str
    floor: str | None = None


@dataclass(frozen=True)
class TrackingConfig:
    occlusion_grace_seconds: float = 5.0
    missing_seconds: float = 120.0
    dedupe_window_seconds: float = 90.0
    same_track_required: bool = True
    min_person_confidence: float = 0.35
    missing_severity: str = "medium"


@dataclass(frozen=True)
class RoutineConfig:
    routine_id: str
    event_type: str
    zone_id: str
    zone_name: str
    object_labels: list[str]
    window_start: str
    window_end: str
    severity: str = "medium"
    confidence: str = "medium"
    x_min: float = 0.0
    y_min: float = 0.0
    x_max: float = 1.0
    y_max: float = 1.0

    def contains_normalized_point(self, x: float, y: float) -> bool:
        return self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max


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
    vertices: tuple[tuple[float, float], ...] = ()

    def __post_init__(self) -> None:
        normalized_vertices = tuple(
            (float(point[0]), float(point[1]))
            for point in self.vertices
        )
        if normalized_vertices and len(normalized_vertices) < 3:
            raise ValueError("zone vertices must contain at least three points")
        object.__setattr__(self, "vertices", normalized_vertices)

    def contains_normalized_point(self, x: float, y: float) -> bool:
        if self.vertices:
            return _point_in_polygon(x, y, self.vertices)
        return self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max

    def normalized_vertices(self) -> tuple[tuple[float, float], ...]:
        if self.vertices:
            return self.vertices
        return (
            (self.x_min, self.y_min),
            (self.x_max, self.y_min),
            (self.x_max, self.y_max),
            (self.x_min, self.y_max),
        )


@dataclass(frozen=True)
class FloorStayConfig:
    dwell_seconds: float = 30.0
    severity: str = "high"
    confidence: str = "high"
    prolonged_dwell_seconds: float = 90.0
    critical_dwell_seconds: float = 180.0


@dataclass(frozen=True)
class StorageConfig:
    database_path: str


@dataclass(frozen=True)
class CareSightConfig:
    camera: CameraConfig
    room: RoomConfig
    floor_zone: ZoneConfig
    floor_stay: FloorStayConfig
    tracking: TrackingConfig
    routines: tuple[RoutineConfig, ...]
    storage: StorageConfig
    cameras: tuple[CameraConfig, ...] = ()
    active_camera_id: str | None = None
    floor_zones: tuple[ZoneConfig, ...] = ()

    @classmethod
    def default(cls) -> "CareSightConfig":
        camera = CameraConfig(
            camera_id="living_room",
            name="Living Room",
            source_type="webcam",
            source_uri=0,
            width=1280,
            height=720,
            fps=30,
            room_id="living_room",
            room_label="Living Room",
        )
        return cls(
            camera=camera,
            room=RoomConfig(room_id="living_room", name="Living Room", floor="main"),
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
            tracking=TrackingConfig(),
            routines=(
                RoutineConfig(
                    routine_id="morning_medication",
                    event_type="medication_routine_likely_observed",
                    zone_id="medication_counter_zone",
                    zone_name="Medication Counter Zone",
                    object_labels=["bottle"],
                    window_start="06:00",
                    window_end="11:00",
                    x_min=0.0,
                    y_min=0.25,
                    x_max=1.0,
                    y_max=1.0,
                ),
                RoutineConfig(
                    routine_id="daytime_hydration",
                    event_type="hydration_routine_likely_observed",
                    zone_id="hydration_zone",
                    zone_name="Hydration Zone",
                    object_labels=["bottle", "cup"],
                    window_start="06:00",
                    window_end="21:00",
                    x_min=0.0,
                    y_min=0.25,
                    x_max=1.0,
                    y_max=1.0,
                ),
            ),
            storage=StorageConfig(
                database_path="apps/caresight-hub/data/caresight-v0.sqlite3",
            ),
            cameras=(camera,),
            active_camera_id=camera.camera_id,
            floor_zones=(),
        )

    @classmethod
    def load(cls, path: str | Path) -> "CareSightConfig":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> "CareSightConfig":
        camera = CameraConfig(**data["camera"])
        cameras = tuple(CameraConfig(**item) for item in data.get("cameras", [data["camera"]]))
        active_camera_id = data.get("active_camera_id", camera.camera_id)
        selected_camera = _find_camera(cameras, active_camera_id) or camera
        base_floor_zone = ZoneConfig(**data["floor_zone"])
        floor_zones = tuple(ZoneConfig(**item) for item in data.get("floor_zones", []))
        selected_floor_zone = _find_zone(floor_zones, selected_camera.camera_id) or base_floor_zone
        room = RoomConfig(
            **data.get(
                "room",
                {
                    "room_id": selected_camera.room_id or selected_camera.camera_id,
                    "name": selected_camera.room_label or selected_camera.name,
                },
            )
        )
        if selected_camera.camera_id != camera.camera_id:
            room = _room_for_camera(selected_camera, room)
        return cls(
            camera=selected_camera,
            room=room,
            floor_zone=selected_floor_zone,
            floor_stay=FloorStayConfig(**data["floor_stay"]),
            tracking=TrackingConfig(**_normalize_tracking_config(data.get("tracking", {}))),
            routines=tuple(RoutineConfig(**item) for item in data.get("routines", [])),
            storage=StorageConfig(**data["storage"]),
            cameras=cameras,
            active_camera_id=selected_camera.camera_id,
            floor_zones=floor_zones,
        )

    def with_selected_camera(self, camera: CameraConfig) -> "CareSightConfig":
        room = _room_for_camera(camera, self.room)
        zone = _find_zone(self.floor_zones, camera.camera_id) or replace(self.floor_zone, camera_id=camera.camera_id)
        return replace(self, camera=camera, room=room, floor_zone=zone, active_camera_id=camera.camera_id)

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")

    def to_dict(self) -> dict:
        return asdict(self)


def _find_camera(cameras: tuple[CameraConfig, ...], camera_id: str | None) -> CameraConfig | None:
    if camera_id is None:
        return None
    for camera in cameras:
        if camera.camera_id == camera_id:
            return camera
    return None


def _find_zone(zones: tuple[ZoneConfig, ...], camera_id: str | None) -> ZoneConfig | None:
    if camera_id is None:
        return None
    for zone in zones:
        if zone.camera_id == camera_id:
            return zone
    return None


def _normalize_tracking_config(data: dict) -> dict:
    normalized = dict(data)
    if "dedupe_seconds" in normalized and "dedupe_window_seconds" not in normalized:
        normalized["dedupe_window_seconds"] = normalized.pop("dedupe_seconds")
    return normalized


def _point_in_polygon(x: float, y: float, vertices: tuple[tuple[float, float], ...]) -> bool:
    inside = False
    previous_x, previous_y = vertices[-1]
    for current_x, current_y in vertices:
        if _point_on_segment(x, y, previous_x, previous_y, current_x, current_y):
            return True
        intersects = (current_y > y) != (previous_y > y)
        if intersects:
            slope_x = (previous_x - current_x) * (y - current_y) / (previous_y - current_y) + current_x
            if x < slope_x:
                inside = not inside
        previous_x, previous_y = current_x, current_y
    return inside


def _point_on_segment(
    x: float,
    y: float,
    segment_x1: float,
    segment_y1: float,
    segment_x2: float,
    segment_y2: float,
) -> bool:
    epsilon = 1e-9
    cross_product = (y - segment_y1) * (segment_x2 - segment_x1) - (x - segment_x1) * (segment_y2 - segment_y1)
    if abs(cross_product) > epsilon:
        return False
    return (
        min(segment_x1, segment_x2) - epsilon <= x <= max(segment_x1, segment_x2) + epsilon
        and min(segment_y1, segment_y2) - epsilon <= y <= max(segment_y1, segment_y2) + epsilon
    )


def _room_for_camera(camera: CameraConfig, fallback: RoomConfig) -> RoomConfig:
    return RoomConfig(
        room_id=camera.room_id or fallback.room_id,
        name=camera.room_label or fallback.name,
        floor=fallback.floor,
    )
