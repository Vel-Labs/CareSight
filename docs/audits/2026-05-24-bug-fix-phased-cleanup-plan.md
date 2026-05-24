# CareSight Bug Fix Phased Cleanup Plan

Date: 2026-05-24

Source report: `docs/audits/2026-05-24-project-bug-risk-audit.md`

Purpose: convert the 20 bug/risk findings into a long-horizon Codex cleanup plan with phases, impacted files, strict implementation steps, intended resolution, required tests, and blank resolution notes for each finding.

Instruction boundary: this document is a planning/control artifact. It does not mark any bug fixed.

## Top-Level Awareness Statement

Current status: 5 of 20 findings resolved in this plan.

Current validation status:

- Latest known full gate: `npm run check` passed on 2026-05-24 after Phase 1 resolution notes and documentation updates.
- Deterministic coverage currently includes scaffold validation, contract validation, TypeScript tests/typecheck, and Python unit tests.
- Runtime integration gates still need more work: camera probes, OBS websocket/feed checks, Gemma endpoint, Hermes no-send, iMessage dry run, human-approved live send, FaceTime setup, TTS generation/playback, and periodic heartbeat checks are not all covered by the unit gate.

More work remains: yes. This plan is ready for Codex execution in phases, but the findings below are still open until an implementation agent updates each `Resolution notes` section with exact code changes, commands run, receipts produced, and remaining risks.

## Phase Status Board

| Phase | Findings | Theme | Status |
| --- | --- | --- | --- |
| Phase 1 | F001, F002, F003, F008, F010 | Live handoff authority, receipts, and media policy | Resolved |
| Phase 2 | F004, F005, F006, F007, F016, F017 | Repo readability, storage/runtime boundaries, lifecycle correctness | Open |
| Phase 3 | F011, F014, F015, F019 | Runtime validation, heartbeat checks, feed exposure, model governance, contracts | Open |
| Phase 4 | F009, F012, F013, F018 | Care intelligence quality: replies, posture/depth/segmentation, missing context, privacy redaction | Open |
| Phase 5 | F020 | Documentation visibility and operator usability | Open |

## Required New or Expanded Schemas

These schemas should be added or expanded before or alongside the relevant fixes. All schema work must include valid and invalid examples, contract corpus updates, docs, changelog entries, and tests.

### `media-sharing-policy`

Purpose: define when event-scoped images, screenshots, clips, or text excerpts may leave the local device.

Owned by:

- `contracts/schemas/media-sharing-policy.schema.json`
- `contracts/examples/valid/media-sharing-policy.event-scoped-snapshot.json`
- `contracts/examples/invalid/media-sharing-policy-raw-video-default.json`
- `tests/contracts/contract-corpus.test.ts`
- `packages/core/src/validate-contracts.ts` if schema mapping is manual.

Required fields:

- `policy_id`
- `media_type`
- `scope`
- `approval_state`
- `approved_by`
- `approved_at`
- `redaction_required`
- `redaction_status`
- `retention_class`
- `blocked_media_types`
- `provenance`

### `reply-gated-handoff`

Purpose: define when a text reply may trigger a follow-up action such as FaceTime or TTS.

Owned by:

- `contracts/schemas/reply-gated-handoff.schema.json`
- `contracts/examples/valid/reply-gated-handoff.facetime.json`
- `contracts/examples/invalid/reply-gated-handoff-ambiguous-reply.json`

Required fields:

- `handoff_id`
- `source_request_id`
- `allowed_followup_actions`
- `reply_classification`
- `required_phrase`
- `live_approval_state`
- `contact_id`
- `target_verification`
- `execution_receipt_required`

### `runtime-validation-receipt`

Purpose: provide machine-readable proof for camera/OBS/model/handoff runtime gates and heartbeat checks.

Owned by:

- `contracts/schemas/runtime-validation-receipt.schema.json`
- `contracts/examples/valid/runtime-validation-receipt.camera-probe.json`
- `contracts/examples/valid/runtime-validation-receipt.heartbeat.json`
- `contracts/examples/invalid/runtime-validation-receipt-missing-boundary.json`

Required fields:

- `receipt_id`
- `check_type`
- `started_at`
- `completed_at`
- `status`
- `target`
- `command`
- `result`
- `safety_boundaries`
- `blockers`
- `next_check_after`

### `model-manifest`

Purpose: record local model source, license, checksum, intended use, and validation status.

Owned by:

- `contracts/schemas/model-manifest.schema.json`
- `contracts/examples/valid/model-manifest.yolo26n.json`
- `contracts/examples/valid/model-manifest.privacy-filter.json`
- `contracts/examples/invalid/model-manifest-missing-license.json`

Required fields:

- `model_id`
- `purpose_lane`
- `source_url`
- `license`
- `local_path`
- `sha256`
- `expected_size_bytes`
- `runtime`
- `allowed_uses`
- `blocked_uses`
- `validation_command`
- `last_validated_at`

### `local-feed-exposure`

Purpose: define when local MJPEG/browser feeds may bind beyond loopback and what auth/token controls are required.

Owned by:

- `contracts/schemas/local-feed-exposure.schema.json`
- `contracts/examples/valid/local-feed-exposure.loopback.json`
- `contracts/examples/invalid/local-feed-exposure-lan-no-token.json`

Required fields:

- `feed_id`
- `bind_host`
- `bind_scope`
- `auth_required`
- `token_required`
- `operator_approved`
- `expires_at`
- `privacy_warning_acknowledged`

### `retention-policy`

Purpose: define retention for SQLite events, snapshots, clips, journal entries, model outputs, and execution attempts.

Owned by:

- `contracts/schemas/retention-policy.schema.json`
- `contracts/examples/valid/retention-policy.local-snapshots.json`
- `contracts/examples/invalid/retention-policy-unbounded-raw-media.json`

Required fields:

- `policy_id`
- `record_type`
- `retention_days`
- `deletion_mode`
- `export_allowed`
- `share_allowed`
- `audit_log_required`

### `privacy-redaction-receipt`

Purpose: record text redaction attempts, including optional local OpenAI Privacy Filter use.

Owned by:

- `contracts/schemas/privacy-redaction-receipt.schema.json`
- `contracts/examples/valid/privacy-redaction-receipt.privacy-filter.json`
- `contracts/examples/invalid/privacy-redaction-receipt-compliance-claim.json`

Required fields:

- `receipt_id`
- `input_type`
- `redaction_engine`
- `model_manifest_id`
- `labels_detected`
- `redaction_status`
- `human_review_required`
- `not_claimed`

Important boundary: OpenAI Privacy Filter is a PII detection/masking aid, not an anonymization, HIPAA compliance, or safety guarantee. Its model card explicitly cautions against over-reliance and recommends in-domain evaluation and human review for high-sensitivity workflows.

Source: https://huggingface.co/openai/privacy-filter

## Phase 1 - Live Handoff Authority, Receipts, and Media Policy

### F001 - Explicit live target bypasses the allowlist target mapping

Status: Resolved

Phase: 1

Priority: High

User note: Easy fix; keep strict recipient boundary.

Impacted files:

- `apps/caresight-hub/caresight/runtime/agent_assist/live_handoff.py`
- `apps/caresight-hub/caresight/runtime/agent_assist/contacts.py`
- `apps/caresight-hub/scripts/caresight_live_handoff.py`
- `apps/caresight-hub/scripts/v0_floor_stay_live.py`
- `apps/caresight-hub/tests/test_agent_assist.py`
- `docs/cli/COMMANDS.md`
- `CHANGELOG.md`

Strict actionable steps:

1. Add a contact-target verification helper that compares explicit targets against the private allowlist channel references or approved target hashes.
2. Change `resolve_contact_target()` so `explicit_target` is not accepted before allowlist validation.
3. Add a separate manual-test override flag only if needed, with `target_override_used=true` in receipts.
4. Update CLI help to state that contact ID and target must match.
5. Update execution attempt payloads with `target_verification`.

Intended resolution:

Live iMessage and FaceTime paths can only target a private channel that is tied to the allowlisted contact ID, unless a clearly marked manual-test override is used and audited.

Tests required:

- Unit test: explicit target does not match allowlist, send is blocked.
- Unit test: explicit target matches allowlist, send dry-run is allowed.
- Unit test: env target is validated against allowlist.
- CLI test: help text documents the target matching rule.

Resolution notes:

Resolved 2026-05-24 in Phase 1. `contacts.py` now verifies explicit CLI and environment targets against the allowlisted contact channel reference or approved target hash before returning a live iMessage/FaceTime target. `live_handoff.py` calls this verification for explicit, environment, and allowlist-derived targets and writes redacted `target_verification` into live attempt payloads. Tests added in `test_agent_assist.py` cover matching explicit targets, blocked mismatches, and blocked mismatching environment targets. Commands run: `npm run validate:contracts`; `PYTHONPATH=apps/caresight-hub python3 -m unittest apps/caresight-hub/tests/test_agent_assist.py apps/caresight-hub/tests/test_sqlite_store.py`; `npm run check`. Remaining risk: local private allowlist files must include either real channel references or approved hashes; redacted example placeholders still intentionally block live targeting.

### F002 - Live action attempts are logged after execution instead of before execution

Status: Resolved

Phase: 1

Priority: High

User note: Easy fix; audit first.

Impacted files:

- `apps/caresight-hub/caresight/runtime/agent_assist/live_handoff.py`
- `apps/caresight-hub/caresight/storage/sqlite_store.py`
- `apps/caresight-hub/tests/test_agent_assist.py`
- `contracts/schemas/agent-action-request.schema.json`
- `contracts/schemas/runtime-validation-receipt.schema.json`
- `contracts/examples/valid/runtime-validation-receipt.*.json`
- `docs/cli/COMMANDS.md`
- `DECISIONS.md`
- `CHANGELOG.md`

Strict actionable steps:

1. Add a pre-execution attempt insert path with `execution_state=pending_execution`.
2. Refactor iMessage, FaceTime, and TTS calls to insert the pending attempt before the external action.
3. Add an update method that marks the same attempt `executed`, `failed`, or `blocked`.
4. Fail closed if the pending attempt cannot be inserted.
5. Update decision docs to reflect the exact pre-execution receipt semantics.

Intended resolution:

No live text, FaceTime open, or TTS playback can occur unless a durable pending execution attempt already exists in SQLite.

Tests required:

- Unit test: preflight insert failure prevents send.
- Unit test: successful send updates pending attempt to executed.
- Unit test: failed send updates pending attempt to failed.
- Unit test: TTS playback follows the same pending-to-final lifecycle.

Resolution notes:

Resolved 2026-05-24 in Phase 1. `live_handoff.py` inserts a durable `pending_execution` row before iMessage and FaceTime calls, then updates the same row to `dry_run`, `executed`, or `failed`. `sqlite_store.py` now supports `pending_execution`, updates existing attempt rows, and migrates older local tables to the expanded state check. The live detector's post-FaceTime TTS path now records a pending TTS attempt before playback and updates it after playback. Tests cover pending-to-final iMessage behavior through the live dry-run path; full Python verification covered the storage migration/readback path. Commands run: `npm run validate:contracts`; `PYTHONPATH=apps/caresight-hub python3 -m unittest apps/caresight-hub/tests/test_agent_assist.py apps/caresight-hub/tests/test_sqlite_store.py`; `npm run check`. Remaining risk: interrupted processes can leave `pending_execution` rows, which is intentional audit evidence and should be surfaced operationally rather than hidden.

### F003 - Event snapshots can leave the local boundary without an explicit media-sharing contract

Status: Resolved

Phase: 1

Priority: High

User note: Easy fix; make media sharing explicit.

Impacted files:

- `contracts/schemas/media-sharing-policy.schema.json`
- `contracts/examples/valid/media-sharing-policy.event-scoped-snapshot.json`
- `contracts/examples/invalid/media-sharing-policy-raw-video-default.json`
- `packages/core/src/validate-contracts.ts`
- `apps/caresight-hub/caresight/runtime/agent_assist/live_handoff.py`
- `apps/caresight-hub/scripts/v0_floor_stay_live.py`
- `apps/caresight-hub/tests/test_agent_assist.py`
- `docs/cli/COMMANDS.md`
- `docs/roadmaps/CURRENT_STATE_AND_NEXT.md`
- `CHANGELOG.md`

Strict actionable steps:

1. Add the `media-sharing-policy` schema and corpus examples.
2. Add media policy fields to no-response escalation payloads.
3. Require explicit media attachment approval separate from text-send approval.
4. Record attachment source, redaction status, attachment hash, and approval state.
5. Block raw video attachment by default.

Intended resolution:

CareSight can only attach event-scoped snapshots after explicit media policy approval, and every attachment has a durable policy receipt.

Tests required:

- Contract test: valid event-scoped snapshot policy passes.
- Contract test: raw video default policy fails.
- Unit test: no-response escalation without media approval sends text only or blocks attachment.
- Unit test: approved media policy attaches only event-scoped snapshot metadata.

Resolution notes:

Resolved 2026-05-24 in Phase 1. Added `contracts/schemas/media-sharing-policy.schema.json` plus valid/invalid corpus examples. `execute_live_imessage()` now rejects any attachment without an explicit approved event-scoped snapshot media policy, blocks raw-video policy shapes by default, records redaction/approval state and attachment hash metadata, and redacts local paths. The no-response escalation path in `v0_floor_stay_live.py` builds an event-scoped media policy before attaching a snapshot. Tests cover attachment rejection without policy and approved event-scoped snapshot metadata. Commands run: `npm run validate:contracts`; `PYTHONPATH=apps/caresight-hub python3 -m unittest apps/caresight-hub/tests/test_agent_assist.py apps/caresight-hub/tests/test_sqlite_store.py`; `npm run check`. Remaining risk: this enforces the live handoff attachment path; broader future clip/feed sharing still needs the later runtime-validation and retention-policy phases.

### F008 - FaceTime path lacks explicit contract-oriented receipt permission

Status: Resolved

Phase: 1

Priority: Medium

User note: Receipt should be extremely helpful and contract oriented.

Impacted files:

- `contracts/schemas/reply-gated-handoff.schema.json`
- `contracts/examples/valid/reply-gated-handoff.facetime.json`
- `contracts/examples/invalid/reply-gated-handoff-ambiguous-reply.json`
- `apps/caresight-hub/caresight/runtime/agent_assist/live_handoff.py`
- `apps/caresight-hub/caresight/runtime/agent_assist/harness.py`
- `apps/caresight-hub/tests/test_agent_assist.py`
- `docs/cli/COMMANDS.md`
- `CHANGELOG.md`

Strict actionable steps:

1. Add `reply-gated-handoff` schema and examples.
2. Require staged action requests to declare allowed follow-up actions.
3. Require FaceTime continuation to include `request_facetime_handoff` or equivalent.
4. Add a FaceTime handoff receipt shape with reply classification, contact verification, and execution attempt IDs.
5. Update CLI readback to show the handoff receipt.

Intended resolution:

FaceTime is not merely an implicit follow-up to an iMessage request. It is a contract-backed, reply-gated handoff with its own receipt.

Tests required:

- Contract test: valid FaceTime reply-gated handoff passes.
- Contract test: ambiguous reply handoff fails.
- Unit test: staged iMessage request without FaceTime follow-up option cannot open FaceTime.
- Unit test: staged request with FaceTime option plus explicit yes phrase may proceed.

Resolution notes:

Resolved 2026-05-24 in Phase 1. Added `contracts/schemas/reply-gated-handoff.schema.json` plus valid/invalid examples. `execute_facetime_if_yes()` now requires the source staged request to offer `request_facetime_handoff`, verifies the FaceTime target against the allowlisted contact, inserts a pending execution receipt before opening FaceTime, and stores a `reply_gated_handoff` receipt with reply classification, source request ID, contact ID, target verification, and execution-receipt requirement. Tests cover yes/no interpretation, blocked requests without the FaceTime follow-up option, and receipt fields. Commands run: `npm run validate:contracts`; `PYTHONPATH=apps/caresight-hub python3 -m unittest apps/caresight-hub/tests/test_agent_assist.py apps/caresight-hub/tests/test_sqlite_store.py`; `npm run check`. Remaining risk: live FaceTime OS/UI behavior still depends on operator-approved local macOS setup; this fix covers authority and receipts, not live call quality.

### F010 - Source action requests remain `not_executed` after live attempts

Status: Resolved

Phase: 1

Priority: Medium

User note: In line with F008; needs resolution.

Impacted files:

- `apps/caresight-hub/caresight/storage/sqlite_store.py`
- `apps/caresight-hub/caresight/runtime/agent_assist/harness.py`
- `apps/caresight-hub/caresight/runtime/agent_assist/live_handoff.py`
- `apps/caresight-hub/scripts/care_console.py`
- `apps/caresight-hub/tests/test_agent_assist.py`
- `docs/cli/COMMANDS.md`
- `CHANGELOG.md`

Strict actionable steps:

1. Preserve immutable staged request rows.
2. Add a derived request status read model that summarizes latest execution attempts.
3. Update list/show commands to display `latest_attempt_state`.
4. Ensure dashboard/read models do not show a request as simply pending if an executed attempt exists.
5. Link reply-gated handoff receipts to the source request.

Intended resolution:

The original action request remains an immutable staged proposal, while operator surfaces clearly show whether live execution attempts occurred and what their result was.

Tests required:

- Unit test: request with no attempts shows pending/staged.
- Unit test: request with executed attempt shows latest attempt executed.
- Unit test: request with failed attempt shows latest attempt failed and error summary.
- CLI test: list action requests includes derived status.

Resolution notes:

Resolved 2026-05-24 in Phase 1. `agent_action_requests` remain immutable staged rows with `execution_state: not_executed`, and `SQLiteStore.list_agent_action_requests()` / `get_agent_action_request()` now append a derived `latest_attempt_state` read model from `agent_execution_attempts`. `docs/cli/COMMANDS.md` documents this derived status. Tests verify a live dry-run updates the same attempt row and that stored action requests remain staged while exposing attempt state. Commands run: `npm run validate:contracts`; `PYTHONPATH=apps/caresight-hub python3 -m unittest apps/caresight-hub/tests/test_agent_assist.py apps/caresight-hub/tests/test_sqlite_store.py`; `npm run check`. Remaining risk: presentation surfaces must choose to display `latest_attempt_state`; this phase added the store read model and CLI documentation but did not refactor every dashboard view.

## Phase 2 - Repo Readability, Storage Boundaries, and Lifecycle Correctness

### F004 - `v0_floor_stay_live.py` should become an explicit event/escalation pipeline

Status: Open

Phase: 2

Priority: High

User note: Obvious no brainer. Internal structure should be an escalation orchestrator with event modules such as floor stay and missing, escalation methods like FaceTime/text, separate handoff modules, and a human-readable repo.

Impacted files:

- `apps/caresight-hub/scripts/v0_floor_stay_live.py`
- `apps/caresight-hub/caresight/runtime/live_loop.py`
- `apps/caresight-hub/caresight/runtime/escalation/orchestrator.py`
- `apps/caresight-hub/caresight/runtime/escalation/events.py`
- `apps/caresight-hub/caresight/runtime/escalation/methods.py`
- `apps/caresight-hub/caresight/runtime/handoffs/`
- `apps/caresight-hub/caresight/runtime/preview/mjpeg.py`
- `apps/caresight-hub/caresight/runtime/post_event_pipeline.py`
- `apps/caresight-hub/tests/test_v0_floor_stay_live.py`
- `apps/caresight-hub/tests/test_agent_assist.py`
- `docs/architecture/ARCHITECTURE.md`
- `docs/architecture/REPO_BOUNDARIES.md`
- `docs/cli/COMMANDS.md`
- `CHANGELOG.md`

Strict actionable steps:

1. Create an `escalation` package with an orchestrator that receives persisted event IDs and chooses allowed post-event flows.
2. Keep event detectors separate: `floor_stay`, `missing_off_camera`, future routine events.
3. Keep escalation methods separate: text, FaceTime, TTS, OBS update, no-send dry-run.
4. Move MJPEG serving into a preview module.
5. Move post-event dry-run/live orchestration into a module independent of the camera loop.
6. Keep the script as a thin CLI wrapper.
7. Preserve existing CLI flags during the first refactor.

Intended resolution:

The live detector script becomes readable and mostly declarative. Event detection, escalation orchestration, handoff methods, and preview serving have explicit module boundaries.

Tests required:

- Existing Python tests remain green.
- Unit test: escalation orchestrator receives `possible_floor_stay` and selects allowed methods.
- Unit test: `missing_off_camera_extended` can be configured as review-only or lower escalation.
- Unit test: CLI help works without importing OpenCV/YOLO.
- Integration-style unit test: no-send post-event pipeline can run without camera hardware.

Resolution notes:

_Open. Codex should update this section after implementation with files changed, commands run, and any remaining risk._

### F005 - `sqlite_store.py` should become a storage orchestrator with digestible stores

Status: Open

Phase: 2

Priority: High

User note: Need main storage orchestrator with different digestible pieces; orchestrators get pulled into a main engine.

Impacted files:

- `apps/caresight-hub/caresight/storage/sqlite_store.py`
- `apps/caresight-hub/caresight/storage/connection.py`
- `apps/caresight-hub/caresight/storage/events.py`
- `apps/caresight-hub/caresight/storage/reviews.py`
- `apps/caresight-hub/caresight/storage/agent_assist.py`
- `apps/caresight-hub/caresight/storage/appearance.py`
- `apps/caresight-hub/caresight/storage/observation_checks.py`
- `apps/caresight-hub/caresight/storage/migrations.py`
- `apps/caresight-hub/tests/test_sqlite_store.py`
- `apps/caresight-hub/tests/test_agent_assist.py`
- `apps/caresight-hub/tests/test_appearance_profiles.py`
- `docs/architecture/ARCHITECTURE.md`
- `CHANGELOG.md`

Strict actionable steps:

1. Keep `SQLiteStore` as a facade/orchestrator for backward compatibility.
2. Extract connection and migration helpers first.
3. Extract event read/write functions.
4. Extract review/journal/handoff functions.
5. Extract agent draft/action/execution attempt functions.
6. Extract appearance profile/sample functions.
7. Extract no-event observation check functions.
8. Add a storage engine diagram to architecture docs.

Intended resolution:

SQLite remains the canonical local blackbox, but storage ownership is split into focused modules with a facade that prevents broad call-site churn.

Tests required:

- Existing storage tests remain green.
- Migration idempotence test.
- Golden row mapping tests for each store module.
- Unit test: facade calls still behave the same.

Resolution notes:

_Open. Codex should update this section after implementation with files changed, commands run, and any remaining risk._

### F006 - `v0.local.json` is tracked despite local-file policy

Status: Open

Phase: 2

Priority: Medium

User note: Agreed, worth resolution.

Impacted files:

- `apps/caresight-hub/config/v0.local.json`
- `apps/caresight-hub/config/v0.example.json`
- `apps/caresight-hub/scripts/caresight_setup_fixtures.py`
- `apps/caresight-hub/scripts/v0_floor_stay_live.py`
- `.gitignore`
- `docs/getting_started.md`
- `docs/cli/COMMANDS.md`
- `docs/FILE_TREE.md`
- `CHANGELOG.md`

Strict actionable steps:

1. Rename tracked demo/default config to `v0.example.json` or `v0.demo.json`.
2. Keep generated `v0.local.json` ignored.
3. Update CLI default behavior to use local config if present, else example config for demo-safe runs.
4. Add setup command to copy example to local.
5. Add validation to prevent newly tracked `*.local.*` files except `.local.example`.

Intended resolution:

No private local config path is tracked. Demo defaults remain available through a tracked example file.

Tests required:

- Scaffold test: tracked `.local.json` files fail unless explicitly example-only.
- CLI test: default config resolution is deterministic.
- Docs check: setup path mentions copying example to local.

Resolution notes:

_Open. Codex should update this section after implementation with files changed, commands run, and any remaining risk._

### F007 - Hard-coded site labeling

Status: Open

Phase: 2

Priority: Medium

User note: Hard-coded labeling is not the way.

Impacted files:

- `apps/caresight-hub/scripts/v0_floor_stay_live.py`
- `apps/obs-hub/tools/update_obs_event.py`
- `apps/obs-hub/config/sample_event.json`
- `apps/caresight-hub/config/live-demo.local.example`
- `apps/caresight-hub/tests/test_demo_surface.py`
- `docs/cli/COMMANDS.md`
- `CHANGELOG.md`

Strict actionable steps:

1. Move `site_name` and `site_mode` to config or CLI args.
2. Default to non-private generic labels such as `CareSight Local Demo`.
3. Add `site_label_source` to overlay payload.
4. Ensure OBS update tools accept and preserve configured labels.
5. Update docs to keep real residence names out of tracked config.

Intended resolution:

Overlay and receipt labels are config-driven and privacy-safe by default.

Tests required:

- Unit test: default overlay label is generic.
- Unit test: local config label is used when provided.
- Unit test: payload includes `site_label_source`.

Resolution notes:

_Open. Codex should update this section after implementation with files changed, commands run, and any remaining risk._

### F016 - `ensure_column()` should validate identifiers

Status: Open

Phase: 2

Priority: Low

User note: Good oversight; worth resolving.

Impacted files:

- `apps/caresight-hub/caresight/storage/sqlite_store.py`
- `apps/caresight-hub/caresight/storage/migrations.py`
- `apps/caresight-hub/tests/test_sqlite_store.py`
- `CHANGELOG.md`

Strict actionable steps:

1. Move migration helpers into `storage/migrations.py`.
2. Add strict identifier validation or a table/column allowlist.
3. Reject invalid table or column identifiers before SQL string interpolation.
4. Keep column definitions hard-coded only.

Intended resolution:

Migration helpers remain safe even if future callers accidentally pass non-hard-coded identifiers.

Tests required:

- Unit test: valid hard-coded migration identifiers pass.
- Unit test: invalid identifier is rejected.
- Unit test: existing initialization remains idempotent.

Resolution notes:

_Open. Codex should update this section after implementation with files changed, commands run, and any remaining risk._

### F017 - Review state changes need explicit lifecycle purposes

Status: Open

Phase: 2

Priority: Medium

User note: Everything should be explicitly noted and purpose driven.

Impacted files:

- `contracts/lifecycle.md`
- `contracts/schemas/care-event.schema.json`
- `contracts/examples/valid/*.event.json`
- `apps/caresight-hub/caresight/runtime/review/service.py`
- `apps/caresight-hub/caresight/storage/reviews.py`
- `apps/caresight-hub/scripts/v0_review_events.py`
- `apps/caresight-hub/tests/test_v0_review_events.py`
- `docs/cli/COMMANDS.md`
- `CHANGELOG.md`

Strict actionable steps:

1. Define allowed lifecycle transitions in `contracts/lifecycle.md`.
2. Add review purpose fields such as `initial_review`, `followup_note`, `amendment`, `correction`.
3. Reject silent final-state flips.
4. Add amendment path for changing a previous review.
5. Make journal entries state the review purpose.

Intended resolution:

Every review mutation has an explicit lifecycle transition and purpose. Final states cannot be silently overwritten.

Tests required:

- Unit test: awaiting -> human_confirmed allowed.
- Unit test: human_confirmed -> dismissed blocked without amendment.
- Unit test: amendment path records previous and new state.
- Contract test: lifecycle examples validate.

Resolution notes:

_Open. Codex should update this section after implementation with files changed, commands run, and any remaining risk._

## Phase 3 - Runtime Validation, Heartbeats, Feed Exposure, Model Governance, and Contracts

### F011 - Unit gates need real runtime probes and heartbeat validation

Status: Open

Phase: 3

Priority: Medium

User note: Unit gates are a running start; probes and heartbeat checks make sense.

Impacted files:

- `contracts/schemas/runtime-validation-receipt.schema.json`
- `apps/caresight-hub/scripts/caresight_demo_preflight.py`
- `apps/caresight-hub/scripts/caresight_camera_probe.py`
- `apps/obs-hub/tools/check_obs_live_feed.py`
- `apps/caresight-hub/scripts/caresight_gemma_start.py`
- `apps/caresight-hub/scripts/caresight_hermes_start.py`
- `apps/caresight-hub/scripts/caresight_tts.py`
- `docs/operations/local_model_operations.md`
- `docs/cli/COMMANDS.md`
- `docs/status/OPERATING_STATUS.md`
- `CHANGELOG.md`

Strict actionable steps:

1. Add `runtime-validation-receipt` schema.
2. Update probe commands to emit receipt-shaped JSON.
3. Add heartbeat mode for non-invasive checks: camera health, OBS feed URL, Gemma endpoint, local disk/database health.
4. Keep live actions out of heartbeat checks.
5. Add docs showing unit gate vs runtime gate vs heartbeat.

Intended resolution:

CareSight has a layered validation model: unit checks for code, runtime probes for setup, and heartbeat checks for ongoing local system health.

Tests required:

- Contract tests for runtime receipts.
- Unit test: heartbeat receipt does not perform live send/call/TTS.
- Unit test: blocked runtime dependency produces blocked receipt.
- CLI test: preflight emits receipt JSON.

Resolution notes:

_Open. Codex should update this section after implementation with files changed, commands run, and any remaining risk._

### F014 - Local MJPEG feed needs explicit LAN exposure/auth policy

Status: Open

Phase: 3

Priority: Medium

User note: Localhost seemed safe; LAN/IP exposure needs auth and cannot just exist online.

Impacted files:

- `contracts/schemas/local-feed-exposure.schema.json`
- `contracts/examples/valid/local-feed-exposure.loopback.json`
- `contracts/examples/invalid/local-feed-exposure-lan-no-token.json`
- `apps/caresight-hub/scripts/v0_floor_stay_live.py`
- `apps/caresight-hub/caresight/runtime/preview/mjpeg.py`
- `apps/caresight-hub/tests/test_v0_floor_stay_live.py`
- `docs/cli/COMMANDS.md`
- `CHANGELOG.md`

Strict actionable steps:

1. Add `local-feed-exposure` schema and examples.
2. Refuse non-loopback bind hosts unless `--allow-lan-preview` is provided.
3. Require a token for LAN feed exposure.
4. Add privacy warning acknowledgment for LAN bind.
5. Emit exposure receipt with bind scope and expiration.

Intended resolution:

Loopback feed remains easy. LAN feed requires explicit operator approval, token protection, and receipt.

Tests required:

- Unit test: default loopback allowed.
- Unit test: `0.0.0.0` blocked without override.
- Unit test: LAN override without token blocked.
- Contract test: LAN no-token example fails.

Resolution notes:

_Open. Codex should update this section after implementation with files changed, commands run, and any remaining risk._

### F015 - Add model doctor and local model manifests

Status: Open

Phase: 3

Priority: Medium

User note: Model doctor is a strong insight.

Impacted files:

- `contracts/schemas/model-manifest.schema.json`
- `contracts/examples/valid/model-manifest.yolo26n.json`
- `contracts/examples/valid/model-manifest.privacy-filter.json`
- `apps/caresight-hub/config/model-manifests.example.json`
- `apps/caresight-hub/scripts/care_console.py`
- `apps/caresight-hub/scripts/caresight_install_models.py`
- `apps/caresight-hub/tests/test_care_console.py`
- `docs/operations/local_model_operations.md`
- `docs/cli/COMMANDS.md`
- `CHANGELOG.md`

Strict actionable steps:

1. Add `model-manifest` schema.
2. Create tracked example manifests for YOLO26n, Gemma, Holler, and Privacy Filter if adopted.
3. Add `care_console.py model-doctor`.
4. Verify local path, checksum, license, purpose lane, and validation command.
5. Fail if a configured model lacks manifest metadata.

Intended resolution:

Local models are treated as governed runtime dependencies with source, license, checksum, purpose, and validation status.

Tests required:

- Contract tests for valid/invalid manifests.
- Unit test: missing manifest fails.
- Unit test: checksum mismatch fails.
- Unit test: valid manifest passes.

Resolution notes:

_Open. Codex should update this section after implementation with files changed, commands run, and any remaining risk._

### F019 - Add contracts for build-phase features that outran governance

Status: Open

Phase: 3

Priority: Medium

User note: Strong basis contracts existed; build portion got sloppy. Restore project ethos.

Impacted files:

- `contracts/schemas/media-sharing-policy.schema.json`
- `contracts/schemas/reply-gated-handoff.schema.json`
- `contracts/schemas/runtime-validation-receipt.schema.json`
- `contracts/schemas/model-manifest.schema.json`
- `contracts/schemas/local-feed-exposure.schema.json`
- `contracts/schemas/retention-policy.schema.json`
- `contracts/schemas/privacy-redaction-receipt.schema.json`
- `contracts/examples/valid/`
- `contracts/examples/invalid/`
- `packages/core/src/validate-contracts.ts`
- `tests/contracts/contract-corpus.test.ts`
- `contracts/README.md`
- `docs/architecture/ARCHITECTURE.md`
- `CHANGELOG.md`

Strict actionable steps:

1. Add schemas one by one in dependency order.
2. For each schema, add at least one valid and one invalid example.
3. Update contract validation mapping.
4. Update `contracts/README.md`.
5. Update runtime docs to point to the new contracts.
6. Do not add runtime behavior until the relevant contract exists.

Intended resolution:

The newest live/demo capabilities are again governed by canonical schemas and fail-closed examples.

Tests required:

- `npm run validate:contracts`
- `npm run test:focused`
- Negative examples prove unsafe behaviors fail.
- Runtime tests consume contract shapes instead of ad hoc dicts where practical.

Resolution notes:

_Open. Codex should update this section after implementation with files changed, commands run, and any remaining risk._

## Phase 4 - Care Intelligence Quality: Replies, Posture, Missing Context, and Privacy Redaction

### F009 - Yes-like reply parsing needs explicit opportunity/intent classification

Status: Open

Phase: 4

Priority: Medium

User note: Smart alteration; can state things for additional opportunity aspects.

Impacted files:

- `contracts/schemas/reply-gated-handoff.schema.json`
- `apps/caresight-hub/caresight/runtime/agent_assist/live_handoff.py`
- `apps/caresight-hub/tests/test_agent_assist.py`
- `docs/cli/COMMANDS.md`
- `CHANGELOG.md`

Strict actionable steps:

1. Replace boolean yes-like parsing with `yes`, `no`, `ambiguous`, and `opportunity` classes.
2. Require explicit phrases for FaceTime: `yes connect`, `yes FaceTime`, or configured phrase.
3. Treat "please wait", "call later", and "start what?" as ambiguous or opportunity, not approval.
4. Add a follow-up draft path for ambiguous replies.
5. Store reply classification in handoff receipt.

Intended resolution:

CareSight can distinguish approval from ambiguity and from useful caregiver context that may shape the next draft.

Tests required:

- Unit tests for `yes connect`, `yes FaceTime`, `ok no`, `please wait`, `call later`, `start what`, `not now`, and `can you call me tomorrow`.
- Contract test: ambiguous reply cannot authorize live FaceTime.

Resolution notes:

_Open. Codex should update this section after implementation with files changed, commands run, and any remaining risk._

### F012 - Add pose/depth/segmentation as a measured value-add, not a fast claim

Status: Open

Phase: 4

Priority: Medium

User note: Important value add but not a fast implementation.

Impacted files:

- `docs/evaluation/posture_pose_segmentation_plan.md`
- `apps/caresight-hub/caresight/events/floor_stay.py`
- `apps/caresight-hub/caresight/runtime/inference/`
- `apps/caresight-hub/config/model-manifests.example.json`
- `apps/caresight-hub/tests/test_floor_stay.py`
- `docs/roadmaps/CURRENT_STATE_AND_NEXT.md`
- `CHANGELOG.md`

Strict actionable steps:

1. Keep current YOLO box-derived posture as baseline.
2. Add evaluation plan before adding a new model path.
3. Define pose/depth/segmentation candidate interfaces as advisory evidence only.
4. Compare candidates on seated-floor, lying-low, couch, recliner, low-light, partial-body, and multi-person cases.
5. Do not change product claims until evaluation receipts exist.

Intended resolution:

Pose/depth/segmentation becomes a measured advisory lane that can improve posture clarity without prematurely claiming fall detection or medical certainty.

Tests required:

- Unit test: advisory evidence cannot alone create a stronger claim.
- Evaluation fixture test: seated-on-floor remains non-event.
- Evaluation fixture test: lying-low in calibrated floor zone creates possible event after dwell.
- Model manifest tests for any added candidate model.

Resolution notes:

_Open. Codex should update this section after implementation with files changed, commands run, and any remaining risk._

### F013 - Missing-off-camera needs contextual nuance and longer/localized windows

Status: Open

Phase: 4

Priority: Medium

User note: Strong indicator, but hardest local boundary; needs contextual nuance and likely longer missing window.

Impacted files:

- `apps/caresight-hub/caresight/events/missing_off_camera.py`
- `apps/caresight-hub/caresight/runtime/config.py`
- `apps/caresight-hub/config/v0.example.json`
- `contracts/schemas/care-event.schema.json`
- `contracts/examples/valid/missing-off-camera.event.json`
- `apps/caresight-hub/tests/test_missing_off_camera.py`
- `apps/caresight-hub/tests/test_multi_camera_narrative.py`
- `docs/cli/COMMANDS.md`
- `docs/roadmaps/CURRENT_STATE_AND_NEXT.md`
- `CHANGELOG.md`

Strict actionable steps:

1. Add per-camera and per-room missing windows.
2. Add `absence_expected_after_seconds` and `quiet_hours`.
3. Suppress or downgrade missing-off-camera when another camera has likely continuity.
4. Add review reason fields explaining why the indicator fired.
5. Extend default missing window for normal household use unless demo mode overrides it.

Intended resolution:

Missing-off-camera becomes a contextual review indicator rather than a noisy "person missing" style alert.

Tests required:

- Unit test: short room exit does not fire.
- Unit test: longer absence fires advisory event.
- Unit test: second camera likely-continuity suppresses or downgrades event.
- Contract test: missing event cannot claim named identity, danger, or emergency.

Resolution notes:

_Open. Codex should update this section after implementation with files changed, commands run, and any remaining risk._

### F018 - Journal notes need redaction/export classification, optionally using OpenAI Privacy Filter

Status: Open

Phase: 4

Priority: Medium

User note: Consider local OpenAI Privacy Filter model from Hugging Face.

Impacted files:

- `contracts/schemas/privacy-redaction-receipt.schema.json`
- `contracts/schemas/model-manifest.schema.json`
- `contracts/examples/valid/model-manifest.privacy-filter.json`
- `apps/caresight-hub/caresight/storage/reviews.py`
- `apps/caresight-hub/caresight/runtime/journal/service.py`
- `apps/caresight-hub/caresight/runtime/privacy/redaction.py`
- `apps/caresight-hub/scripts/care_console.py`
- `apps/caresight-hub/tests/test_v0_review_events.py`
- `apps/caresight-hub/tests/test_care_console.py`
- `docs/operations/local_model_operations.md`
- `docs/cli/COMMANDS.md`
- `CHANGELOG.md`

Strict actionable steps:

1. Add journal export classifications: local-only, caregiver-shareable, clinical-review, do-not-share.
2. Add `privacy-redaction-receipt` schema.
3. Add optional local Privacy Filter manifest and model doctor support.
4. Add redaction command that can run locally on journal text before export.
5. Require human review for high-sensitivity redactions.
6. Document that Privacy Filter is not compliance or anonymization proof.

Intended resolution:

Journal notes can be classified and optionally redacted before external sharing, while preserving local canonical text and avoiding compliance overclaims.

Tests required:

- Contract test: valid redaction receipt passes.
- Contract test: redaction receipt claiming HIPAA/anonymization guarantee fails.
- Unit test: local-only note is blocked from caregiver export.
- Unit test: redaction receipt records labels and human review requirement.

Resolution notes:

_Open. Codex should update this section after implementation with files changed, commands run, and any remaining risk._

## Phase 5 - Documentation Visibility and Operator Usability

### F020 - Split operational docs and add short operating status

Status: Open

Phase: 5

Priority: Medium

User note: Short operating status doc and split command categories/index are strong visibility layers.

Impacted files:

- `docs/status/OPERATING_STATUS.md`
- `docs/cli/COMMANDS.md`
- `docs/cli/README.md`
- `docs/cli/setup.md`
- `docs/cli/camera.md`
- `docs/cli/detection.md`
- `docs/cli/review.md`
- `docs/cli/agent-handoff.md`
- `docs/cli/obs-tts-facetime.md`
- `docs/cli/validation.md`
- `docs/roadmaps/CURRENT_STATE_AND_NEXT.md`
- `README.md`
- `docs/FILE_TREE.md`
- `CHANGELOG.md`

Strict actionable steps:

1. Add `docs/status/OPERATING_STATUS.md` with current feature status, tests completed, and remaining work.
2. Split `docs/cli/COMMANDS.md` into categorized files.
3. Keep `docs/cli/COMMANDS.md` as a generated or curated index.
4. Add a "safe to run unattended" vs "human-review-required" command classification.
5. Link operating status from README and roadmap.

Intended resolution:

Operators and future agents can quickly see current status, safe commands, manual gates, and remaining validation work without reading a thousand-line command file.

Tests required:

- Scaffold/file-tree validation passes.
- Docs link check if available.
- Command index includes every supported CLI command.
- Manual spot check: current demo command and remaining gates are visible in under two minutes.

Resolution notes:

_Open. Codex should update this section after implementation with files changed, commands run, and any remaining risk._

## Recommended Execution Order

1. F001, F002, F003.
2. F008, F010.
3. F006, F007, F016, F017.
4. F004.
5. F005.
6. F011, F014, F015, F019.
7. F009, F013.
8. F018.
9. F012.
10. F020.

## Closeout Requirements for Each Phase

For every phase, Codex should update this document with:

- Status changes per finding.
- Exact files changed.
- Exact commands run.
- Test output summary.
- Any skipped tests and why.
- Remaining risk.
- Follow-up tasks.

Do not mark a finding resolved unless:

- Intended resolution is implemented.
- Required tests exist and pass, or a written reason explains why a test is impractical.
- Docs and changelog are updated.
- No unrelated files are staged.
