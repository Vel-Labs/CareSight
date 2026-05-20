from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from caresight.runtime.config import CareSightConfig
from caresight.runtime.tracking import TrackSnapshot


class MissingOffCameraDetector:
    def __init__(self, config: CareSightConfig):
        self.config = config
        self._emitted_track_ids: set[str] = set()

    def update(self, missing_tracks: list[TrackSnapshot], now: float) -> dict | None:
        for track in missing_tracks:
            if track.track_id in self._emitted_track_ids:
                continue
            self._emitted_track_ids.add(track.track_id)
            return self._build_event(track, now)
        return None

    def _build_event(self, track: TrackSnapshot, now: float) -> dict:
        occurred_at = datetime.fromtimestamp(now, tz=UTC).isoformat().replace("+00:00", "Z")
        return {
            "schema": "care-event",
            "event_id": f"evt_{uuid4().hex}",
            "event_type": "missing_off_camera_extended",
            "occurred_at": occurred_at,
            "camera_id": self.config.camera.camera_id,
            "zone_id": None,
            "severity": self.config.tracking.missing_severity,
            "confidence": "medium",
            "status": "awaiting_human_confirmation",
            "requires_human_confirmation": True,
            "allowed_actions": ["journal_entry", "caregiver_alert", "facetime_handoff"],
            "blocked_actions": ["autonomous_emergency_dispatch", "medical_diagnosis"],
            "evidence": {
                "raw_video_stays_local": True,
                "track_id": track.track_id,
                "missed_seconds": track.missed_seconds,
                "last_seen_at": datetime.fromtimestamp(
                    track.last_seen_at,
                    tz=UTC,
                ).isoformat().replace("+00:00", "Z"),
                "model": "yolo26n-mlx",
                "camera_id": self.config.camera.camera_id,
                "room_id": self.config.room.room_id,
                "room_name": self.config.room.name,
            },
        }
