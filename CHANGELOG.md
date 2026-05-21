# Changelog

## Unreleased

- Added Sprint 02 agent-assist contract schemas and corpus examples for forbidden claims, agent drafts, staged action requests, and TTS utterances.
- Added a fake agent provider boundary that stores validated and blocked drafts in local SQLite without calling Gemma, OpenClaw, TTS, or external services.
- Added Care Console commands for fake-provider agent drafts and staged-only action requests, including list/readback coverage and documentation.
- Downloaded the selected Gemma/Holler MLX model candidates into the ignored local runtime model directory and recorded an audit receipt.
- Reorganized local model artifacts into purpose lanes for vision, reasoning, and TTS.
- Clarified that OpenClaw/Hermes are not installed agent surfaces yet; they remain future wrappers behind CareSight action-request policy.
- Added a non-executing Hermes/OpenClaw harness planning layer for staged action requests, including iMessage and FaceTime handoff planning.
- Vendored Hermes as a pinned workspace submodule and added safe local config templates for routing Hermes to a local OpenAI-compatible Gemma MLX endpoint.
- Updated scaffold validation so upstream Hermes submodule files are treated as external vendor content rather than CareSight-owned placeholder/file-tree material.
- Added staged Hermes handoff payloads with escalation level, emergency-contact allowlists, and bounded response options for text updates, local screen capture by request, and FaceTime handoff by request.

## 2026-05-20

- Reframed Sprint 07 as a contract continuity audit; implementation sprints now absorb the contract pieces they consume before runtime behavior.
- Recorded the Sprint 01 demo surface audit receipt and read-only authority decision for review packets and blackbox receipts.
- Added `care_console.py review-packet` and `blackbox-receipt` read-only commands, plus focused dashboard backlog separation for Sprint 01.
- Added read-only demo surface builders for human review packets and blackbox receipts derived from SQLite audit chains.
- Added Sprint 01 contract schemas and corpus examples for human review packets and blackbox receipts.
- Clarified the sprint-pack execution order as `01 -> 02 -> 03 -> 04 -> 05 -> 06 -> 07 -> 08`, with Sprint 07 as a continuity audit rather than a standalone build step.
- Added the CareSight sprint pack to the roadmap index and updated the current-state roadmap with direct sprint-pack links, review notes, and Sprint 01 as the recommended next implementation lane.
- Documented Daily Appearance Profiles as a bounded future sprint: local-only, daily-refreshing, non-biometric person continuity using clothing/accessory descriptors, last-seen context, and optional human-assigned roles.
- Documented the Agent/LLM Drafting Layer as a bounded local Gemma MLX plus OpenClaw/Hermes orchestration path for caregiver text, Apple Notes drafts, handoff packets, and audit summaries.
- Added Open Questions sections to the current and hackathon roadmaps with suggested answers and rationale for unresolved product/architecture choices.
- Updated the current roadmap now that the live v0 blackbox loop is proven for `evt_d9aa38bdc636459c92ea4e25f665cd0d`.

## 2026-05-19

- Added deterministic multi-camera config/source selection for webcam, USB, Continuity Camera, and local RTSP sources without requiring camera authorization or live hardware proof.
- Added a read-only live-proof readiness and audit-bundle collector that reports camera authorization blockers and emits SQLite-backed provenance bundles for fresh operator-supplied event IDs.
- Added root `AGPL-3.0-only` license posture for the hackathon repository.
- Added `NOTICE.md` and `docs/legal/LICENSE_NOTES.md` to document YOLO MLX AGPL dependency posture, model-weight caution, and future commercial packaging boundaries.
- Updated `README.md` with license positioning and submodule clone instructions.
- Hardened the v0 live-loop review audit path with a read-only SQLite audit command, reviewer/timestamp handoff payload fields, and automation-reviewer rejection.
- Added a shared review service boundary so CLI and future console controls use the same reviewer-gated confirm/dismiss/journal/audit path.
- Added a CareSight-owned YOLO26 MLX inference harness with raw Detection records, normalized Observation records, config-first model/camera/room metadata, and fail-closed adapter behavior.
- Added deterministic track-aware floor-stay foundations with observation `track_id` persistence, short-occlusion continuity tests, dedupe/reset behavior, and an initial `missing_off_camera_extended` event policy.
- Added deterministic medication and hydration routine policies that require a person, configured object label evidence, a routine zone, and a routine window while keeping human confirmation mandatory.
- Added a local care console read model and caregiver alert draft path that reads SQLite through `ReviewService`, keeps delete/dispatch forbidden, and includes provenance.
- Added constrained agent policy checks and docs for summary/draft/audit actions with required provenance and forbidden confirmation, dismissal, deletion, dispatch, diagnosis, medication confirmation, and raw-video decision access.
- Added non-destructive SQLite schema upgrade handling so existing local `event_observations` tables gain `track_id` without deleting prior blackbox rows.
- Closed SQLiteStore database handles deterministically to remove unclosed-connection `ResourceWarning` noise from Python verification.
- Added bounded live-proof controls for `v0_floor_stay_live.py` with `--max-seconds` and `--stop-after-event`.
- Hardened `v0_floor_stay_live.py --help` so argument parsing works without OpenCV imports and live runs can resolve the vendored YOLO26 package path.

## 2026-05-18

- Adopted `Vel-Labs/project-scaffold` as the CareSight Hub repo backbone.
- Personalized root docs, project brief, architecture, boundaries, roadmap, decisions, and agent rules.
- Routed the CareSight docs pack into hackathon, roadmap, architecture, and reference lanes.
- Added CareSight contract schemas and examples for events, cameras, routines, alert policies, and caregiver roles.
- Added a bounded Python runtime skeleton under `apps/caresight-hub/`.
- Added `py:check` to the local quality gate.
- Cloned `thewebAI/yolo-mlx` under the CareSight runtime boundary and added local setup, model-prep, image smoke-test, and webcam smoke-test scripts.
- Recorded the YOLO26 MLX smoke checkpoint audit and routed v0 next work toward eventization and SQLite persistence.
- Implemented v0 floor-stay eventization with file-backed config, zone/dwell logic, SQLite tables, event observation persistence, live runner, and tests.
- Added local still snapshot capture for v0 floor-stay events, recorded in event evidence as local-only snapshot metadata.
- Added v0 review and acknowledgement CLI with event inbox, human-readable summaries, reviewer-gated confirm/dismiss, journal entries, report-only agent handoffs, and lifecycle tests.
- Added `docs/cli/COMMANDS.md` as the durable local CLI registry and updated agent rules for review-flow boundaries.
- Added README project ethos for an accessible open-source baseline plus future packaged/service value-adds.
