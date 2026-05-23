# CareSight Hub Scripts

This folder contains the Python operator and validation commands for the local runtime. The complete CLI registry lives in `docs/cli/COMMANDS.md`; this file is the practical run index.

## Setup

| Script | Use |
| --- | --- |
| `caresight_install_all.py` | Install local runtime prerequisites, models, OBS helper pieces, and fixtures. |
| `caresight_install_runtime.py` | Install Python runtime dependencies. |
| `caresight_install_model.py` / `caresight_install_models.py` | Prepare local model artifacts. |
| `caresight_install_obs.py` | Prepare OBS helper assets. |
| `caresight_demo_preflight.py` | Check local demo prerequisites without starting the full stack. |

## Camera Configuration

| Script | Use |
| --- | --- |
| `caresight_camera_discover.py` | Owner-authorized LAN discovery and local RTSP config scaffolding. |
| `caresight_camera_probe.py` | Confirm an RTSP config can open and read the first frame. |
| `caresight_camera_view.py` | Open a simple local camera preview for operator validation. |

## Utilization

| Script | Use |
| --- | --- |
| `caresight_detector_start.py` | Start configured detector workers and expose local OBS browser feeds. |
| `v0_floor_stay_live.py` | Single-camera live detector loop for bounded proofs and development. |
| `care_console.py` | Render dashboard, review packet, blackbox receipt, escalation receipt, narrative, and staged action state. |
| `caresight_stack_start.py` / `caresight_stack_stop.py` | Start or stop the local no-send model/handoff stack. |

## Handoff And Media

| Script | Use |
| --- | --- |
| `caresight_live_handoff.py` | Explicitly approved local iMessage/FaceTime handoff helper. |
| `caresight_tts.py` | Local text-to-speech helper. |
| `caresight_audio_route.py` | Local audio route helper for BlackHole/system routing. |
| `caresight_contacts_config.py` | Local contact allowlist setup helper. |

## Validation And Developer Tools

| Script | Use |
| --- | --- |
| `live_proof_audit.py` | Collect live proof audit context. |
| `v0_review_events.py` | Inspect v0 event state. |
| `yolo26_image_smoke.py` | Run still-image YOLO smoke checks. |
| `yolo26_webcam_smoke.py` | Run webcam YOLO smoke checks. |
| `caresight_yolo26_appearance_review.py` | Render appearance review overlays for validation images. |

## Current Demo Start

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python \
  apps/caresight-hub/scripts/caresight_detector_start.py \
  --appearance-overlay \
  --stop-existing
```

