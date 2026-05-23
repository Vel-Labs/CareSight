# Sprint 04 Tracking Reliability

Date: 2026-05-23

Scope: deterministic Sprint 04 implementation for tracking reliability. This is implemented and locally tested; it is not a human/live-camera production-validation claim.

## Implemented Behavior

- `possible_floor_stay` evidence now includes `escalation_stage`, `same_track_dwell_seconds`, `occlusion_grace_seconds`, `dedupe_window_seconds`, `policy_version`, and explicit `not_claimed` boundaries.
- Same-track dwell is required by default in tracking config; a different track cannot inherit floor-stay dwell.
- Short occlusion still preserves track continuity through `TrackState`; long occlusion resets dwell.
- Repeated events for the same track are suppressed inside the configured dedupe window.
- Missing-off-camera evidence now uses staged language:
  - under 2 minutes: observe only, no event;
  - 2-5 minutes: check-in suggested;
  - 5-10 minutes after recent concern: attention suggested;
  - 10-15 minutes after high concern: urgent handoff suggested.
- Missing-off-camera copy uses `a tracked person` and avoids named identity, danger, medical emergency, and dispatch claims.
- Human review packet and blackbox receipt Markdown now display `Escalation stage` when present.
- Added bounded valid/invalid contract examples for tracking-reliability events and forbidden overclaim cases.

## Deterministic Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s apps/caresight-hub/tests -t apps/caresight-hub -p 'test_floor_stay.py'
```

Result: passed, 9 tests OK.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s apps/caresight-hub/tests -t apps/caresight-hub -p 'test_missing_off_camera.py'
```

Result: passed, 5 tests OK.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s apps/caresight-hub/tests -t apps/caresight-hub -p 'test_demo_surface.py'
```

Result: passed, 4 tests OK.

```bash
npm run py:check
```

Result: passed, 137 tests OK.

```bash
npm run validate:contracts
```

Result: passed, 15 schemas, 20 valid examples, 21 invalid examples.

## Optional Operator Validation

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python \
  apps/caresight-hub/scripts/v0_floor_stay_live.py \
  --camera-id living_room \
  --debug-floor-stay \
  --max-seconds 90 \
  --stop-after-event \
  --no-window
```

Operator checklist:

- [ ] Floor-zone trigger is understandable in the debug output.
- [ ] Seated/desk posture does not create a floor-stay event.
- [ ] Debug rejection reasons are readable without inspecting private imagery.
- [ ] Review packet avoids emergency, diagnosis, and medical-device language.
- [ ] Any live event remains `awaiting_human_confirmation` unless an authorized human explicitly reviews it.

## Remaining Risks

- The default v0 demo config still uses an 8-second dwell for fast local proof. The Sprint 04 policy fields support 30/90/180 second staged thresholds when configured for longer operator validation.
- Human/live-camera validation is still operator-owned.
- No FaceTime, iMessage, TTS playback, or OBS live handoff was engaged by this Sprint 04 deterministic pass.

## Decision Log

No new architecture decision was required. This change stays inside the existing deterministic tracking, SQLite-canonical, and human-review boundaries already recorded in `DECISIONS.md`.
