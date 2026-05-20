from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from caresight.runtime.config import CareSightConfig
from caresight.runtime.tracking import TrackSnapshot, TrackState
from caresight.vision.detections import Detection


class FloorStayDetector:
    def __init__(self, config: CareSightConfig):
        self.config = config
        self._tracker = TrackState(occlusion_grace_seconds=config.tracking.occlusion_grace_seconds)
        self._entered_at_by_track: dict[str, float] = {}
        self._last_event_at_by_track: dict[str, float] = {}

    def update(self, detections: list[Detection], now: float | None = None) -> dict | None:
        if now is None:
            now = datetime.now(tz=UTC).timestamp()

        tracked_people = self._tracker.update(detections, now=now)
        person = self._best_person_in_floor_zone(tracked_people)
        active_track_ids = self._tracker.active_track_ids()
        self._entered_at_by_track = {
            track_id: entered_at
            for track_id, entered_at in self._entered_at_by_track.items()
            if track_id in active_track_ids
        }
        if person is None:
            return None

        entered_at = self._entered_at_by_track.get(person.track_id)
        if entered_at is None:
            self._entered_at_by_track[person.track_id] = now
            return None

        dwell_seconds = now - entered_at
        last_event_at = self._last_event_at_by_track.get(person.track_id)
        if dwell_seconds < self.config.floor_stay.dwell_seconds:
            return None
        if last_event_at is not None and now - last_event_at < self.config.tracking.dedupe_seconds:
            return None

        self._last_event_at_by_track[person.track_id] = now
        return self._build_event(person, dwell_seconds, now)

    def missing_tracks(self, now: float) -> list[TrackSnapshot]:
        return self._tracker.missing_tracks(
            now=now,
            missing_seconds=self.config.tracking.missing_seconds,
        )

    def _best_person_in_floor_zone(self, detections: list[TrackSnapshot]) -> TrackSnapshot | None:
        people_in_zone = [
            track
            for track in detections
            if track.detection.is_person()
            and self.config.floor_zone.contains_normalized_point(
                *track.detection.bottom_center_normalized
            )
        ]
        if not people_in_zone:
            return None
        return max(people_in_zone, key=lambda track: track.detection.confidence)

    def _build_event(self, track: TrackSnapshot, dwell_seconds: float, now: float) -> dict:
        detection = track.detection
        occurred_at = datetime.fromtimestamp(now, tz=UTC).isoformat().replace("+00:00", "Z")
        return {
            "schema": "care-event",
            "event_id": f"evt_{uuid4().hex}",
            "event_type": "possible_floor_stay",
            "occurred_at": occurred_at,
            "camera_id": self.config.camera.camera_id,
            "zone_id": self.config.floor_zone.zone_id,
            "severity": self.config.floor_stay.severity,
            "confidence": self.config.floor_stay.confidence,
            "status": "awaiting_human_confirmation",
            "requires_human_confirmation": True,
            "allowed_actions": ["journal_entry", "caregiver_alert", "facetime_handoff"],
            "blocked_actions": ["autonomous_emergency_dispatch", "medical_diagnosis"],
            "evidence": {
                "raw_video_stays_local": True,
                "dwell_seconds": round(dwell_seconds, 2),
                "track_id": track.track_id,
                "model": "yolo26n-mlx",
                "detection_confidence": round(detection.confidence, 4),
                "bbox_xyxy": list(detection.bbox_xyxy),
                "zone_kind": self.config.floor_zone.kind,
                "camera_id": self.config.camera.camera_id,
                "room_id": self.config.room.room_id,
                "room_name": self.config.room.name,
            },
        }
