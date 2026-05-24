# Current State and Next

## Current State

CareSight Hub has adopted the project scaffold as its governance backbone:

- `contracts/` owns canonical care schemas and examples.
- `packages/core/` validates the contract corpus.
- `tests/` runs the shared local quality gate.
- `docs/hackathon/`, `docs/roadmaps/`, `docs/architecture/`, and `docs/references/` now route the imported docs pack.
- `apps/caresight-hub/` exists as the Python runtime boundary.
- YOLO26 MLX is installed under `apps/caresight-hub/vendor/yolo-mlx`.
- `yolo26n.npz` is converted and verified.
- Image and live webcam smoke tests work with usable visual quality, FPS/settings overlay, and COCO labels.
- Smoke checkpoint: `docs/audits/2026-05-18-yolo26-mlx-smoke-checkpoint.md`.
- v0 eventization implementation: `docs/audits/2026-05-18-v0-eventization-implementation.md`.
- v0 review and acknowledgement CLI: `apps/caresight-hub/scripts/v0_review_events.py`.
- Durable CLI registry: `docs/cli/COMMANDS.md`.
- v0 SQLite audit command: `python apps/caresight-hub/scripts/v0_review_events.py audit <event_id>`.
- CareSight-owned inference harness: `apps/caresight-hub/caresight/runtime/inference/`.
- Deterministic tracking foundation: `apps/caresight-hub/caresight/runtime/tracking/` with `track_id` event-observation persistence.
- Deterministic v1 routine policies: `medication_routine_likely_observed` and `hydration_routine_likely_observed`.
- Live proof event `evt_d9aa38bdc636459c92ea4e25f665cd0d` completed the v0 blackbox loop: live floor-zone observation, SQLite event and observation with `track_id`, authorized human confirmation, journal row, report-only handoff row, focused dashboard view, caregiver alert draft, and complete live-proof bundle.
- YOLO26 image smoke now reports human-readable COCO labels plus machine-readable `class_id` in normalized observations.
- Sprint 01 contract-backed demo surfaces are production-validated for the current seeded-real A/B scope: Case A has JSON plus skimmable Markdown review-packet and blackbox-receipt artifacts, and Case B has a normal/no-event proof showing non-escalation. Human feedback accepted the Markdown audit-receipt direction while keeping evidence-label translation and concise Gemma alerts as follow-up work.
- Sprint 01 demo surface audit receipt: `docs/audits/2026-05-20-sprint-01-demo-surface.md`.
- Sprint 02 agent-assist infrastructure is implemented but not production-ready: `agent-draft`, `agent-action-request`, `tts-utterance`, and `forbidden-claim-vocabulary` schemas/examples validate through the contract corpus, and production-validation receipts exist for staging, no-event non-escalation, execution-attempt logging, and blocked live gates.
- The Sprint 02 fake provider is a safety proof, not the finished provider: validated and blocked agent drafts are stored in SQLite through `agent_drafts`, with forbidden-claim reasons and safe rewrites for blocked drafts.
- Sprint 02 action-request staging is implemented as a pre-execution gate: `care_console.py agent-draft`, `stage-action-request`, and `list-action-requests` write and inspect local SQLite rows only. Staged requests remain `not_executed` and require human approval.
- Phase 1 live-handoff cleanup now requires allowlisted target matching, pre-execution `pending_execution` receipts before live iMessage/FaceTime/TTS actions, explicit `media-sharing-policy` approval for event snapshot attachments, and `reply-gated-handoff` receipts for FaceTime continuation.
- Local model candidates have been downloaded under ignored purpose lanes for follow-up provider benchmarking: `models/vision/yolo26-mlx/`, `models/reasoning/gemma/`, and `models/tts/holler/`.
- Hermes is vendored as a pinned workspace submodule at `apps/caresight-hub/vendor/hermes-agent`; OpenClaw remains uninstalled and available as the policy-heavy gateway fallback.
- Hermes is now the preferred first harness trial for staged iMessage/Notes/FaceTime-style actions. `care_console.py agent-harness-plan` renders non-executing routing plans only.
- `apps/caresight-hub/config/hermes/` contains safe repo-local Hermes templates for a local OpenAI-compatible Gemma MLX endpoint; OpenRouter is not required by default and remains an explicit cloud fallback only.
- Staged Hermes handoff payloads now support `routine`, `attention`, and `urgent_handoff` levels, allowlisted emergency-contact routing, and bounded response options for journal text updates, local screen capture by request, or FaceTime handoff by request.
- Production-validation receipts live under `docs/audits/production-validation/`. Current blockers are explicit: local Gemma E2B serves through `mlx-vlm.server`; Case A now has a validated `provider: gemma_mlx` draft, staged urgent handoff, and Hermes no-send receipt; Case B correctly produces no Gemma alert or urgent handoff because it is a normal/no-event check; live iMessage/BlueBubbles delivery is not approved/proven; OBS and `obsws_python` are present but need scene/privacy confirmation; TTS generation works locally from the Gemma message but playback needs human wording/tone validation.
- Sprint 02 no-call runtime audit on 2026-05-23 found the local demo preflight ready, Gemma endpoint reachable, BlackHole/SwitchAudioSource available, and Dakota TTS generation working with `played=false`. OBS live-feed validation remained blocked because the detector MJPEG server and OBS websocket were not running/reachable, and FaceTime/TTS playback remained intentionally unrun under the no-call boundary. See `docs/audits/2026-05-23-sprint-02-no-call-runtime-audit.md`.
- Sprint 03 Daily Appearance Profile foundations are implemented on the `codex/sprint-03-appearance` worktree branch: the contract corpus includes `appearance-profile`, SQLite stores same-day profile, observation, and capped sample rows, the runtime derives coarse clothing descriptors from real local snapshots, and `care_console.py appearance-profile derive-from-event` has been proven against copied local SQLite data for event `evt_67f81ae3d0df49fd92832766b94be216`. Periodic `--appearance-sampling` can now collect better non-event frames and `summarize-today` reports support ratios. This is dynamic local proof, not a seeded fixture. Human role assignment and production acceptance remain gated.
- Sprint 03 now also has a sourced still-image validation matrix at `apps/caresight-hub/config/appearance-still-image-sources.example.json` and audit receipt `docs/audits/2026-05-23-sprint-03-sourced-still-image-validation.md`. The matrix covers hats/headwear, full outfits, tops, bottoms, sneakers, and boots as source records only; no third-party media is committed, and local operator downloads remain bounded to `appearance-profile describe-image` checks.
- Sprint 04 tracking reliability is implemented for deterministic local checks: floor-stay evidence now records escalation stage, same-track dwell seconds, occlusion grace, dedupe window, policy version, and explicit `not_claimed` boundaries; missing-off-camera evidence uses staged check-in/attention/urgent-handoff wording without identity, danger, medical-emergency, or dispatch claims. Review packets and blackbox receipts display escalation stage when present. Human/live-camera production validation remains operator-owned; see `docs/audits/2026-05-23-sprint-04-tracking-reliability.md`.
- Floor-stay posture evidence now exposes YOLO-box-derived posture labels for live debugging and OBS feed overlays: `standing_likely`, `seated_on_floor_possible`, `low_posture_possible`, and `laying_low_possible`. Seated-on-floor is visible context but does not emit `possible_floor_stay` by itself; the event still requires a laying-low/wide person box in the configured floor zone plus dwell. Missing-off-camera evidence now includes `visibility_state`, `indicator_label`, and a bounded `review_reason`.
- Sprint 05 explicit camera support is implemented for deterministic local checks and owner-authorized live RTSP probing: examples cover webcam, USB, Continuity Camera, and local RTSP; `caresight_camera_probe.py` produces redacted RTSP health receipts from ignored local configs; `MultiCameraFrameManager` provides sequential frame reads with camera/room metadata and health blockers; `care_console.py narrative` renders SQLite-derived camera/track context with `likely_continuity_not_identity` boundaries. Living Room and Kitchen Tapo C210 cameras now probe successfully through ignored local configs with first frames at `1920x1080@15fps`; this is camera-stream proof, not yet full multi-camera event-loop production validation. See `docs/audits/2026-05-23-sprint-05-camera-support.md` and `docs/audits/2026-05-23-tapo-rtsp-validation.md`.

## Production Readiness Correction

The sprint status language must distinguish implementation scaffolding from production-ready operation. Under the current project standard, a sprint is not production-ready until the real runtime path works end to end with configured local dependencies, human validation, and an audit receipt.

Sprint 01 remaining production gates:

1. Translate low-level evidence labels into cleaner human-facing labels.
2. Add a concise Gemma-generated outbound alert once local Gemma serving is available.
3. Capture more seeded-real household normal cases over time for confidence beyond the initial desk/no-event proof.

Sprint 02 remaining production gates:

1. Human-review the generated Gemma Case A wording and approve whether it is caregiver-ready.
2. Configure the live Hermes/BlueBubbles route behind CareSight's redacted contact allowlist, then request explicit human approval for one send only after readiness passes.
3. Configure a real allowlisted caregiver/emergency-contact record in ignored local config, without committing secrets.
4. Prove one dry-run iMessage payload and one human-approved live send path after readiness gates pass.
5. Configure an OBS scene or documented local screen-capture path, then capture a privacy-safe proof.
6. Configure and validate FaceTime handoff as a human-approved action, not an autonomous call, using an approved Apple contact mapping outside Git.
7. Play and human-validate local TTS output from an approved Gemma message draft.
8. Keep SQLite execution-attempt rows for every attempted external action.

## Immediate Next Action

Clear the Sprint 02 runtime blockers before asking for live-action approval:

1. Human-review the generated Gemma Case A wording before live messaging or playback.
2. Configure the live Hermes/BlueBubbles route without committing secrets, then rerun `care_console.py hermes-dry-run <request_id>` before asking for approval.
3. Create the OBS `CareSight Demo` scene or a simpler local screen-capture proof path and confirm it only shows intended content.
4. After Gemma message wording is approved, play the generated local TTS audio and record human audibility/tone approval.
5. For Sprint 03, run the live loop with `--appearance-sampling` to collect capped quality-gated samples, inspect `care_console.py appearance-profile summarize-today`, and have a human assign any resident/caregiver/visitor role before using that role in caregiver-facing copy. For still-image descriptor coverage, use the sourced matrix at `apps/caresight-hub/config/appearance-still-image-sources.example.json`, download selected images only into ignored local storage, then run `care_console.py appearance-profile describe-image LOCAL_IMAGE_PATH --bbox X1,Y1,X2,Y2`.
6. For Sprint 04, run the bounded `--debug-floor-stay --max-seconds 90 --stop-after-event --no-window` operator check when live-camera validation is needed; deterministic tests are implemented but do not by themselves prove production readiness.
7. Before claiming the updated posture/missing indicators as live-validated, run three operator checks: laying-low floor-zone dwell creates `possible_floor_stay`, seated-on-floor shows `seated_on_floor_possible` without creating a floor-stay event, and a known track leaving the camera creates `missing_off_camera_extended` with the off-camera indicator.
8. For Sprint 05, use the ignored Tapo local configs with `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/caresight_camera_probe.py --config <ignored-local-config>` for live RTSP health checks, then run a bounded multi-camera event-loop proof before claiming production operation.

Sprint 05 recovery receipt: `docs/audits/2026-05-23-sprint-05-camera-proof-recovery.md` distinguishes source-backed Tapo/RTSP assumptions, redacted dry-run proof, and the later live local RTSP first-frame proof.

Sprint 02 resolution recovery receipt: `docs/audits/2026-05-23-sprint-02-facetime-obs-tts-resolution-ladder.md` records current FaceTime/OBS/TTS research, no-call checks, OBS feed/websocket blockers, BlackHole/TTS state, and the recommended test ladder before any live handoff approval.

Validation recovery closeout: `docs/audits/2026-05-23-sprint-02-05-validation-recovery-closeout.md` maps the corrected Sprint 02/03/04/05 status to artifacts and remaining gates after the prior overclaim.

Primary sprint entrypoint: [`docs/roadmaps/caresight_sprint_pack/00-master-codex-prompt.md`](caresight_sprint_pack/00-master-codex-prompt.md).

Current production-validation gate: [`docs/roadmaps/caresight_sprint_pack/09-sprint-01-02-production-validation.md`](caresight_sprint_pack/09-sprint-01-02-production-validation.md).

The v0 review and acknowledgement loop is now proven for the confirmed live proof event:

```text
possible_floor_stay event
  -> local event inbox
  -> human-readable summary
  -> human confirm/dismiss
  -> SQLite status update
  -> journal entry
  -> agent-ready handoff record
```

Recommended next command for a clean demo view:

```bash
python3 apps/caresight-hub/scripts/care_console.py dashboard --event-id evt_d9aa38bdc636459c92ea4e25f665cd0d
python3 apps/caresight-hub/scripts/care_console.py review-packet evt_d9aa38bdc636459c92ea4e25f665cd0d --format markdown
python3 apps/caresight-hub/scripts/care_console.py blackbox-receipt evt_d9aa38bdc636459c92ea4e25f665cd0d --format markdown
```

## Recommended Workstreams

- Demo surface steward: execute [`Sprint 01 - Demo Surface Consolidation`](caresight_sprint_pack/01-sprint-demo-surface-consolidation.md) by keeping the focused dashboard, journal preview, alert draft, review packet, and blackbox receipt centered on the selected proof event while preserving the separate awaiting-review backlog.
- Contract steward: keep `possible_floor_stay` aligned with `contracts/schemas/care-event.schema.json`.
- Runtime steward: add the Python v0 loop behind the existing `apps/caresight-hub/` boundary.
- Storage steward: add the minimal SQLite schema and one insert/readback path.
- Review steward: keep `v0_review_events.py` human-readable, reviewer-gated, and documented in `docs/cli/COMMANDS.md`.
- Dashboard steward: expose event timeline, model/FPS panel, and journal without becoming canonical truth.
- Audit steward: keep `DECISIONS.md`, `CHANGELOG.md`, roadmap docs, and quality-gate evidence synchronized.

## v0 Resolution Order

1. Run `python apps/caresight-hub/scripts/v0_floor_stay_live.py`.
2. Tune `apps/caresight-hub/config/v0.local.json` if the floor zone is too large or too small.
3. Confirm `event_persisted` prints once per continuous same-track floor-zone dwell.
4. Inspect `apps/caresight-hub/data/caresight-v0.sqlite3`.
5. Run `python apps/caresight-hub/scripts/v0_review_events.py list`.
6. Run `python apps/caresight-hub/scripts/v0_review_events.py show <event_id>`.
7. Confirm or dismiss with an authorized reviewer.
8. Run `python apps/caresight-hub/scripts/v0_review_events.py audit <event_id>`.
9. Verify `event_observations.track_id`, `event_reviews`, `journal_entries`, and `agent_handoffs` rows exist with reviewer, timestamps, status, and report-only handoff state.
10. Promote the verified command and observed output into a follow-up audit receipt.

Status: completed for the current tranche. See `docs/audits/2026-05-20-t041-final-live-proof.md`.

## Next Sprint Candidates

Sprint pack index:

- [`README.md`](caresight_sprint_pack/README.md) - pack overview and global rule.
- [`00-master-codex-prompt.md`](caresight_sprint_pack/00-master-codex-prompt.md) - full sprint prompt, boundaries, implementation order, and validation expectations.
- [`01-sprint-demo-surface-consolidation.md`](caresight_sprint_pack/01-sprint-demo-surface-consolidation.md) - focused dashboard, review packet, blackbox receipt, and stale-backlog handling.
- [`02-sprint-agent-llm-drafting-layer.md`](caresight_sprint_pack/02-sprint-agent-llm-drafting-layer.md) - local fake/Gemma drafting, action requests, TTS staging, and forbidden-action tests.
- [`03-sprint-daily-appearance-profiles.md`](caresight_sprint_pack/03-sprint-daily-appearance-profiles.md) - non-biometric same-day appearance continuity.
- [`04-sprint-tracking-reliability-upgrade.md`](caresight_sprint_pack/04-sprint-tracking-reliability-upgrade.md) - same-track dwell, occlusion grace, dedupe, missing-off-camera, and escalation-stage evidence.
- [`05-sprint-multi-camera-narrative-proof.md`](caresight_sprint_pack/05-sprint-multi-camera-narrative-proof.md) - explicit local multi-camera narrative proof without cloud providers or discovery.
- [`06-sprint-routine-event-demo.md`](caresight_sprint_pack/06-sprint-routine-event-demo.md) - medication and hydration likely-observed routine demo.
- [`07-contract-json-pack.md`](caresight_sprint_pack/07-contract-json-pack.md) - contract continuity audit source pack for checking the schemas absorbed into earlier implementation sprints.
- [`08-readme-product-shape.md`](caresight_sprint_pack/08-readme-product-shape.md) - product story, README copy, value-adds, and demo narrative.
- [`09-sprint-01-02-production-validation.md`](caresight_sprint_pack/09-sprint-01-02-production-validation.md) - production-readiness checklist for Sprint 01 and Sprint 02 seeded-real A/B validation.

Sprint pack review:

- The pack is aligned with the current CareSight ethos: contracts and SQLite remain canonical, YOLO26 MLX remains the vision lane, agents remain draft/report-only, and external adapters are downstream of policy.
- Treat [`00-master-codex-prompt.md`](caresight_sprint_pack/00-master-codex-prompt.md) as a boundary document, not a mandate to implement all six workstreams in one change. Execute one sprint at a time, starting with Sprint 01.
- Treat [`07-contract-json-pack.md`](caresight_sprint_pack/07-contract-json-pack.md) as a contract audit/checkpoint, not a standalone build sprint. Each implementation sprint absorbs the contract pieces it needs before runtime work; Sprint 07 later validates continuity across the absorbed schemas, examples, validators, runtime outputs, and docs.
- Treat [`09-sprint-01-02-production-validation.md`](caresight_sprint_pack/09-sprint-01-02-production-validation.md) as the current production-readiness gate before claiming Sprint 01 or Sprint 02 complete under the production standard.
- Hardware, model, pricing, and external-tool claims in the sprint pack are roadmap guidance only. Re-check live sources before using them in purchase recommendations, marketing copy, or proof claims.

Recommended execution order:

```text
01 demo surface consolidation
  -> 02 agent/LLM drafting layer
  -> 03 daily appearance profiles
  -> 04 tracking reliability upgrade
  -> 05 multi-camera narrative proof
  -> 06 routine event demo
  -> 07 contract continuity audit
  -> 08 README/product-shape refresh
```

### 1. [Demo Surface Consolidation](caresight_sprint_pack/01-sprint-demo-surface-consolidation.md)

Goal: make the proof story clean and repeatable for judges and future agents.

Scope:

- Keep `dashboard --event-id <event_id>` as the primary demo path.
- Add a human-review packet command for compact approval decisions.
- Separate stale awaiting-review demo rows from the focused proof event.
- Export one markdown or JSON blackbox receipt from SQLite for a chosen event.

Recommended answer to ambiguity: stale events should remain visible as an audit backlog, but not drive the focused demo view.

### 2. [Agent/LLM Drafting Layer](caresight_sprint_pack/02-sprint-agent-llm-drafting-layer.md)

Goal: add a local, constrained language layer that turns SQLite-backed event records into caregiver-friendly drafts without gaining authority over review decisions or raw video.

Architecture:

```text
SQLite blackbox
  -> structured event JSON / audit chain
  -> local Gemma MLX summarizer
  -> OpenClaw/Hermes agent wrapper
  -> draft-only outputs
  -> human review / Apple Notes / alert text
```

Scope:

- Serve a local MLX Gemma model for summary generation.
- Send only structured event JSON, audit chains, journal rows, review state, handoff payloads, and bounded appearance summaries to the model.
- Produce constrained JSON outputs for caregiver summaries, Apple Notes entries, alert drafts, handoff packets, and audit summaries.
- Add forbidden-action tests proving agents cannot confirm, dismiss, delete, dispatch, diagnose, inspect raw video, or claim medication was taken.
- Preserve provenance and purpose on every generated draft.

Example input:

```json
{
  "event_id": "evt_d9aa38bdc636459c92ea4e25f665cd0d",
  "event_type": "possible_floor_stay",
  "status": "human_confirmed",
  "room": "Living Room",
  "reviewer": "Steven",
  "journal_entries": 1,
  "agent_handoffs": 1,
  "blocked_actions": ["autonomous_emergency_dispatch", "medical_diagnosis"]
}
```

Example output:

```json
{
  "caregiver_summary": "A possible floor-stay event was confirmed in the Living Room. The local record includes a snapshot, human review, journal entry, and report-only handoff.",
  "apple_notes_entry": "CareSight confirmed a possible floor-stay event in the Living Room. Reviewed by Steven. No autonomous emergency dispatch or medical diagnosis was performed.",
  "alert_draft": "CareSight confirmed a possible floor-stay event in the Living Room. Please review the local record and follow your care plan.",
  "safety_boundaries": ["draft_only", "human_review_required"]
}
```

Recommended answer to ambiguity: the agent may propose wording and packets, but only SQLite records and authorized human review state are canonical.

### 3. [Daily Appearance Profiles](caresight_sprint_pack/03-sprint-daily-appearance-profiles.md)

Goal: add non-biometric, local-only person continuity for caregiving context.

Current branch status: started and implementation-ready in `codex/sprint-03-appearance`. The dynamic path reads existing SQLite events, observation bounding boxes, local `snapshot_path` images, and capped periodic appearance samples; it does not depend on seeded appearance fixtures. Remaining production gates are human role assignment, longer live/demo operator validation, and acceptance of the dashboard wording.

Value:

- Helps caregivers answer “who was last seen where, wearing what?”
- Supports missing-off-camera and wandering narratives.
- Gives useful descriptions during stressful moments without claiming biometric identity.

Scope:

- Store daily, expiring appearance profiles in SQLite.
- Derive temporary descriptors from person observations, such as upper/lower clothing color, visible accessories, carried objects, last seen room, last seen time, and last seen event.
- Link tracks with conservative “likely same tracked person” confidence, not definitive identity.
- Allow human role assignment for the day, such as `resident_primary`, `caregiver_known`, `visitor_unknown`, or `unknown_person`.
- Refresh profiles each day and expire active matching after a configurable window.

Example profile:

```json
{
  "appearance_profile_id": "appearance_2026_05_20_001",
  "role_assignment": "resident_primary",
  "assignment_source": "human_confirmed",
  "active_date": "2026-05-20",
  "expires_at": "2026-05-21T04:00:00Z",
  "attributes": {
    "upper_body_color": { "value": "dark gray", "confidence": 0.78 },
    "lower_body_color": { "value": "gray", "confidence": 0.70 },
    "eyewear": { "value": "glasses", "confidence": 0.64 },
    "headwear": { "value": "none", "confidence": 0.58 }
  },
  "last_seen": {
    "camera_id": "living_room",
    "room": "Living Room",
    "timestamp": "2026-05-20T02:36:31Z",
    "event_id": "evt_d9aa38bdc636459c92ea4e25f665cd0d"
  }
}
```

Recommended answer to ambiguity: clothing and accessories are daily appearance memory, not durable identity. CareSight may say “likely same tracked person” or “resident-assigned profile for today,” but not “this is Steven” unless a later explicit local enrollment feature is added.

### 4. [Tracking Reliability Upgrade](caresight_sprint_pack/04-sprint-tracking-reliability-upgrade.md)

Goal: make floor-stay and missing-off-camera behavior more resilient in multi-person scenes.

Scope:

- Trigger floor-stay from the same `track_id` staying low for configured durations.
- Add severity scaling, such as early concern, prolonged concern, and critical attention.
- Add occlusion grace and dedupe tests for get-up/fall-again behavior.
- Feed daily appearance profiles with track continuity but keep identity claims bounded.

Recommended answer to ambiguity: default to conservative, configurable thresholds and no autonomous emergency dispatch.

### 5. [Multi-Camera Narrative Proof](caresight_sprint_pack/05-sprint-multi-camera-narrative-proof.md)

Goal: support the stronger story that a person moved from one room to another, then an event occurred.

Scope:

- Configure two local cameras or one webcam plus one RTSP source.
- Keep local-only camera rules; no Ring/Nest/cloud provider path.
- Group dashboard timeline by room and camera.
- Use track continuity and daily appearance profiles only as likely continuity signals.

Recommended answer to ambiguity: two configured local sources are enough for v1/v2; defer ONVIF discovery and LAN scanning.

### 6. [Routine Event Demo](caresight_sprint_pack/06-sprint-routine-event-demo.md)

Goal: demonstrate medication and hydration routine events without overclaiming.

Scope:

- Use person + object label + routine zone + routine window.
- Keep event names `medication_routine_likely_observed` and `hydration_routine_likely_observed`.
- Require human confirmation.
- Add review packet examples and journal language.

Recommended answer to ambiguity: never say “medication taken” or “hydration completed”; say the routine was likely observed.

## Open Questions

Question: Should the dashboard default to the latest confirmed proof event or the oldest awaiting-review concern?
Suggested Answer: Default to latest confirmed proof event for demo mode, while keeping awaiting-review concerns in a separate backlog lane.
Rationale: The demo narrative should be clean and auditable, but unresolved events should remain visible rather than hidden.

Question: Should agents be allowed to recommend confirm or dismiss decisions?
Suggested Answer: Agents may recommend and draft a human review packet, but may not execute confirm or dismiss or become reviewer of record.
Rationale: Recommendations reduce operator burden while preserving the project’s human-authority boundary.

Question: Should the local Gemma/OpenClaw/Hermes layer inspect raw video or snapshots?
Suggested Answer: No for v1/v2. It should consume structured JSON, audit chains, journal rows, and bounded descriptors only.
Rationale: YOLO26 MLX is the vision lane; the LLM layer is a drafting and audit-assistance lane.

Question: Should Apple Notes writes be automatic?
Suggested Answer: Stage Apple Notes text as a draft first, then optionally allow a human-approved local automation to append it.
Rationale: Draft-first behavior keeps provenance clear and avoids silent changes to external user-visible records.

Question: Should Daily Appearance Profiles identify named people?
Suggested Answer: No. Use daily, human-assigned roles such as `resident_primary`, `caregiver_known`, `visitor_unknown`, and `unknown_person`.
Rationale: Clothing/accessory descriptors are useful caregiver context but are not durable biometric identity.

Question: How long should daily appearance profiles remain active?
Suggested Answer: Default to same-day expiration with a configurable 12-18 hour active window.
Rationale: Clothing changes frequently; stale descriptors can mislead caregivers during a high-stress event.

Question: How long should someone be absent from all configured feeds before CareSight escalates?
Suggested Answer: Start with configurable stages: observe-only under 2 minutes, check-in suggested at 2-5 minutes, attention at 5-10 minutes when recent context is concerning, and urgent handoff at 10-15 minutes only after a high-concern or repeated unresolved event. All stages remain caregiver-review prompts, not emergency dispatch.
Rationale: Absence can mean normal movement, privacy, occlusion, or camera coverage gaps. Sprint 04 should combine last-seen track context, same-day appearance sample confidence, room type, time of day, and prior event state before escalating.

Question: Should multi-camera support include LAN discovery or ONVIF now?
Suggested Answer: No. Use two explicitly configured local sources first, then evaluate ONVIF discovery later.
Rationale: Discovery adds credential, privacy, and network-scanning complexity before the two-room demo story needs it.

Question: Should the system claim medication or hydration completion?
Suggested Answer: No. Keep event names and copy at `medication_routine_likely_observed` and `hydration_routine_likely_observed`.
Rationale: Vision can observe routine context, but cannot safely confirm ingestion or health state.

Question: Should older stale awaiting-review demo events be dismissed, archived, or left untouched?
Suggested Answer: Add an archive/backlog state or demo filter rather than deleting records; dismiss only with explicit human review.
Rationale: SQLite is the blackbox source of truth, so old records should remain auditable while the demo avoids confusing them with proof events.

Question: Should severity escalation ever trigger emergency dispatch?
Suggested Answer: No for hackathon core. Escalation can draft text and suggest FaceTime/text handoff, but cannot dispatch.
Rationale: The project is a caregiver-awareness prototype, not a medical device or emergency response system.

## Recommended Next Work

1. Start [`Sprint 02 - Agent/LLM Drafting Layer`](caresight_sprint_pack/02-sprint-agent-llm-drafting-layer.md).
2. Absorb the Sprint 07 contract pieces Sprint 02 actually consumes: `agent-draft`, `agent-action-request`, `tts-utterance`, and forbidden claim/action vocabulary.
3. Add valid and invalid examples before provider/runtime behavior.
4. Implement the fake provider first, then optional Gemma MLX support only after deterministic tests pass.
5. Keep OpenClaw/Hermes, Apple Notes, iMessage, OBS, FaceTime, and TTS behind CareSight action-request policy; no silent external action execution.
6. Preserve Sprint 03 ownership of `appearance-profile` contracts and non-biometric descriptor behavior.
7. Keep [`07-contract-json-pack.md`](caresight_sprint_pack/07-contract-json-pack.md) as the later continuity audit that checks whether contracts absorbed into Sprints 01, 02, and 03 remain consistent across schemas, examples, validators, runtime output, CLI docs, and audit receipts.

Do not start Gemma/OpenClaw/Hermes behavior until the Sprint 02 contract slice is validated. That keeps the agent/action gateway downstream of a concise, inspectable schema surface.

## Validation Before Advancing

```bash
npm run validate:scaffold
npm run validate:contracts
npm run test:focused
npm test
npm run typecheck
npm run py:check
npm run check
```

## Do Not Start Yet

- Ring/Nest adapters.
- HIPAA claims.
- autonomous emergency dispatch.
- cloud raw-video upload defaults.
- biometric identity recognition or face recognition without an explicit future local-enrollment decision.
