# Sprint 02-05 Validation Recovery Closeout

Date: 2026-05-23

Scope: corrected recovery status after the prior premature Sprint 02/03/04/05 completion claim.

## Corrected Evidence Map

| User correction | Recovery artifact | Status |
| --- | --- | --- |
| Sprint 03 still-image validation needs actual varied runs | `apps/caresight-hub/config/appearance-still-image-validation-runs.example.json`; `docs/audits/2026-05-23-sprint-03-expanded-still-image-validation.md` | Improved: 10 actual local snapshot runs plus one source-backed crowded Wikimedia Commons run under `/private/tmp`, with difficulty, confidence, descriptor status, and outputs. |
| Sprint 04 needs complexity-graded deterministic testing | `apps/caresight-hub/tests/test_floor_stay.py`; `docs/audits/2026-05-23-sprint-04-complexity-graded-validation.md` | Improved: named tests cover same-track dwell, churn, occlusion, dedupe, distance/box scale, multi-person selection, false-positive posture, and missing-off-camera stages. Live camera proof remains operator-owned. |
| Sprint 05 camera support needs proof or precise blocker | `docs/audits/2026-05-23-sprint-05-camera-proof-recovery.md` | Improved: source-backed Tapo/RTSP assumptions, redacted dry-run receipt, live probe prerequisites, and blocker classes are explicit. Live Tapo proof remains blocked on operator-owned credentials/IP/same-LAN access. |
| Sprint 02 FaceTime/OBS/TTS needs resolution research and alternatives | `docs/audits/2026-05-23-sprint-02-facetime-obs-tts-resolution-ladder.md` | Improved: source-backed OBS/FaceTime/BlackHole findings and no-call checks are recorded. Detector MJPEG and OBS websocket were not running; BlackHole device was unavailable; Dakota TTS generated with playback disabled after Metal access was allowed. |
| Docs/changelog/CLI need corrected inspectable output | `CHANGELOG.md`; `docs/cli/COMMANDS.md`; `docs/roadmaps/CURRENT_STATE_AND_NEXT.md`; `docs/operations/local_model_operations.md`; `docs/architecture/camera_integration_strategy.md` | Improved and verified with `npm run check`. |

## Remaining Gates

- Sprint 02: start detector MJPEG server and OBS websocket, confirm `check_obs_live_feed.py`, confirm BlackHole appears as input/output, and get explicit human approval before any FaceTime or TTS playback.
- Sprint 03: collect broader source-backed still-image variety only if more internet-media coverage is needed beyond the local snapshot and one crowded-source recovery run.
- Sprint 04: run the bounded live-camera `--debug-floor-stay --max-seconds 90 --stop-after-event --no-window` validation when operator proof is required.
- Sprint 05: create ignored `tapo.local.json` with owner-authorized credentials/IP and run the live redacted probe.

## Verification

```bash
npm run check
```

Latest result in this recovery run: passed.

## Boundary

This recovery does not claim CareSight is production-ready, a medical device, HIPAA-compliant, a fall detector, or an autonomous emergency-dispatch system. No live iMessage, FaceTime call, TTS playback, event confirmation, event dismissal, camera scan, credential guessing, or raw media commit occurred.
