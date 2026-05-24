from __future__ import annotations

from dataclasses import dataclass

from caresight.runtime.escalation.events import EscalationEvent
from caresight.runtime.escalation.methods import (
    FACETIME_HANDOFF,
    NO_SEND_DRY_RUN,
    OBS_UPDATE,
    REVIEW_ONLY,
    TEXT_HANDOFF,
    EscalationMethod,
)


@dataclass(frozen=True)
class EscalationPlan:
    event_id: str
    event_type: str
    methods: tuple[EscalationMethod, ...]
    escalation_level: str


def plan_escalation(
    event: EscalationEvent | dict,
    *,
    missing_off_camera_review_only: bool = True,
    live_handoff_enabled: bool = False,
) -> EscalationPlan:
    escalation_event = EscalationEvent.from_event(event) if isinstance(event, dict) else event
    if escalation_event.event_type == "possible_floor_stay":
        methods = [OBS_UPDATE, NO_SEND_DRY_RUN]
        if live_handoff_enabled:
            methods.extend([TEXT_HANDOFF, FACETIME_HANDOFF])
        return EscalationPlan(
            event_id=escalation_event.event_id,
            event_type=escalation_event.event_type,
            methods=tuple(methods),
            escalation_level="urgent_handoff" if escalation_event.severity == "high" else "attention",
        )
    if escalation_event.event_type == "missing_off_camera_extended":
        return EscalationPlan(
            event_id=escalation_event.event_id,
            event_type=escalation_event.event_type,
            methods=(REVIEW_ONLY,) if missing_off_camera_review_only else (OBS_UPDATE, NO_SEND_DRY_RUN),
            escalation_level="review_only" if missing_off_camera_review_only else "attention",
        )
    return EscalationPlan(
        event_id=escalation_event.event_id,
        event_type=escalation_event.event_type,
        methods=(REVIEW_ONLY,),
        escalation_level="review_only",
    )
