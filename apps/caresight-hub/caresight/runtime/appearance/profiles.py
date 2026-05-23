from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .descriptors import AppearanceDescriptor


@dataclass(frozen=True)
class AppearanceProfile:
    appearance_profile_id: str
    active_date: str
    expires_at: str
    role_assignment: str
    assignment_source: str
    track_id: str | None
    upper_body_color: str
    lower_body_color: str
    last_seen_camera_id: str
    last_seen_room: str
    last_seen_at: str
    headwear: str = "unknown"
    footwear: str = "unknown"
    last_seen_event_id: str | None = None

    def to_storage_record(self) -> dict[str, object]:
        return {
            "appearance_profile_id": self.appearance_profile_id,
            "active_date": self.active_date,
            "expires_at": self.expires_at,
            "role_assignment": self.role_assignment,
            "assignment_source": self.assignment_source,
            "track_id": self.track_id,
            "upper_body_color": self.upper_body_color,
            "lower_body_color": self.lower_body_color,
            "headwear": self.headwear,
            "footwear": self.footwear,
            "last_seen_camera_id": self.last_seen_camera_id,
            "last_seen_room": self.last_seen_room,
            "last_seen_at": self.last_seen_at,
            "last_seen_event_id": self.last_seen_event_id,
        }


@dataclass(frozen=True)
class ContinuityMatch:
    matched: bool
    confidence: float
    reason: str
    appearance_profile_id: str

    def to_storage_record(self) -> dict[str, object]:
        return {
            "matched": self.matched,
            "confidence": self.confidence,
            "reason": self.reason,
            "appearance_profile_id": self.appearance_profile_id,
        }


def match_profile_continuity(
    profile: AppearanceProfile,
    descriptor: AppearanceDescriptor,
    *,
    observed_at: datetime,
    track_id: str | None = None,
    camera_id: str | None = None,
    role_assignment: str | None = None,
) -> ContinuityMatch:
    if _is_expired(profile, observed_at):
        return ContinuityMatch(False, 0.0, "expired_profile", profile.appearance_profile_id)

    if descriptor.descriptor_status != "available":
        return ContinuityMatch(False, 0.0, "descriptor_unavailable", profile.appearance_profile_id)

    colors_match = (
        descriptor.upper_body_color.value == profile.upper_body_color
        and descriptor.lower_body_color.value == profile.lower_body_color
    )
    same_track = track_id is not None and track_id == profile.track_id
    same_camera = camera_id is not None and camera_id == profile.last_seen_camera_id
    conflicting_role = (
        role_assignment is not None
        and profile.role_assignment != "unknown_person"
        and role_assignment != profile.role_assignment
    )

    if not same_track and not colors_match:
        return ContinuityMatch(False, 0.0, "descriptor_mismatch", profile.appearance_profile_id)

    if same_track:
        confidence = 0.85
        reason = "same_track_same_day"
    elif same_camera:
        confidence = 0.65
        reason = "clothing_only_same_camera"
    else:
        confidence = 0.55
        reason = "clothing_only_cross_camera"

    if conflicting_role:
        confidence = min(confidence, 0.40)
        reason = "conflicting_role"

    return ContinuityMatch(True, confidence, reason, profile.appearance_profile_id)


def _is_expired(profile: AppearanceProfile, observed_at: datetime) -> bool:
    if observed_at.date().isoformat() != profile.active_date:
        return True
    expires_at = _parse_datetime(profile.expires_at)
    return observed_at >= expires_at


def _parse_datetime(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)
