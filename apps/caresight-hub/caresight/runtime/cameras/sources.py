from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING
from urllib.parse import urlparse

if TYPE_CHECKING:
    from caresight.runtime.config import CameraConfig, CareSightConfig

SUPPORTED_CAMERA_SOURCE_TYPES = frozenset({"webcam", "usb", "continuity_camera", "rtsp"})
BLOCKED_PROVIDER_TERMS = frozenset({"ring", "nest", "google_home", "home_assistant", "onvif", "cloud"})


def validate_camera_source(camera: "CameraConfig") -> None:
    source_type = camera.source_type.strip().lower()
    if source_type not in SUPPORTED_CAMERA_SOURCE_TYPES:
        raise ValueError(f"unsupported camera source_type: {camera.source_type}")

    haystack = f"{camera.camera_id} {camera.name} {source_type} {camera.source_uri}".lower()
    if any(term in haystack for term in BLOCKED_PROVIDER_TERMS):
        raise ValueError("cloud/provider camera sources are outside the local v0 scope")

    if source_type == "rtsp":
        parsed = urlparse(str(camera.source_uri))
        if parsed.scheme.lower() != "rtsp" or not parsed.hostname:
            raise ValueError("rtsp camera source_uri must be an rtsp:// host path")
        if parsed.username or parsed.password:
            raise ValueError("rtsp source_uri must not embed credentials")
        return

    if isinstance(camera.source_uri, int):
        return
    if isinstance(camera.source_uri, str) and camera.source_uri.isdecimal():
        return
    raise ValueError(f"{source_type} camera source_uri must be a local numeric device index")


def select_configured_camera(
    config: "CareSightConfig",
    *,
    camera_id: str | None = None,
    source_type: str | None = None,
) -> "CareSightConfig":
    cameras = config.cameras or (config.camera,)
    candidates = list(cameras)
    if camera_id:
        candidates = [camera for camera in candidates if camera.camera_id == camera_id]
    if source_type:
        normalized_source_type = source_type.strip().lower()
        candidates = [camera for camera in candidates if camera.source_type == normalized_source_type]

    if not candidates:
        requested = camera_id or source_type or config.active_camera_id or config.camera.camera_id
        raise ValueError(f"no configured camera matches {requested}")
    if len(candidates) > 1:
        matches = ", ".join(camera.camera_id for camera in candidates)
        raise ValueError(f"camera selection is ambiguous; choose one of: {matches}")

    selected = candidates[0]
    validate_camera_source(selected)
    return config.with_selected_camera(selected)


def camera_source_for_opencv(camera: "CameraConfig") -> int | str:
    validate_camera_source(camera)
    if camera.source_type == "rtsp":
        return str(camera.source_uri)
    return int(camera.source_uri)
