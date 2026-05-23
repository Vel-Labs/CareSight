from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable, Protocol

from caresight.runtime.config import CameraConfig
from caresight.runtime.cameras.sources import validate_camera_source


class FrameSource(Protocol):
    def read(self) -> tuple[bool, Any]: ...

    def release(self) -> None: ...


@dataclass(frozen=True)
class MultiCameraFrame:
    camera_id: str
    room_id: str
    room_label: str
    captured_at: str
    frame: Any


@dataclass(frozen=True)
class CameraHealth:
    camera_id: str
    status: str
    blocker: str | None = None
    message: str | None = None
    captured_at: str | None = None


class UnsupportedCameraSource(ValueError):
    pass


class MultiCameraFrameManager:
    def __init__(
        self,
        cameras: tuple[CameraConfig, ...],
        *,
        opener: Callable[[CameraConfig], FrameSource] | None = None,
        now: Callable[[], str] | None = None,
    ):
        if not cameras:
            raise ValueError("at least one camera is required")
        for camera in cameras:
            try:
                validate_camera_source(camera)
            except ValueError as error:
                raise UnsupportedCameraSource(str(error)) from error
        self._cameras = cameras
        self._opener = opener or _opencv_source
        self._now = now or _utc_now
        self._sources: dict[str, FrameSource] = {}
        self._health: dict[str, CameraHealth] = {
            camera.camera_id: CameraHealth(camera_id=camera.camera_id, status="not_opened")
            for camera in cameras
        }
        self._next_index = 0

    def read_next(self) -> MultiCameraFrame | None:
        camera = self._cameras[self._next_index]
        self._next_index = (self._next_index + 1) % len(self._cameras)
        try:
            source = self._source_for(camera)
            ok, frame = source.read()
        except Exception as error:
            self._health[camera.camera_id] = CameraHealth(
                camera_id=camera.camera_id,
                status="open_failure",
                blocker="camera_source_unavailable",
                message=str(error),
            )
            return None
        if not ok or frame is None:
            self._health[camera.camera_id] = CameraHealth(
                camera_id=camera.camera_id,
                status="open_failure",
                blocker="camera_source_unavailable",
                message="first frame was not available",
            )
            return None
        captured_at = self._now()
        self._health[camera.camera_id] = CameraHealth(
            camera_id=camera.camera_id,
            status="ok",
            captured_at=captured_at,
        )
        return MultiCameraFrame(
            camera_id=camera.camera_id,
            room_id=camera.room_id or camera.camera_id,
            room_label=camera.room_label or camera.name,
            captured_at=captured_at,
            frame=frame,
        )

    def health(self) -> dict[str, CameraHealth]:
        return dict(self._health)

    def close(self) -> None:
        for source in self._sources.values():
            source.release()
        self._sources.clear()

    def _source_for(self, camera: CameraConfig) -> FrameSource:
        source = self._sources.get(camera.camera_id)
        if source is None:
            source = self._opener(camera)
            self._sources[camera.camera_id] = source
        return source


def _opencv_source(camera: CameraConfig) -> FrameSource:
    import cv2

    from caresight.runtime.cameras.sources import camera_source_for_opencv

    capture = cv2.VideoCapture(camera_source_for_opencv(camera))
    if camera.source_type == "rtsp":
        capture.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
        capture.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
    return capture


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
