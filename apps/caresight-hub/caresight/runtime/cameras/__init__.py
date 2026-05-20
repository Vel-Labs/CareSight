"""Deterministic camera configuration helpers for local source selection."""

from .sources import (
    SUPPORTED_CAMERA_SOURCE_TYPES,
    camera_source_for_opencv,
    select_configured_camera,
    validate_camera_source,
)

__all__ = [
    "SUPPORTED_CAMERA_SOURCE_TYPES",
    "camera_source_for_opencv",
    "select_configured_camera",
    "validate_camera_source",
]
