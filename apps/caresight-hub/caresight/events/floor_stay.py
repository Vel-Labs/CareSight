from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from caresight.runtime.config import CareSightConfig
from caresight.vision.detections import Detection


class FloorStayDetector:
    def __init__(self, config: CareSightConfig):
        self.config = config
        self._entered_at: float | None = None
        self._event_emitted_for_current_dwell = False

    def update(self, detections: list[Detection], now: float | None = None) -> dict | None:
        if now is None:
            now = datetime.now(tz=UTC).timestamp()

        person = self._best_person_in_floor_zone(detections)
        if person is None:
            self._entered_at = None
            self._event_emitted_for_current_dwell = False
            return None

        if self._entered_at is None:
            self._entered_at = now
            return None

        dwell_seconds = now - self._entered_at
        if (
            dwell_seconds < self.config.floor_stay.dwell_seconds
            or self._event_emitted_for_current_dwell
        ):
            return None

        self._event_emitted_for_current_dwell = True
        return self._build_event(person, dwell_seconds, now)

    def _best_person_in_floor_zone(self, detections: list[Detection]) -> Detection | None:
        people_in_zone = [
            detection
            for detection in detections
            if detection.is_person()
            and self.config.floor_zone.contains_normalized_point(
                *detection.bottom_center_normalized
            )
        ]
        if not people_in_zone:
            return None
        return max(people_in_zone, key=lambda detection: detection.confidence)

    def _build_event(self, detection: Detection, dwell_seconds: float, now: float) -> dict:
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
                "model": "yolo26n-mlx",
                "detection_confidence": round(detection.confidence, 4),
                "bbox_xyxy": list(detection.bbox_xyxy),
                "zone_kind": self.config.floor_zone.kind,
            },
        }
