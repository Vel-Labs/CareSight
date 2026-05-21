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
- Sprint 01 contract-backed demo surfaces are complete: `human-review-packet` and `blackbox-receipt` contracts exist, read-only demo-surface builders derive from SQLite audit chains, and `care_console.py` exposes `review-packet` and `blackbox-receipt` as agent-safe read commands.
- Sprint 01 demo surface audit receipt: `docs/audits/2026-05-20-sprint-01-demo-surface.md`.
- Sprint 02 agent-assist contracts are complete for this tranche: `agent-draft`, `agent-action-request`, `tts-utterance`, and `forbidden-claim-vocabulary` schemas/examples validate through the contract corpus.
- The Sprint 02 fake provider is complete for this tranche: validated and blocked agent drafts are stored in SQLite through `agent_drafts`, with forbidden-claim reasons and safe rewrites for blocked drafts.
- Sprint 02 action-request staging is complete for this tranche: `care_console.py agent-draft`, `stage-action-request`, and `list-action-requests` write and inspect local SQLite rows only. Staged requests remain `not_executed` and require human approval.
- Local model candidates have been downloaded under ignored purpose lanes for follow-up provider benchmarking: `models/vision/yolo26-mlx/`, `models/reasoning/gemma/`, and `models/tts/holler/`.
- Hermes is vendored as a pinned workspace submodule at `apps/caresight-hub/vendor/hermes-agent`; OpenClaw remains uninstalled and available as the policy-heavy gateway fallback.
- Hermes is now the preferred first harness trial for staged iMessage/Notes/FaceTime-style actions. `care_console.py agent-harness-plan` renders non-executing routing plans only.
- `apps/caresight-hub/config/hermes/` contains safe repo-local Hermes templates for a local OpenAI-compatible Gemma MLX endpoint; OpenRouter is not required by default and remains an explicit cloud fallback only.
- Staged Hermes handoff payloads now support `routine`, `attention`, and `urgent_handoff` levels, allowlisted emergency-contact routing, and bounded response options for journal text updates, local screen capture by request, or FaceTime handoff by request.

## Immediate Next Action

Consolidate the validated demo surface and prepare the next sprint lane from the CareSight sprint pack.

Primary sprint entrypoint: [`docs/roadmaps/caresight_sprint_pack/00-master-codex-prompt.md`](caresight_sprint_pack/00-master-codex-prompt.md).

Recommended first implementation lane: [`docs/roadmaps/caresight_sprint_pack/01-sprint-demo-surface-consolidation.md`](caresight_sprint_pack/01-sprint-demo-surface-consolidation.md).

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

Sprint pack review:

- The pack is aligned with the current CareSight ethos: contracts and SQLite remain canonical, YOLO26 MLX remains the vision lane, agents remain draft/report-only, and external adapters are downstream of policy.
- Treat [`00-master-codex-prompt.md`](caresight_sprint_pack/00-master-codex-prompt.md) as a boundary document, not a mandate to implement all six workstreams in one change. Execute one sprint at a time, starting with Sprint 01.
- Treat [`07-contract-json-pack.md`](caresight_sprint_pack/07-contract-json-pack.md) as a contract audit/checkpoint, not a standalone build sprint. Each implementation sprint absorbs the contract pieces it needs before runtime work; Sprint 07 later validates continuity across the absorbed schemas, examples, validators, runtime outputs, and docs.
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
