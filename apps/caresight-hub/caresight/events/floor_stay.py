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
        self._floor_candidate_entered_at: float | None = None
        self._floor_candidate_last_seen_at: float | None = None
        self._last_floor_event_at: float | None = None
        self._last_diagnostic: dict = {"status": "not_started"}
        self._last_tracked_people: list[TrackSnapshot] = []

    def update(self, detections: list[Detection], now: float | None = None) -> dict | None:
        if now is None:
            now = datetime.now(tz=UTC).timestamp()

        tracked_people = self._tracker.update(detections, now=now)
        self._last_tracked_people = tracked_people
        person = self._best_person_in_floor_zone(tracked_people)
        active_track_ids = self._tracker.active_track_ids()
        self._entered_at_by_track = {
            track_id: entered_at
            for track_id, entered_at in self._entered_at_by_track.items()
            if track_id in active_track_ids
        }
        self._last_diagnostic = self._build_diagnostic(tracked_people, person, now)
        if person is None:
            if (
                self._floor_candidate_last_seen_at is not None
                and now - self._floor_candidate_last_seen_at > self.config.tracking.occlusion_grace_seconds
            ):
                self._floor_candidate_entered_at = None
                self._floor_candidate_last_seen_at = None
                self._last_floor_event_at = None
            return None

        if person.track_id not in self._entered_at_by_track:
            self._entered_at_by_track[person.track_id] = now
        if self._floor_candidate_entered_at is None or self.config.tracking.same_track_required:
            self._floor_candidate_entered_at = now
        self._floor_candidate_last_seen_at = now

        entered_at = (
            self._entered_at_by_track.get(person.track_id)
            if self.config.tracking.same_track_required
            else self._floor_candidate_entered_at
        )
        if entered_at is None:
            self._last_diagnostic = self._build_diagnostic(tracked_people, person, now)
            return None

        dwell_seconds = now - entered_at
        self._last_diagnostic = self._build_diagnostic(tracked_people, person, now)
        if dwell_seconds < self.config.floor_stay.dwell_seconds:
            return None
        last_event_at = self._last_event_at_by_track.get(person.track_id)
        if (
            last_event_at is not None
            and now - last_event_at < self.config.tracking.dedupe_window_seconds
        ):
            return None

        self._last_floor_event_at = now
        self._last_event_at_by_track[person.track_id] = now
        return self._build_event(person, dwell_seconds, now)

    def missing_tracks(self, now: float) -> list[TrackSnapshot]:
        return self._tracker.missing_tracks(
            now=now,
            missing_seconds=self.config.tracking.missing_seconds,
        )

    def diagnostic(self) -> dict:
        return self._last_diagnostic

    def tracked_people(self) -> list[TrackSnapshot]:
        return list(self._last_tracked_people)

    def _best_person_in_floor_zone(self, detections: list[TrackSnapshot]) -> TrackSnapshot | None:
        people_in_zone = [
            track
            for track in detections
            if track.detection.is_person()
            and track.detection.confidence >= self.config.tracking.min_person_confidence
            and self.config.floor_zone.contains_normalized_point(
                *track.detection.bottom_center_normalized
            )
            and _looks_like_low_posture(track.detection)
        ]
        if not people_in_zone:
            return None
        return max(people_in_zone, key=lambda track: track.detection.confidence)

    def _build_diagnostic(
        self,
        tracked_people: list[TrackSnapshot],
        selected: TrackSnapshot | None,
        now: float,
    ) -> dict:
        people = []
        for track in tracked_people:
            detection = track.detection
            x1, y1, x2, y2 = detection.bbox_xyxy
            width = max(x2 - x1, 1.0)
            height = max(y2 - y1, 1.0)
            aspect_ratio = width / height
            center_y = ((y1 + y2) / 2.0) / detection.frame_height
            bottom_center = detection.bottom_center_normalized
            in_floor_zone = self.config.floor_zone.contains_normalized_point(*bottom_center)
            low_posture = _looks_like_low_posture(detection)
            entered_at = self._entered_at_by_track.get(track.track_id)
            if selected is not None and track.track_id == selected.track_id:
                entered_at = (
                    self._entered_at_by_track.get(track.track_id)
                    if self.config.tracking.same_track_required
                    else self._floor_candidate_entered_at
                )
            dwell_seconds = 0.0 if entered_at is None else max(0.0, now - entered_at)
            people.append(
                {
                    "track_id": track.track_id,
                    "confidence": round(detection.confidence, 4),
                    "bbox_xyxy": [round(value, 1) for value in detection.bbox_xyxy],
                    "aspect_ratio": round(aspect_ratio, 2),
                    "center_y": round(center_y, 2),
                    "bottom_center": [round(value, 2) for value in bottom_center],
                    "in_floor_zone": in_floor_zone,
                    "low_posture": low_posture,
                    "dwell_seconds": round(dwell_seconds, 2),
                }
            )

        status = "no_person_detected"
        if people:
            status = "person_detected_but_not_floor_stay_candidate"
        if selected is not None:
            status = "floor_stay_candidate_tracking"

        return {
            "status": status,
            "required_dwell_seconds": self.config.floor_stay.dwell_seconds,
            "selected_track_id": selected.track_id if selected else None,
            "people": people,
        }

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
                "same_track_dwell_seconds": round(dwell_seconds, 2),
                "escalation_stage": _escalation_stage(self.config, dwell_seconds),
                "occlusion_grace_seconds": self.config.tracking.occlusion_grace_seconds,
                "dedupe_window_seconds": self.config.tracking.dedupe_window_seconds,
                "policy_version": "floor_stay_v1_tracking_reliability",
                "not_claimed": ["fall_confirmed", "injury_detected", "medical_emergency"],
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


def _looks_like_low_posture(detection: Detection) -> bool:
    x1, y1, x2, y2 = detection.bbox_xyxy
    width = max(x2 - x1, 1.0)
    height = max(y2 - y1, 1.0)
    aspect_ratio = width / height
    center_y = ((y1 + y2) / 2.0) / detection.frame_height

    return aspect_ratio >= 2.0 and center_y >= 0.60


def _escalation_stage(config: CareSightConfig, dwell_seconds: float) -> str:
    if dwell_seconds >= config.floor_stay.critical_dwell_seconds:
        return "critical_attention"
    if dwell_seconds >= config.floor_stay.prolonged_dwell_seconds:
        return "prolonged_concern"
    return "early_concern"
