from __future__ import annotations

from dataclasses import dataclass

from caresight.vision.detections import Detection


@dataclass(frozen=True)
class TrackSnapshot:
    track_id: str
    detection: Detection
    first_seen_at: float
    last_seen_at: float
    missed_seconds: float = 0.0


class TrackState:
    def __init__(self, *, occlusion_grace_seconds: float = 1.0):
        self.occlusion_grace_seconds = occlusion_grace_seconds
        self._tracks: dict[str, TrackSnapshot] = {}
        self._next_track_number = 1

    def update(self, detections: list[Detection], *, now: float) -> list[TrackSnapshot]:
        people = [detection for detection in detections if detection.is_person()]
        matched: set[str] = set()
        snapshots: list[TrackSnapshot] = []

        for detection in people:
            track_id = self._match_track_id(detection, matched)
            previous = self._tracks.get(track_id)
            snapshot = TrackSnapshot(
                track_id=track_id,
                detection=detection,
                first_seen_at=previous.first_seen_at if previous else now,
                last_seen_at=now,
            )
            self._tracks[track_id] = snapshot
            matched.add(track_id)
            snapshots.append(snapshot)

        self._expire_missing_tracks(now, matched)
        return snapshots

    def missing_tracks(self, *, now: float, missing_seconds: float) -> list[TrackSnapshot]:
        missing = []
        for snapshot in self._tracks.values():
            elapsed = now - snapshot.last_seen_at
            if elapsed >= missing_seconds:
                missing.append(
                    TrackSnapshot(
                        track_id=snapshot.track_id,
                        detection=snapshot.detection,
                        first_seen_at=snapshot.first_seen_at,
                        last_seen_at=snapshot.last_seen_at,
                        missed_seconds=round(elapsed, 2),
                    )
                )
        return missing

    def reset_track(self, track_id: str) -> None:
        self._tracks.pop(track_id, None)

    def active_track_ids(self) -> set[str]:
        return set(self._tracks)

    def _match_track_id(self, detection: Detection, matched: set[str]) -> str:
        best_track_id = None
        best_score = 0.0
        for track_id, snapshot in self._tracks.items():
            if track_id in matched:
                continue
            score = bbox_iou(detection.bbox_xyxy, snapshot.detection.bbox_xyxy)
            if score > best_score:
                best_score = score
                best_track_id = track_id

        if best_track_id is not None and best_score >= 0.3:
            return best_track_id

        track_id = f"track_{self._next_track_number}"
        self._next_track_number += 1
        return track_id

    def _expire_missing_tracks(self, now: float, matched: set[str]) -> None:
        expired = [
            track_id
            for track_id, snapshot in self._tracks.items()
            if track_id not in matched
            and now - snapshot.last_seen_at > self.occlusion_grace_seconds
        ]
        for track_id in expired:
            self._tracks.pop(track_id, None)


def bbox_iou(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> float:
    ax1, ay1, ax2, ay2 = first
    bx1, by1, bx2, by2 = second
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    inter_width = max(0.0, inter_x2 - inter_x1)
    inter_height = max(0.0, inter_y2 - inter_y1)
    intersection = inter_width * inter_height
    first_area = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    second_area = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = first_area + second_area - intersection
    if union <= 0:
        return 0.0
    return intersection / union
