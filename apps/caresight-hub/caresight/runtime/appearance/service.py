from __future__ import annotations

from datetime import datetime

from .descriptors import AppearanceDescriptor, BBox, Frame, extract_appearance_descriptor
from .profiles import AppearanceProfile, ContinuityMatch, match_profile_continuity


class AppearanceProfileService:
    def describe_observation(
        self,
        *,
        bbox_xyxy: BBox,
        frame: Frame | None = None,
        snapshot_path: str | None = None,
        frame_source: str | None = None,
        descriptor_source: str = "runtime_observation",
        event_id: str | None = None,
        observation_id: str | None = None,
    ) -> AppearanceDescriptor:
        return extract_appearance_descriptor(
            bbox_xyxy=bbox_xyxy,
            frame=frame,
            snapshot_path=snapshot_path,
            frame_source=frame_source,
            descriptor_source=descriptor_source,
            event_id=event_id,
            observation_id=observation_id,
        )

    def continuity_match(
        self,
        profile: AppearanceProfile,
        descriptor: AppearanceDescriptor,
        *,
        observed_at: datetime,
        track_id: str | None = None,
        camera_id: str | None = None,
        role_assignment: str | None = None,
    ) -> ContinuityMatch:
        return match_profile_continuity(
            profile,
            descriptor,
            observed_at=observed_at,
            track_id=track_id,
            camera_id=camera_id,
            role_assignment=role_assignment,
        )
