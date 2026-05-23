# Decisions

## 2026-05-18: Adopt Project Scaffold as CareSight Governance Backbone

CareSight Hub uses the TypeScript scaffold for contracts, validation, governance, quality gates, and agent operating rules. Runtime implementation lives separately in `apps/caresight-hub/`.

Rationale: this preserves the scaffold's contract-first strengths while avoiding a mixed TypeScript/Python implementation boundary.

## 2026-05-18: Keep CareSight Local-First and Human-Confirmed

CareSight events are local structured observations. The system may alert caregivers and create journals, but it must not autonomously dispatch emergency services, diagnose medical conditions, or confirm medication administration from vision alone.

Rationale: the hackathon demo should show responsible AI boundaries through schemas, examples, and implementation constraints.

## 2026-05-18: Clone YOLO26 MLX as Vendored Runtime Dependency

The upstream `thewebAI/yolo-mlx` repository is cloned under `apps/caresight-hub/vendor/yolo-mlx` for local testing and troubleshooting. CareSight-owned glue scripts live in `apps/caresight-hub/scripts/` and runtime code stays in `apps/caresight-hub/caresight/`.

Rationale: this keeps the challenge-critical YOLO26 MLX implementation close enough for offline inspection and debugging while preserving a clear boundary between AGPL upstream code and CareSight-specific runtime work.

## 2026-05-18: Make v0 Review Human-Gated and Agent-Ready

CareSight v0 review commands may list and summarize local events, but confirm/dismiss transitions require an explicit human reviewer. Each review creates a durable review row, journal row, and report-only agent handoff payload.

Rationale: this proves the first agent-ready lifecycle while preserving the bounded control loop and preventing autonomous emergency dispatch, medical diagnosis, or agent-owned acknowledgement.

## 2026-05-19: Use AGPL-3.0-Only for the Hackathon Repository

CareSight Hub uses `AGPL-3.0-only` for the public hackathon repository. The current runtime depends on the `thewebAI/yolo-mlx` submodule, which is also licensed under `AGPL-3.0-only`.

Rationale: this keeps the hackathon build open, inspectable, and compatible with the current YOLO MLX dependency posture while leaving future commercial packaging, support, managed updates, hardware compatibility, and other service layers as separate product decisions.

## 2026-05-19: Keep v0 Audit Read-Only and SQLite-Canonical

The v0 audit command reads event, observation, review, journal, and handoff rows from SQLite and does not mutate event lifecycle state. Review lifecycle mutations still require an explicit human reviewer, and automation-like reviewer names are rejected.

Rationale: this lets operators and agents inspect the blackbox chain without making generated summaries, dashboards, scripts, agents, or LLM output canonical truth.

## 2026-05-19: Put Review Lifecycle Mutations Behind a Shared Service

CareSight v0 review lifecycle actions route through `caresight.runtime.review.ReviewService`. The CLI is one adapter over that service, and future console buttons should call the same service rather than creating separate confirm, dismiss, journal, or handoff logic.

Rationale: a single review boundary keeps reviewer validation, SQLite blackbox writes, report-only agent handoffs, and forbidden automation actions consistent across operator surfaces.

## 2026-05-19: Keep Inference Adapter Fail-Closed and Observation-Normalized

CareSight-owned inference code lives under `apps/caresight-hub/caresight/runtime/inference/`. The adapter loads YOLO26 MLX only when the configured model is present and importable, returns raw detections from actual model output, and normalizes those detections into observations with configured camera and room metadata.

Rationale: downstream event policies need stable CareSight observations, but the demo must not synthesize detections or hide model/runtime failures behind plausible-looking output.

## 2026-05-19: Start Tracking with a Lightweight Deterministic State Machine

CareSight starts v1 tracking with a local IoU-based track state machine instead of adding a heavier tracker dependency. Floor-stay events now require a stable `track_id` to remain in the configured low zone, and missing-off-camera is represented as a separate human-review event when a known track is absent beyond the configured window.

Rationale: the hackathon build needs track-aware event semantics and SQLite-visible `track_id` evidence before comparing ByteTrack or BoT-SORT. The lightweight state machine is deterministic, testable, and keeps emergency dispatch, diagnosis, and medication claims out of the tracking layer.

## 2026-05-19: Keep Routine Events Deterministic and Human-Confirmed

Medication and hydration routine events require a person in the configured routine zone, narrow configured object-label evidence, and a routine time window. These events are recorded as `*_likely_observed` and remain `awaiting_human_confirmation`.

Rationale: routine awareness is useful for the demo, but vision must not claim that medication was taken, hydration was medically sufficient, or any care action was confirmed without an authorized human.

## 2026-05-19: Keep Dashboard and Alert Drafts Presentation-Only

The local care console renders dashboard state and caregiver alert drafts from SQLite through `ReviewService`. It may show review controls and draft text-to-FaceTime escalation wording, but delete, dispatch, diagnosis, and confirmation remain outside presentation code.

Rationale: the demo needs a visible care surface, but SQLite remains the blackbox source of truth and the review service remains the only lifecycle mutation boundary.

## 2026-05-19: Constrain Agents to Provenance-Bearing Drafts and Audits

CareSight agents may summarize structured events, draft caregiver or journal wording, and audit handoff payloads only when outputs include purpose and event provenance. Agents must not confirm, dismiss, delete, dispatch, diagnose, confirm medication, or inspect raw video as the decision-maker.

Rationale: agent assistance can make the demo more useful, but it must remain downstream of SQLite truth and human review.

## 2026-05-19: Preserve Existing SQLite Blackbox Rows During Schema Upgrades

CareSight initialization applies additive SQLite schema upgrades such as adding `event_observations.track_id` to existing local databases. Upgrade logic must preserve prior rows and avoid destructive rewrites.

Rationale: local SQLite is the blackbox source of truth. New sprint fields should not require deleting earlier event evidence.

## 2026-05-20: Make Live Proof Collection Bounded

The v0 live loop supports `--max-seconds` and `--stop-after-event` so an operator can collect one `event_persisted` receipt without leaving the process open-ended.

`--stop-after-event` is proof/demo behavior only. Monitoring-style runs should omit it so CareSight continues observing after a persisted event.

Rationale: live demo proof should be operationally repeatable and auditable without forcing a GUI quit path or an unbounded process.

## 2026-05-20: Keep Live CLI Help Independent of Camera Runtime Imports

`v0_floor_stay_live.py` parses arguments before importing OpenCV or YOLO26 MLX, and it adds the vendored YOLO path before live runtime imports.

Rationale: operators need a reliable readiness/help command even on shells where camera/model runtime dependencies are unavailable.

## 2026-05-20: Keep Live-Proof Audit Bundles Read-Only

`live_proof_audit.py` collects readiness and post-event audit bundles without writing SQLite rows. It accepts an operator-supplied fresh `event_id`, reads event, observation, review, journal, and handoff records from SQLite-backed services, and includes dashboard and alert provenance only as derived outputs.

Rationale: live proof should become easier to audit without letting stale rows, dashboards, alerts, agents, or scripts become canonical truth or perform lifecycle actions.

## 2026-05-20: Keep Multi-Camera Support Deterministic and Local-Configured

CareSight v0 supports configured source selection for `webcam`, `usb`, `continuity_camera`, and local `rtsp` sources by camera ID or unambiguous source type. The runtime rejects cloud/provider camera scope and credential-bearing RTSP URLs, and it still writes selected camera provenance through the existing SQLite event path.

Rationale: the demo needs credible multi-camera setup without claiming live proof, adding discovery, handling credentials, or making any source other than SQLite canonical for event lifecycle state.

## 2026-05-20: Keep Sprint 01 Demo Packets and Receipts Read-Only

Human review packets and blackbox receipts are derived from SQLite audit-chain records. They may summarize evidence, review state, journal counts, report-only handoffs, dashboard inclusion, and alert-draft provenance, but they must not create events, confirm, dismiss, delete, dispatch, diagnose, or become canonical truth.

Rationale: the demo needs a clean, repeatable proof surface for judges and future agents while preserving the bounded control loop and keeping SQLite plus authorized human review as the authority boundary.

## 2026-05-21: Keep Sprint 02 Agent Actions Staged Before OpenClaw/Hermes

Sprint 02 implements a CareSight-owned fake provider, `agent_drafts`, and `agent_action_requests` before any OpenClaw or Hermes agent surface. OpenClaw/Hermes may later wrap staged requests for Apple Notes, iMessage, FaceTime, OBS, or TTS, but they must not bypass CareSight policy, SQLite provenance, forbidden-claim validation, or human approval.

Rationale: OpenClaw and Hermes are useful because they provide service integrations, not because they should become the authority layer. CareSight must own the contract, staging, audit, and approval boundary before service-capable agents are connected.

## 2026-05-21: Keep Downloaded MLX Models Local and Ignored

Gemma and Holler MLX model artifacts are local runtime dependencies under `apps/caresight-hub/models/` and are ignored by Git. The local model folder is organized by purpose lane: `vision/yolo26-mlx/`, `reasoning/gemma/`, and `tts/holler/`. Repo commits should track manifests, audit notes, config, and integration code, not multi-gigabyte model weights.

Rationale: the hackathon appliance needs local model availability, but public Git history should stay portable and avoid committing large generated artifacts. Purpose lanes keep future provider code from treating every MLX artifact as interchangeable.

## 2026-05-21: Trial Hermes Before OpenClaw for CareSight Service Wrappers

CareSight will prefer Hermes for the first controlled harness trial because its current docs show a direct BlueBubbles iMessage route and broad self-hosting/integration posture. OpenClaw remains the gateway/policy fallback because its docs expose strong pairing, allowlist, session, and config-write controls.

Rationale: the first harness should prove user-visible service routing without weakening CareSight's staging boundary. Hermes appears to be the simpler first route for iMessage/Notes/FaceTime-style workflows, while OpenClaw is valuable when gateway control and multi-agent routing become more important.

## 2026-05-21: Serve Hermes Through a Local OpenAI-Compatible Endpoint

CareSight vendors Hermes as a pinned workspace dependency and configures it to use a local OpenAI-compatible endpoint for Gemma MLX by default. OpenRouter and other hosted routers remain explicit cloud fallback options only.

Rationale: Hermes provides the service-capable agent surface, but CareSight still needs local-first privacy, SQLite provenance, and bounded staging. A local endpoint lets Hermes use the Gemma reasoning lane without sending care context to a hosted router by default.

## 2026-05-21: Treat Hermes Upstream Files as External Vendor Content

CareSight scaffold validation tracks the Hermes submodule through `.gitmodules`, CareSight-owned config templates, docs, and audit records, but it does not recurse through the upstream Hermes working tree for file-tree or placeholder governance.

Rationale: Hermes carries its own docs, skills, examples, and template placeholders that are not CareSight contract placeholders. Validating those upstream files as CareSight-owned governance would create false failures and make the local file tree noisy without improving CareSight safety.

## 2026-05-21: Make Emergency Contact Escalation a Bounded Ask

CareSight urgent handoffs may target an allowlisted emergency-contact role, but the staged message must ask for human direction instead of initiating a call or attaching media. The current supported options are text acknowledgement, local screen capture by request, and FaceTime handoff by request.

Rationale: escalation should help caregivers act quickly without making CareSight an emergency dispatch system or letting Hermes control cameras, calls, messages, or raw video by default.

## 2026-05-21: Sprint Done Means Operationally Ready

CareSight sprint status must not call a sprint complete when only contracts, fixtures, templates, fake providers, staged payloads, or dry-run surfaces exist. Those are implementation milestones. A sprint is production-ready only when the real local runtime path is configured, exercised end to end, human-validated where required, and backed by an audit receipt.

Rationale: the project is safety-sensitive and local-first. Overstating scaffolded or staged behavior as complete weakens trust and makes it harder to see which human and runtime gates remain.

## 2026-05-21: Persist Normal No-Event Checks Separately From Events

Bounded normal/no-event runs are local continuity evidence and should be persisted as `observation_checks` rows in SQLite. They prove the system was online for a configured window and did not create a concerning event. They must not become reviewable care events, human-review packets, emergency escalations, or blackbox receipts for event chains unless a real event is created.

Rationale: normal presence is useful for operational confidence and non-escalation testing, but treating no-event checks as care events would blur the bounded control loop and create misleading review surfaces.

## 2026-05-21: Log External-Action Attempts Before Live Execution

CareSight stores dry-run external-action attempts in `agent_execution_attempts` before any live Hermes, iMessage, FaceTime, Apple Notes, or TTS path is enabled. A dry-run attempt records the staged request ID, event ID, harness, payload snapshot, execution state, result, safety boundaries, and `external_action_performed: false` while leaving the source action request in `not_executed`.

Rationale: Sprint 02 needs inspectable service-wrapper receipts without letting a payload render become an implicit send/call/write. Persisting attempts separately preserves the bounded control loop and creates a durable audit layer for later human-approved live actions.

## 2026-05-21: Use Redacted Contact IDs for Live-Contact Staging

CareSight iMessage and FaceTime staging validates requested contact IDs against a redacted local allowlist. Git-tracked examples may include stable IDs, roles, display labels, and redacted channel references, but not phone numbers, addresses, passwords, tokens, or BlueBubbles credentials.

Rationale: service-capable handoff paths need deterministic allowlist checks before dry-run or live harness work, but caregiver contact details are private operational data and must stay out of committed repo files.

## 2026-05-21: OBS Visual Handoff Uses Browser Source Overlays

CareSight visual handoff scenes should be created through OBS websocket using a small number of stable OBS sources: camera/image/video feeds plus local browser-source overlays from `apps/obs-hub/`.

Rationale: browser overlays keep caregiver-facing text, event cards, recent activity, and future local API updates in HTML/CSS/JS instead of brittle native OBS text-source layers. This preserves scriptability and makes FaceTime/OBS Virtual Camera demos reproducible.

The default visual language remains bounded: possible floor-stay, review required, draft caregiver alert prepared, raw video stays local, and human review required. It must not show diagnostic, medical-device, emergency-dispatch, or raw confidence claims by default.

## 2026-05-22: Prefer Dual OBS Output Targets for FaceTime

CareSight should prefer a dual-output OBS model for live caregiver handoff: the normal OBS canvas remains landscape for desktop/operator review, and an optional Aitum Vertical Canvas output owns the phone-oriented FaceTime surface. Plain OBS portrait output remains a fallback when the plugin is not installed.

Rationale: OBS video settings are profile-global, not scene-local. Mutating the main OBS output from landscape to portrait during a call makes desktop review unstable and creates confusing preview behavior. A separate vertical canvas matches how multi-stream operators handle desktop and mobile outputs and lets CareSight keep purpose-built views for each recipient device.

## 2026-05-21: Alert Lifecycle Needs Follow-Up And Resolution Updates

The approved initial Gemma wording is concise enough for the immediate validation path, but the operator requested time relevance, unresolved-alert follow-up cadence, and a resolution update with estimated total duration.

Future alert lifecycle behavior should keep these as bounded updates and must not say the person is stable, injured, diagnosed, or receiving autonomous emergency dispatch.

## 2026-05-21: Keep OBS Scenes Stable And Update Overlay State

CareSight OBS scenes should remain stable after setup. Dynamic event data should flow through `apps/obs-hub/config/current_event.json`, written by `scripts/update_obs_overlay.sh` from SQLite-derived context.

Rationale: local Gemma/Hermes tooling needs a simple command/tool surface it can invoke safely. Rewriting a local overlay-state JSON file is safer and more reproducible than letting agents create OBS text sources, modify scene graphs, or touch raw video feeds for every alert.

The caregiver-facing OBS panel should use shortened event IDs to preserve layout, while full IDs remain in SQLite, ignored overlay state files, and audit receipts.

## 2026-05-21: Start Post-Event Agent Automation In No-Send Mode

The live detector may automatically run the local post-event agent pipeline after persisting an event behind `--auto-agent-dry-run`. That pipeline may update OBS overlay state, draft with local Gemma, stage an allowlisted iMessage request, and run Hermes no-send preflight.

Rationale: this gives the demo a realistic event-to-alert path without hiding live external actions behind detection. Live iMessage, FaceTime, TTS playback, and visual handoff execution remain explicit human gates.

## 2026-05-21: Keep Live Handoffs Explicit And Reply-Gated

CareSight may run a bounded `--auto-agent-live-run` only when the operator provides `--live-approved` and a private allowlisted contact target outside Git. The live detector may send the approved iMessage after a persisted event, but it must not automatically start FaceTime without an affirmative caregiver reply supplied to the reply-gated handoff command.

Rationale: the hackathon test needs a realistic text-to-visual-handoff path, but automatic call initiation and message-database polling would weaken the bounded control loop. Keeping the FaceTime step reply-gated preserves human approval, contact privacy, and local auditability.

The live demo may optionally use `imsg` or watch `~/Library/Messages/chat.db` after the alert is sent when the operator enables `--auto-facetime-on-reply`. This requires macOS Full Disk Access and is constrained to the configured target handle and the post-alert time window.

Rationale: automatic reply detection is useful for the demo, but it is private local data. It should be explicit, time-bounded, target-bounded, and fail closed when the OS denies access.

## 2026-05-21: Route TTS Audio Temporarily For FaceTime

CareSight may use `BlackHole 2ch` plus `switchaudio-osx` to route approved Dakota TTS into a FaceTime handoff, but only for the playback window. The script records the current input/output devices, switches both to `BlackHole 2ch`, runs TTS playback, and restores the prior devices afterward.

Rationale: OBS Virtual Camera only solves the visual handoff. Audio needs a separate local route, and the operator should not have their microphone permanently changed for the demo.

## 2026-05-21: Feed OBS From Detector-Owned Annotated Frames

For the live FaceTime demo, the detector serves an annotated local MJPEG feed from `http://127.0.0.1:8766/stream.mjpg`, and the OBS browser overlay displays that stream as the active feed. OBS should not open the same webcam as the detector for this path.

Rationale: macOS camera ownership can make OpenCV and OBS fight over the same camera. A local MJPEG browser feed keeps raw video local, lets OpenCV remain the camera owner, and gives caregivers the same boxed detector view through OBS Virtual Camera.

`apps/obs-hub/config/live_preview.jpg` remains useful as a fallback/debug artifact, but it is not the primary live-video transport.

## 2026-05-22: Keep Escalation Evidence Event-Scoped

Each live or dry-run escalation attempt should be readable back through the originating `event_id`. The event-scoped escalation receipt links local event evidence, agent drafts, staged action requests, execution attempts, OBS overlay state, and the detector preview path without creating a new care event or exposing private contact targets.

Rationale: caregivers and demo operators need a clean audit trail for what happened after an event. Keeping the receipt read-only and event-scoped preserves SQLite as source of truth while making iMessage, FaceTime, TTS, and OBS evidence inspectable.

## 2026-05-22: Keep Daily Appearance Profiles Non-Biometric And Same-Day

Sprint 03 appearance profiles are local SQLite records derived from real event observations and local snapshots. They may store coarse clothing descriptors, last-seen room/camera/time, event provenance, track context, same-day continuity hints, and human-assigned daily roles.

They must not identify named people, perform face recognition, claim biometric identity, link identity across days, store raw face crops as canonical truth, diagnose, detect falls, or dispatch help. Missing, unreadable, or invalid image evidence must produce an unavailable descriptor status rather than hallucinated attributes.

Periodic appearance samples may be stored only behind quality gates and capped retention per profile/day. Event snapshots remain audit evidence; they are not automatically trusted as the best appearance descriptor frame.

Rationale: caregivers need bounded context such as "unknown-person profile for today; blue upper clothing; last seen in Living Room," but clothing is not identity, stale daily descriptors can mislead, and a single prone or occluded event frame can produce false appearance claims.
