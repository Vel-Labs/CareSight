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

The following model artifacts were downloaded into ignored local runtime paths:

| Model | Local path | Local size |
| --- | --- | ---: |
| `mlx-community/gemma-4-e2b-it-4bit` | `apps/caresight-hub/models/mlx/gemma-4-e2b-it-4bit` | 3.4G |
| `mlx-community/gemma-4-e4b-it-4bit` | `apps/caresight-hub/models/mlx/gemma-4-e4b-it-4bit` | 4.9G |
| `sentiuminc/holler-0.6b` | `apps/caresight-hub/models/mlx/holler-0.6b` | 2.3G |
| `sentiuminc/holler-0.6b-6bit` | `apps/caresight-hub/models/mlx/holler-0.6b-6bit` | 1.7G |

Model artifacts are intentionally ignored by Git through `apps/caresight-hub/models/`.

## Recommendation

Use `mlx-community/gemma-4-e2b-it-4bit` as the first Gemma provider candidate for the 16 GB Mac mini budget because it leaves more headroom for YOLO26, camera capture, SQLite, and the dashboard.

Use `sentiuminc/holler-0.6b-6bit` as the first TTS candidate because it is the smaller/lower-RAM Holler option.

Do not wire either model into caregiver-visible actions until the provider task measures memory and latency with the rest of CareSight running.

## Validation

- `npm run check`: passed before this audit correction.
- `apps/caresight-hub/models/mlx/*`: present locally after `hf download`.
- `git status --ignored apps/caresight-hub/models`: model directories are ignored after the `.gitignore` update.

## Remaining Gate

Next implementation should add a measured local provider task with explicit stop conditions:

- no cloud inference
- no raw-video or image bytes sent to the language model
- no OpenClaw/Hermes execution bypass
- no Apple Notes, iMessage, or FaceTime action without staged request plus human approval
- memory and latency measured on the 16 GB target while YOLO26/camera/dashboard are active
