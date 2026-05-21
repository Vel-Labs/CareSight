# Sprint 02 Agent and Model Surface Audit

Date: 2026-05-21

## Summary

Sprint 02 now has a CareSight-owned agent-assist surface for contracts, fake-provider drafts, SQLite persistence, and staged action requests. It does not install or wire OpenClaw or Hermes yet.

The service-capable agent surface remains a follow-up integration: OpenClaw/Hermes may wrap Apple Notes, iMessage, FaceTime, OBS, or TTS only after CareSight-owned staging, policy, provenance, and human-approval checks remain the authority boundary.

## Current Agent Surface

- Implemented: CareSight fake provider.
- Implemented: `agent_drafts` SQLite table.
- Implemented: `agent_action_requests` SQLite table.
- Implemented: `care_console.py agent-draft`.
- Implemented: `care_console.py stage-action-request`.
- Implemented: `care_console.py list-action-requests`.
- Not implemented: OpenClaw install.
- Not implemented: Hermes install.
- Not implemented: Apple Notes writes.
- Not implemented: iMessage sends.
- Not implemented: FaceTime launch.
- Not implemented: external action execution.

## Local Model Downloads

The following model artifacts were downloaded into ignored local runtime paths, grouped by purpose lane:

| Model | Local path | Local size |
| --- | --- | ---: |
| YOLO26 MLX converted model | `apps/caresight-hub/models/vision/yolo26-mlx/converted/yolo26n.npz` | symlink to vendored YOLO model cache |
| YOLO26 MLX upstream cache | `apps/caresight-hub/models/vision/yolo26-mlx/upstream/models` | symlink to vendored YOLO model cache |
| `mlx-community/gemma-4-e2b-it-4bit` | `apps/caresight-hub/models/reasoning/gemma/gemma-4-e2b-it-4bit` | 3.4G |
| `mlx-community/gemma-4-e4b-it-4bit` | `apps/caresight-hub/models/reasoning/gemma/gemma-4-e4b-it-4bit` | 4.9G |
| `sentiuminc/holler-0.6b` | `apps/caresight-hub/models/tts/holler/holler-0.6b` | 2.3G |
| `sentiuminc/holler-0.6b-6bit` | `apps/caresight-hub/models/tts/holler/holler-0.6b-6bit` | 1.7G |

Model artifacts are intentionally ignored by Git through `apps/caresight-hub/models/`.

## Model Lane Contract

Use these lanes for future local model setup and provider code:

- `apps/caresight-hub/models/vision/yolo26-mlx/`: vision models and symlinks for YOLO26 MLX.
- `apps/caresight-hub/models/reasoning/gemma/`: Gemma MLX reasoning/summarization candidates.
- `apps/caresight-hub/models/tts/holler/`: Holler MLX text-to-speech candidates.

Provider code should reference purpose lanes instead of a generic `models/mlx/` bucket.

## Recommendation

Use `mlx-community/gemma-4-e2b-it-4bit` as the first Gemma provider candidate for the 16 GB Mac mini budget because it leaves more headroom for YOLO26, camera capture, SQLite, and the dashboard.

Use `sentiuminc/holler-0.6b-6bit` as the first TTS candidate because it is the smaller/lower-RAM Holler option.

Do not wire either model into caregiver-visible actions until the provider task measures memory and latency with the rest of CareSight running.

## Validation

- `npm run check`: passed before this audit correction.
- `apps/caresight-hub/models/reasoning/gemma/*`: present locally after `hf download`.
- `apps/caresight-hub/models/tts/holler/*`: present locally after `hf download`.
- `apps/caresight-hub/models/vision/yolo26-mlx/*`: present locally as purpose-lane symlinks to the existing YOLO26 model cache.
- `git status --ignored apps/caresight-hub/models`: model directories are ignored after the `.gitignore` update.

## Remaining Gate

Next implementation should add a measured local provider task with explicit stop conditions:

- no cloud inference
- no raw-video or image bytes sent to the language model
- no OpenClaw/Hermes execution bypass
- no Apple Notes, iMessage, or FaceTime action without staged request plus human approval
- memory and latency measured on the 16 GB target while YOLO26/camera/dashboard are active
