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
        likely_continuity_camera_id: str | None = None,
    ) -> dict | None:
        if likely_continuity_camera_id:
            return None
        for track in missing_tracks:
            missing_window = _missing_window_seconds(self.config)
            if track.missed_seconds < missing_window:
                continue
            if track.track_id in self._emitted_track_ids:
                continue
            self._emitted_track_ids.add(track.track_id)
            return self._build_event(
                track,
                now,
                recent_concern_severity=recent_concern_severity,
                missing_window_seconds=missing_window,
            )
        return None

    def _build_event(
        self,
        track: TrackSnapshot,
        now: float,
        *,
        recent_concern_severity: str | None,
        missing_window_seconds: float,
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
                "missing_window_seconds": missing_window_seconds,
                "absence_expected_after_seconds": self.config.tracking.absence_expected_after_seconds,
                "quiet_hours": list(self.config.tracking.quiet_hours),
                "visibility_state": "previously_seen_now_absent",
                "indicator_label": _indicator_for_stage(stage),
                "review_reason": _review_reason(track.missed_seconds, missing_window_seconds),
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


def _indicator_for_stage(stage: str) -> str:
    if stage == "urgent_handoff_suggested":
        return "Off-camera urgent handoff suggested"
    if stage == "attention_suggested":
        return "Off-camera attention suggested"
    return "Off-camera check-in suggested"


def _missing_window_seconds(config: CareSightConfig) -> float:
    tracking = config.tracking
    if config.camera.camera_id in tracking.per_camera_missing_seconds:
        return float(tracking.per_camera_missing_seconds[config.camera.camera_id])
    if config.room.room_id in tracking.per_room_missing_seconds:
        return float(tracking.per_room_missing_seconds[config.room.room_id])
    return float(tracking.missing_seconds)


def _review_reason(missed_seconds: float, missing_window_seconds: float) -> str:
    return (
        "tracked person no longer visible past configured contextual missing window "
        f"({missed_seconds:.1f}s observed, {missing_window_seconds:.1f}s required)"
    )


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
