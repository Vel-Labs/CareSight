# Tracking Foundation Audit

Date: 2026-05-19

## Scope

This audit records the deterministic tracking foundation for CareSight v1 event logic.

## Implemented

- Added `apps/caresight-hub/caresight/runtime/tracking/` with a lightweight local track state machine.
- Made `possible_floor_stay` track-aware through stable `track_id` dwell evidence.
- Preserved short occlusions within the configured grace period.
- Reset dwell and dedupe state when a track exits long enough to expire.
- Added initial `missing_off_camera_extended` event policy for known tracks absent beyond the configured window.
- Persisted `track_id` in `event_observations`.
- Added contract coverage for `missing_off_camera_extended`.

## Boundaries

- No emergency dispatch is triggered.
- No medical diagnosis is made.
- No medication administration is inferred.
- Live camera and multi-camera proof remain operator-run evidence for final/demo audit.

## Deterministic Checks

Run:

```bash
npm run validate:contracts
npm run py:check
npm run check
```

Expected:

- Contract validation includes the missing-off-camera event example.
- Python tests cover same-track dwell, short occlusion continuity, long occlusion reset, duplicate suppression, missing-off-camera event emission, and SQLite `track_id` persistence.
