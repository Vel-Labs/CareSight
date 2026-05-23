from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from caresight.runtime.config import CareSightConfig
from caresight.runtime.tracking import TrackSnapshot


class MissingOffCameraDetector:
    def __init__(self, config: CareSightConfig):
        self.config = config
        self._emitted_track_ids: set[str] = set()

    def update(
        self,
        missing_tracks: list[TrackSnapshot],
        now: float,
        *,
        recent_concern_severity: str | None = None,
    ) -> dict | None:
        for track in missing_tracks:
            if track.missed_seconds < 120:
                continue
            if track.track_id in self._emitted_track_ids:
                continue
            self._emitted_track_ids.add(track.track_id)
            return self._build_event(track, now, recent_concern_severity=recent_concern_severity)
        return None

    def _build_event(
        self,
        track: TrackSnapshot,
        now: float,
        *,
        recent_concern_severity: str | None,
    ) -> dict:
        occurred_at = datetime.fromtimestamp(now, tz=UTC).isoformat().replace("+00:00", "Z")
        stage, severity, language = _stage_for_missing(
            track.missed_seconds,
            recent_concern_severity=recent_concern_severity,
        )
        return {
            "schema": "care-event",
            "event_id": f"evt_{uuid4().hex}",
            "event_type": "missing_off_camera_extended",
            "occurred_at": occurred_at,
            "camera_id": self.config.camera.camera_id,
            "zone_id": None,
            "severity": severity,
            "confidence": "medium",
            "status": "awaiting_human_confirmation",
            "requires_human_confirmation": True,
            "allowed_actions": ["journal_entry", "caregiver_alert", "facetime_handoff"],
            "blocked_actions": ["autonomous_emergency_dispatch", "medical_diagnosis"],
            "evidence": {
                "raw_video_stays_local": True,
                "track_id": track.track_id,
                "missed_seconds": track.missed_seconds,
                "escalation_stage": stage,
                "caregiver_language": language,
                "policy_version": "missing_off_camera_v1_tracking_reliability",
                "not_claimed": ["named_identity", "person_in_danger", "medical_emergency", "dispatching_help"],
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


def _stage_for_missing(
    missed_seconds: float,
    *,
    recent_concern_severity: str | None,
) -> tuple[str, str, str]:
    if missed_seconds >= 600 and recent_concern_severity == "high":
        return (
            "urgent_handoff_suggested",
            "high",
            "A tracked person is no longer visible after a recent high-concern observation; prepare an urgent handoff for caregiver review without emergency dispatch.",
        )
    if missed_seconds >= 300 and recent_concern_severity in {"medium", "high"}:
        return (
            "attention_suggested",
            "medium",
            "A tracked person is no longer visible after a recent concern; caregiver attention is suggested using the local record.",
        )
    return (
        "check_in_suggested",
        "low",
        "A tracked person has been off this camera long enough for a caregiver check-in suggestion.",
    )
