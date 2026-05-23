# Sprint 04 Tracking Baseline

Date: 2026-05-23

Scope: read the current tracking and floor-stay behavior before the Sprint 04 reliability changes.

## Baseline Commands

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python -m pytest apps/caresight-hub/tests/test_tracking_state.py apps/caresight-hub/tests/test_floor_stay.py -v
```

Result: blocked in the local YOLO venv because `pytest` is not installed.

```text
No module named pytest
```

Equivalent repo-supported unittest gate:

```bash
npm run py:check
```

Result before Sprint 04 edits: passed, 133 tests OK.

## Baseline Findings

- `FloorStayDetector` already persisted `possible_floor_stay` events with `track_id`, local-only evidence, and human-confirmation status.
- The previous detector allowed continuous floor-candidate dwell to survive a new track ID; that helped the prior live demo but did not satisfy the Sprint 04 same-track reliability policy.
- `MissingOffCameraDetector` emitted one missing-off-camera event per track but did not yet encode staged absence language or explicit `not_claimed` evidence.
- Review packets and blackbox receipts were already SQLite-derived and read-only, but did not display `escalation_stage`.

## Boundary

This baseline did not run live camera, OBS, iMessage, TTS, or FaceTime paths.
