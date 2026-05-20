from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from caresight.runtime.config import CareSightConfig, RoutineConfig
from caresight.vision.detections import Detection


class RoutineEventDetector:
    def __init__(self, config: CareSightConfig):
        self.config = config
        self._emitted_routines: set[str] = set()

    def update(self, detections: list[Detection], now: datetime | None = None) -> list[dict]:
        if now is None:
            now = datetime.now(tz=UTC)
        events = []
        for routine in self.config.routines:
            if routine.routine_id in self._emitted_routines:
                continue
            person = self._person_in_routine_zone(detections, routine)
            evidence = self._object_evidence(detections, routine)
            if person is None or evidence is None or not is_in_window(now, routine):
                continue
            self._emitted_routines.add(routine.routine_id)
            events.append(self._build_event(routine, person, evidence, now))
        return events

    def _person_in_routine_zone(
        self,
        detections: list[Detection],
        routine: RoutineConfig,
    ) -> Detection | None:
        people = [
            detection
            for detection in detections
            if detection.is_person()
            and routine.contains_normalized_point(*detection.bottom_center_normalized)
        ]
        if not people:
            return None
        return max(people, key=lambda detection: detection.confidence)

    def _object_evidence(
        self,
        detections: list[Detection],
        routine: RoutineConfig,
    ) -> Detection | None:
        allowed = set(routine.object_labels)
        objects = [
            detection
            for detection in detections
            if detection.class_name in allowed
            and routine.contains_normalized_point(*detection.bottom_center_normalized)
        ]
        if not objects:
            return None
        return max(objects, key=lambda detection: detection.confidence)

    def _build_event(
        self,
        routine: RoutineConfig,
        person: Detection,
        evidence: Detection,
        now: datetime,
    ) -> dict:
        occurred_at = now.astimezone(UTC).isoformat().replace("+00:00", "Z")
        return {
            "schema": "care-event",
            "event_id": f"evt_{uuid4().hex}",
            "event_type": routine.event_type,
            "occurred_at": occurred_at,
            "camera_id": self.config.camera.camera_id,
            "zone_id": routine.zone_id,
            "severity": routine.severity,
            "confidence": routine.confidence,
            "status": "awaiting_human_confirmation",
            "requires_human_confirmation": True,
            "allowed_actions": ["journal_entry", "caregiver_alert", "facetime_handoff"],
            "blocked_actions": [
                "autonomous_emergency_dispatch",
                "medical_diagnosis",
                "medication_confirmed_without_authorized_human",
            ],
            "evidence": {
                "raw_video_stays_local": True,
                "routine_id": routine.routine_id,
                "routine_window": f"{routine.window_start}-{routine.window_end}",
                "person_label": person.class_name,
                "person_confidence": round(person.confidence, 4),
                "object_label": evidence.class_name,
                "object_confidence": round(evidence.confidence, 4),
                "bbox_xyxy": list(person.bbox_xyxy),
                "object_bbox_xyxy": list(evidence.bbox_xyxy),
                "wording": "likely observed",
                "not_claimed": [
                    "specific_medication_taken",
                    "medication_administered",
                    "medical_compliance",
                ],
                "camera_id": self.config.camera.camera_id,
                "room_id": self.config.room.room_id,
                "room_name": self.config.room.name,
            },
        }


def is_in_window(now: datetime, routine: RoutineConfig) -> bool:
    current = now.astimezone(UTC).strftime("%H:%M")
    if routine.window_start <= routine.window_end:
        return routine.window_start <= current <= routine.window_end
    return current >= routine.window_start or current <= routine.window_end
