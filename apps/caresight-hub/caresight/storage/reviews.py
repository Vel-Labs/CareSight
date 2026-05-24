from __future__ import annotations

from dataclasses import dataclass


ALLOWED_REVIEW_PURPOSES = {"initial_review", "followup_note", "amendment", "correction"}
FINAL_REVIEW_STATES = {"human_confirmed", "dismissed"}
REVIEW_DECISIONS = FINAL_REVIEW_STATES | {"needs_followup"}
INITIAL_REVIEW_FROM_STATES = {"awaiting_human_confirmation", "possible", "likely_observed", "needs_followup"}


@dataclass(frozen=True)
class ReviewTransition:
    previous_status: str
    new_status: str
    review_purpose: str
    amendment_of_review_id: str | None = None


def validate_review_transition(
    *,
    previous_status: str,
    decision: str,
    review_purpose: str,
    amendment_of_review_id: str | None = None,
) -> ReviewTransition:
    if decision not in REVIEW_DECISIONS:
        raise ValueError(f"unsupported decision: {decision}")
    if review_purpose not in ALLOWED_REVIEW_PURPOSES:
        raise ValueError(f"unsupported review purpose: {review_purpose}")
    if review_purpose == "amendment" and not amendment_of_review_id:
        raise ValueError("amendment_of_review_id is required for amendment reviews")
    if previous_status in FINAL_REVIEW_STATES and review_purpose != "amendment":
        raise ValueError("final review states require an explicit amendment")
    if review_purpose == "initial_review" and previous_status not in INITIAL_REVIEW_FROM_STATES:
        raise ValueError(f"initial_review cannot change event from {previous_status}")
    return ReviewTransition(
        previous_status=previous_status,
        new_status=decision,
        review_purpose=review_purpose,
        amendment_of_review_id=amendment_of_review_id,
    )
