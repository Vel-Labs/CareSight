# CareSight Audit Digest

This digest makes the evidence trail readable without asking a judge or operator to inspect every audit file.

## What The Audit Trail Shows

| Area | Evidence status | Key files |
| --- | --- | --- |
| YOLO26 MLX smoke path | Local model path and inference harness were established. | `docs/audits/2026-05-18-yolo26-mlx-smoke-checkpoint.md`, `docs/audits/2026-05-19-yolo26-inference-harness.md` |
| Floor-stay event engine | Same-track dwell, occlusion grace, dedupe, snapshots, and SQLite persistence were implemented. | `docs/audits/2026-05-18-v0-eventization-implementation.md`, `docs/audits/2026-05-20-t041-final-live-proof.md` |
| Human review and alerts | Dashboard, alert draft, review packet, blackbox receipt, and escalation surfaces exist. | `docs/audits/2026-05-19-care-console-dashboard-alerts.md`, `docs/audits/2026-05-21-agent-harness-review.md` |
| OBS and live handoff | OBS/FaceTime/TTS paths were staged with no-send and live-approval boundaries. | `docs/audits/2026-05-23-sprint-02-no-call-runtime-audit.md`, `docs/audits/2026-05-23-sprint-02-facetime-obs-tts-resolution-ladder.md` |
| Appearance descriptors | Visual-reference matrices and clothing sub-box overlays were added as advisory review context. | `docs/audits/2026-05-22-sprint-03-daily-appearance-profiles.md`, `docs/audits/2026-05-23-sprint-03-04-visual-reference-matrix.md` |
| Tracking and camera support | Multi-camera RTSP setup, Tapo camera probing, and detector browser feeds were added. | `docs/audits/2026-05-23-sprint-04-tracking-baseline.md`, `docs/audits/2026-05-23-sprint-05-camera-support.md`, `docs/audits/2026-05-23-tapo-rtsp-validation.md` |
| Current cleanup state | The current stable cut and cleanup plan were captured. | `docs/audits/2026-05-23-hackathon-state-and-cleanup-plan.md` |

## Current Truth Boundary

Implemented:

- local Tapo RTSP probing
- YOLO26 MLX detector workers
- calibrated floor-plane overlay
- `possible_floor_stay` event persistence
- SQLite event/audit path
- Markdown review and receipt rendering
- OBS browser feeds for Living Room and Kitchen

Now wired for validation:

- `missing_off_camera_extended` event persistence from the live loop when enabled with `--missing-off-camera-events`
- last-seen snapshot evidence for missing events
- advisory last-seen appearance attributes

Still needs operator proof:

- one current calibrated-floor-plane live event receipt using the final Tapo camera setup
- one current missing-off-camera live receipt using the final Tapo camera setup
- recorded demo screenshots of review packet, escalation evidence, and OBS handoff

## How To Read SQLite Proof

SQLite is the machine-readable blackbox. The demo does not need a separate database UI to prove the engine, but it should show at least one receipt rendered from SQLite:

```bash
python3 apps/caresight-hub/scripts/care_console.py blackbox-receipt <event_id> --format markdown
```

For judges, that receipt is enough to show the engine shape. For product work, a richer care journal UI can come later.

