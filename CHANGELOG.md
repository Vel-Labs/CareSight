# Changelog

## Unreleased

- Added CareSight OBS Hub scene setup with browser-source overlays, local websocket-driven scene creation, dry-run planning, and FaceTime/OBS Virtual Camera operator docs.
- Added a dynamic OBS overlay-state update tool so local agents can refresh event and recent-activity context from SQLite without rebuilding OBS scenes.
- Added OBS overlay watch mode for live sessions and shortened caregiver-facing event IDs while preserving full IDs in SQLite/audit state.
- Added a live-detector `--auto-agent-dry-run` path that automatically updates OBS overlay state, creates a local Gemma alert draft, stages an allowlisted iMessage request, and records Hermes no-send preflight after an event is persisted.
- Recorded 2026-05-21 human validation feedback: Gemma wording approved, Dakota requested for final TTS playback, OBS browser-overlay scene direction approved, and `contact_emergency_primary` approved for iMessage/FaceTime testing without tracking real contact details.
- Added requested alert lifecycle follow-up cadence notes for unresolved alerts and resolution updates with total-duration estimates.
- Added production-validation Sprint 01 Case A artifacts for the accepted seeded-real event: generated review packet and blackbox receipt JSON plus skimmable Markdown companions under `docs/audits/production-validation/sprint-01/`.
- Reworked Sprint 01 review-packet and blackbox-receipt Markdown output into clear human-facing summaries while keeping JSON as the machine/audit receipt format.
- Recorded human acceptance of the Case A Markdown direction as an actionable audit receipt surface, with evidence-label translation and future concise Gemma alerts kept as follow-up boundaries.
- Captured the normal-desk Case B attempt as a false-positive/over-trigger finding, clarified live-loop terminal output for no-event proof receipts, fixed repo-root resolution for relative runtime DB paths, and added a low-posture regression guard.
- Recorded the passing Case B normal-desk no-event proof and marked Case B packet/receipt generation as not applicable because no event was created.
- Added SQLite persistence for bounded normal/no-event observation checks so periodic safe-state runs can prove continuity without creating reviewable care events.
- Recorded the Sprint 02 local Gemma endpoint gate and kept it blocked until a local OpenAI-compatible endpoint can actually serve a compatible model.
- Installed a repo-local ignored runtime environment for Sprint 02 model/handoff checks, proved the Holler TTS model can generate a local WAV with the `kit` voice, and updated the OBS/FaceTime/TTS receipts to reflect tooling readiness versus remaining human validation gates.
- Re-tested both local Gemma 4 MLX candidates through `mlx_lm.server`; the runtime dependencies are present, but both model packages fail to load with weight/config mismatch errors, so real Gemma drafting remains blocked.
- Identified `mlx-vlm.server` as the local runner for the already-present Gemma 4 E2B MLX model and proved an OpenAI-compatible `/v1/chat/completions` smoke response locally with no cloud fallback.
- Added repeatable local operations scripts for starting/stopping the Gemma endpoint and generating Holler TTS audio, plus getting-started and local model operations docs.
- Added Hermes readiness and stack start/stop scripts so the local test stack can bring Gemma online, pulse-check chat completions, verify Hermes no-send readiness, and stop cleanly.
- Added a local `gemma_mlx` agent-draft provider path for SQLite-derived audit context, generated the Case A Gemma draft/no-send Hermes receipts, and recorded Case B Gemma non-escalation.
- Added an explicit macOS live-handoff harness for human-approved iMessage sends and reply-gated FaceTime opening, with private contact targets kept out of Git and persisted execution receipts redacting target handles.
- Added an automatic demo mode that can watch local Messages for a yes-like reply, open FaceTime to the allowlisted contact, and play approved Dakota TTS after the handoff starts.
- Added optional `imsg` reply-watch support and a BlackHole/SwitchAudioSource audio-route check so Dakota TTS can be routed into FaceTime only during the triggered handoff.
- Added an OBS live-preview image path from the detector so the FaceTime handoff can show annotated YOLO frames without OBS opening the camera separately.
- Added `--debug-floor-stay` live-loop diagnostics so operator tests can see why a person box is or is not being counted as a floor-stay candidate before the iMessage/FaceTime path runs.
- Added FaceTime/TTS timing controls so the automatic handoff waits briefly after call initiation, plays an automated CareSight message, and holds the live process open for a bounded review window.
- Corrected the FaceTime pre-call coordinate fallback so the live handoff clicks the visible video-call control instead of only opening the FaceTime pre-call sheet.
- Added a portrait-safe `CareSight Hub - FaceTime Mobile` OBS scene for phone recipients and switched live FaceTime handoffs to request that scene before calling.
- Added local TTS playback volume control so FaceTime handoff audio can be boosted through `afplay` while keeping generation local.
- Added a bounded no-response iMessage escalation that sends one follow-up with the local event snapshot attached before continuing to wait for a yes-like reply.
- Added a short BlackHole hold after TTS playback so the virtual call input is not restored immediately at the end of the utterance.
- Added a dedicated OBS `CareSight FaceTime Live Detector Preview` source and overlay fallback for `live_preview.jpg` so the FaceTime scene has an explicit detector-feed source instead of relying only on event JSON.
- Added local browser-feed refresh for OBS escalation and FaceTime Mobile overlays so `live_preview.jpg` updates continuously during detector-owned camera runs.
- Added an ignored caregiver contact config initializer, live-demo preflight checker, and event-scoped escalation receipt command linking drafts, requests, execution attempts, OBS state, and preview evidence.
- Added install/setup wrappers for the local runtime, Gemma/Holler models, OBS, full prerequisite install, fixture setup, and a machine-readable command registry.
- Added SQLite execution-attempt logging for dry-run external-action receipts before any Hermes/iMessage/FaceTime/TTS live path is enabled.
- Added redacted contact allowlist handling for iMessage/FaceTime staging and blocked unconfigured contact IDs without committing real contact details.
- Added a Hermes no-send dry-run preflight command that records a local execution-attempt receipt, works through the existing YOLO MLX venv, and redacts raw Hermes target names from persisted output.
- Recorded the seeded-real Case A Sprint 02 path: fake-provider alert draft, urgent allowlisted action request, Hermes handoff payload, and blocked no-send Hermes dry-run receipt.
- Recorded the seeded-real Case B Sprint 02 non-escalation path as not applicable for drafts, action requests, and Hermes dry-runs because the normal-desk run persisted no care event.
- Updated screen-capture/OBS readiness from missing tooling to scene/privacy-confirmation pending after OBS and `obsws_python` were verified locally.
- Updated FaceTime/TTS approval receipts after operator approval: FaceTime remains setup/contact-mapping pending, while TTS generation is proven and playback validation remains pending.
- Recorded FaceTime/TTS execution as not yet performed because live call, visual handoff, and audio playback still require the remaining human validation gates.
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
- Corrected Sprint 01/Sprint 02 status language to distinguish implemented staging surfaces from production-ready operation and listed the remaining human/runtime gates.
- Added a Sprint 01/02 production validation checklist for seeded-real A/B validation, Sprint 02 product requirements, and production acceptance gates.

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
