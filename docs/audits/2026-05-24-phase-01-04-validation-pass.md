# Phase 1-4 Bug-Fix Validation Pass

Date: 2026-05-24

Source plan: `docs/audits/2026-05-24-bug-fix-phased-cleanup-plan.md`

Scope: separate validation pass for Phases 1, 2, 3, and 4 only. Phase 5 / F020 documentation visibility work is intentionally excluded except where it affects the ability to validate Phases 1-4.

## Top-Level Awareness Statement

Validation status: Phases 1-4 are accepted as code-and-contract resolved with residual runtime proof gaps noted below.

Findings covered: F001-F019.

Findings accepted in this validation pass:

- Verified: F001, F002, F003, F006, F007, F008, F009, F010, F011, F014, F015, F016, F017, F019.
- Verified with residual risk: F004, F005, F012, F013, F018.
- Not validated in this pass: F020, because it belongs to Phase 5.

Tests completed:

- `npm run validate:contracts` passed: 22 schemas, 29 valid examples, 28 invalid examples.
- `npm run py:check` passed: 204 Python tests.
- `npm run check` passed: scaffold validation, contract validation, focused TypeScript tests, full TypeScript tests, TypeScript typecheck, and 204 Python tests.
- `python3 apps/caresight-hub/scripts/care_console.py model-doctor --model-id model_yolo26n_mlx` passed for `model_yolo26n_mlx`.
- `python3 apps/caresight-hub/scripts/caresight_demo_preflight.py --heartbeat --json` completed with `status: warn`, `ready: true`, and no live actions. Warn items were optional/not-running runtime surfaces: detector MJPEG feed, Aitum canvas, and Gemma endpoint.
- `python3 apps/caresight-hub/scripts/caresight_camera_probe.py --config apps/caresight-hub/config/tapo.local.example.json --dry-run` completed as a non-invasive `runtime-validation-receipt` with redacted URI and no camera connection attempted.

More work remains: yes. Phase 5 is still open, and several Phase 1-4 runtime claims remain code/probe validated rather than physically live-validated. This pass does not prove live iMessage delivery, FaceTime calling, TTS playback into a call, active Gemma endpoint health, active OBS MJPEG feed health, or HIPAA/compliance readiness.

## Validation Method

This pass used repository evidence rather than the previous resolution notes alone:

- Read the phase plan top-level status and per-finding resolution notes.
- Inspected live handoff, contact allowlisting, storage, migrations, review transitions, runtime loop, missing-off-camera, privacy redaction, model doctor, and contract registration code.
- Confirmed command documentation exists for the new CLI/runtime surfaces.
- Ran deterministic gates and selected non-invasive runtime-shaped probes.

## Phase 1: Live Handoff Authority, Receipts, and Media Policy

Status: verified.

Findings: F001, F002, F003, F008, F010.

### F001 - Live iMessage Target Must Match Allowlisted Contact

Validation result: verified.

Evidence:

- `apps/caresight-hub/caresight/runtime/agent_assist/live_handoff.py` resolves explicit, environment, and allowlist contact targets through `resolve_contact_target`.
- `apps/caresight-hub/caresight/runtime/agent_assist/contacts.py` verifies target values against allowlisted channel refs or approved hashes.
- `apps/caresight-hub/tests/test_agent_assist.py` includes contact allowlist blocks for unknown live destinations.

Residual risk: none found for the intended fix.

### F002 - Live Execution Needs Durable Pending/Failed Receipts

Validation result: verified.

Evidence:

- `execute_live_imessage` and `execute_facetime_if_yes` insert `pending_execution` attempts before external action and update the same attempt to `executed`, `dry_run`, or `failed`.
- `SQLiteStore.update_agent_execution_attempt` preserves attempt identity and prevents request/event mutation.
- `agent_execution_attempts` migration path allows `pending_execution`.

Residual risk: no live-send proof was run in this pass, by design.

### F003 - Live TTS Playback Needs Receipt Coverage

Validation result: verified.

Evidence:

- `record_tts_playback_pending_attempt` records a pending attempt before TTS playback.
- `record_tts_playback_attempt` updates that attempt to `executed` or `failed` with route, voice, repeat count, and bounded safety fields.
- `npm run py:check` includes storage and handoff tests covering execution attempts.

Residual risk: no audio playback was performed in this pass.

### F008 - Reply-Gated FaceTime Needs a Contract-Like Receipt

Validation result: verified.

Evidence:

- `contracts/schemas/reply-gated-handoff.schema.json` and valid/invalid examples are registered in contract validation.
- `classify_reply_intent` distinguishes explicit `yes connect` / `yes facetime` from ambiguous, opportunity, and negative replies.
- `execute_facetime_if_yes` records a `reply_gated_handoff` receipt and only opens FaceTime after a yes classification, allowlisted target verification, response-option permission, and live approval.

Residual risk: no actual FaceTime call was opened in this pass.

### F010 - Snapshot/Media Sharing Needs Explicit Policy

Validation result: verified.

Evidence:

- `contracts/schemas/media-sharing-policy.schema.json` and examples are registered.
- `build_event_snapshot_media_policy` creates event-scoped snapshot policy metadata and blocks raw video/continuous feed.
- `_validate_media_attachment_policy` rejects missing policy, wrong media type, wrong scope, unapproved state, incomplete redaction when required, and missing `raw_video` block.

Residual risk: redaction status is a policy receipt field for the snapshot path; this pass did not inspect a visual redaction engine output.

## Phase 2: Readability, Boundaries, Lifecycle, and Config Hygiene

Status: accepted with residual extraction risk.

Findings: F004, F005, F006, F007, F016, F017.

### F004 - Post-Event Pipeline Should Become Explicit Orchestration Pieces

Validation result: verified with residual risk.

Evidence:

- Added explicit orchestration pieces under `apps/caresight-hub/caresight/runtime/escalation/`, `runtime/live_loop.py`, and `runtime/post_event_pipeline.py`.
- `plan_escalation` separates event type from escalation methods and keeps missing-off-camera review-only by default.
- `v0_floor_stay_live.py` now calls named helpers for loop stopping, live handoff gating, missing event construction, preview exposure, and post-event live/dry-run behavior.

Residual risk: `apps/caresight-hub/scripts/v0_floor_stay_live.py` remains a very large compatibility CLI surface. The intended direction is validated, but full human-readability extraction is not complete.

### F005 - Storage Should Have Digestible Boundaries

Validation result: verified with residual risk.

Evidence:

- Storage helper modules now exist for connection, migrations, reviews, events, appearance, agent assist, and observation checks.
- `SQLiteStore` uses `sqlite_connection`, `SCHEMA_SQL`, `ensure_column`, and `validate_review_transition`.
- Migration helper validates SQLite identifiers before `ALTER TABLE`.

Residual risk: `SQLiteStore` remains large and acts as a facade over many domains. This is acceptable for this phase but should continue to be split behind stable tests.

### F006 - Tracked Local Config Should Be Removed/Fallback Should Be Explicit

Validation result: verified.

Evidence:

- `v0.local.json` is no longer the tracked default artifact; `v0.example.json` is tracked.
- `resolve_default_config_path` uses ignored local config when present, otherwise tracked example config.
- `scripts/validate-scaffold.ts` blocks tracked `*.local.json` config files except `.local.example.json`.

Residual risk: none found for the intended fix.

### F007 - Hard-Coded Labels Should Use COCO Source of Truth

Validation result: verified.

Evidence:

- `class_name` falls back to `caresight.vision.coco.coco_name`.
- Placeholder model names such as `class_0` are rejected by `is_placeholder_name`.
- `DISPLAY_LABELS` controls which labels are drawn without turning the model names into canonical class truth.

Residual risk: none found for the intended fix.

### F016 - Review Final-State Mutations Need Explicit Lifecycle Controls

Validation result: verified.

Evidence:

- `apps/caresight-hub/caresight/storage/reviews.py` enforces review purposes, amendment requirements, and final-state transition restrictions.
- `record_event_review` persists `review_purpose`, `previous_status`, and `amendment_of_review_id`.
- `contracts/lifecycle.md` documents the same lifecycle rule.

Residual risk: none found for the intended fix.

### F017 - Site/OBS Labels Should Be Purpose-Driven and Not Hard-Coded

Validation result: verified.

Evidence:

- `v0_floor_stay_live.py` accepts `--site-name` and `--site-mode`.
- OBS update payload records `site_label_source`.
- `CareSightConfig` supports `site` metadata.

Residual risk: default generic labels still exist for safe fallback, which is intentional.

## Phase 3: Runtime Validation, Feed Exposure, Model Governance, Contracts

Status: verified.

Findings: F011, F014, F015, F019.

### F011 - Runtime Gates and Heartbeats

Validation result: verified.

Evidence:

- `contracts/schemas/runtime-validation-receipt.schema.json` and examples are registered.
- `caresight_demo_preflight.py --heartbeat --json` produced a `runtime-validation-receipt` with `no_live_send`, `no_facetime_call`, `no_tts_playback`, and `local_probe_only`.
- Heartbeat result was `status: warn`, `ready: true`; warning items were optional/not-running runtime surfaces rather than blockers.

Residual risk: this pass did not start detector MJPEG, Gemma, Hermes, OBS websocket/live feed, TTS playback, or live handoff. Those remain runtime validation gates.

### F014 - Localhost Preview Is Safe, LAN Preview Needs Auth/Receipt

Validation result: verified.

Evidence:

- `validate_preview_exposure` refuses non-loopback binds unless `--allow-lan-preview`, `--preview-token`, and `--ack-lan-preview-risk` are provided.
- `contracts/schemas/local-feed-exposure.schema.json` requires token/operator/privacy acknowledgement for LAN exposure.
- `MjpegPreviewServer` requires token authorization for LAN mode.

Residual risk: no live LAN MJPEG server was started in this pass.

### F015 - Model Doctor

Validation result: verified.

Evidence:

- `contracts/schemas/model-manifest.schema.json` and examples are registered.
- `care_console.py model-doctor --model-id model_yolo26n_mlx` passed with matching size and SHA-256 for the local YOLO26n MLX model.
- Manifest includes purpose lane, runtime, source URL, license, allowed uses, blocked uses, checksum, and validation command.

Residual risk: privacy-filter model validation was not run in this pass.

### F019 - Contract Ethos Was Restored

Validation result: verified.

Evidence:

- Contract validation now covers 22 schemas and both positive/negative examples for new Phase 1-4 contracts.
- `packages/core/src/validate-contracts.ts` registers the new schemas.
- `npm run check` includes scaffold, contract, TypeScript, and Python gates.

Residual risk: none found for the intended fix.

## Phase 4: Care Intelligence Quality and Privacy Boundaries

Status: accepted with residual runtime/model risk.

Findings: F009, F012, F013, F018.

### F009 - Reply Opportunity/Ambiguity Should Be Represented

Validation result: verified.

Evidence:

- `classify_reply_intent` returns `yes`, `no`, `ambiguous`, and `opportunity`.
- Non-yes replies produce local follow-up drafts rather than external action.
- Reply receipts preserve reply classification and required phrase.

Residual risk: none found for the intended fix.

### F012 - Pose/Depth/Segmentation Should Be Added as Advisory Evidence, Not False Authority

Validation result: verified with residual risk.

Evidence:

- `advisory_posture_evidence` is included in floor-stay diagnostics and event evidence.
- `apps/caresight-hub/caresight/runtime/inference/advisory_evidence.py` defines advisory-only pose, depth, and segmentation placeholders.
- Floor-stay event evidence explicitly states `claim_boundary: cannot_confirm_fall_or_injury`.

Residual risk: pose, depth, and segmentation are not implemented model lanes yet. The validation accepts that the current fix correctly prevents false authority, not that those modalities exist.

### F013 - Missing-Off-Camera Needs Contextual Nuance

Validation result: verified with residual risk.

Evidence:

- `MissingOffCameraDetector` uses configurable missing windows, dedupe per track, recent-concern severity, quiet hours, last-seen snapshot evidence, and bounded caregiver language.
- Event evidence includes `not_claimed` boundaries for named identity, danger, emergency, and dispatch.
- `v0_floor_stay_live.py` only emits missing events when `--missing-off-camera-events` is enabled.

Residual risk: this remains a single-camera/track-continuity heuristic. Cross-camera continuity and authorized care-plan context are not implemented.

### F018 - Privacy Filter / Redaction Receipts

Validation result: verified with residual risk.

Evidence:

- `contracts/schemas/privacy-redaction-receipt.schema.json` and valid/invalid examples are registered.
- `build_privacy_redaction_receipt` records engine, optional model manifest ID, labels, redaction status, and explicit `not_claimed` boundaries.
- `journal-redaction-preview` documentation states Privacy Filter/local rules are aids only, not anonymization or HIPAA compliance.

Residual risk: current implementation is primarily local-rule receipt wiring plus a selectable `openai_privacy_filter` receipt lane. This pass did not run the OpenAI Privacy Filter model, and no compliance guarantee is justified by this layer alone.

## Cross-Cutting Observations

- The prior cleanup pass left many new files untracked. This validation accepts behavior in the current worktree but does not imply the changes have been staged or committed.
- `docs/FILE_TREE.md` was current before adding this validation report. It must be regenerated after this file is added.
- Phase 5 should keep the current distinction between deterministic code gates, runtime probes, and physical/live validation. The cleanup plan already says more runtime integration gates remain.

## Recommendation Before Phase 5

Proceed to Phase 5 documentation work, but carry these open validation statements forward:

- Phases 1-4 are code-and-contract resolved.
- Runtime validation is partial, not production validation.
- F004/F005 are improved but not fully extracted.
- F012 is advisory scaffolding, not real pose/depth/segmentation inference.
- F013 is bounded single-camera missing-context logic, not identity or safety determination.
- F018 is privacy aid/receipt plumbing, not anonymization, HIPAA compliance, or medical privacy clearance.
