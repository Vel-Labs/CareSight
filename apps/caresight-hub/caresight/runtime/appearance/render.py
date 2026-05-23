from __future__ import annotations

from .profiles import AppearanceProfile


ROLE_LABELS = {
    "resident_primary": "resident-assigned profile for today",
    "caregiver_known": "caregiver-assigned profile for today",
    "visitor_unknown": "visitor profile for today",
    "unknown_person": "unknown-person profile for today",
}


def render_appearance_summary(profile: AppearanceProfile) -> str:
    role = ROLE_LABELS.get(profile.role_assignment, "profile for today")
    parts = [role]
    if profile.upper_body_color != "unknown":
        parts.append(f"{profile.upper_body_color} upper clothing")
    if profile.lower_body_color != "unknown":
        parts.append(f"{profile.lower_body_color} lower clothing")
    if profile.headwear != "unknown":
        parts.append(f"{profile.headwear} headwear")
    if profile.footwear != "unknown":
        parts.append(f"{profile.footwear} footwear")
    if profile.last_seen_room:
        parts.append(f"last seen in {profile.last_seen_room}")
    return "; ".join(parts) + "."
