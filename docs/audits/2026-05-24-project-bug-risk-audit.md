# CareSight Project Bug and Risk Audit

Date: 2026-05-24

Scope: repository-only audit of the current CareSight checkout at `/Users/steven/Workspace/40_Code/hackathons/CareSight`.

Instruction boundary: this report identifies issues and remediation paths only. No runtime fixes were made as part of this audit.

Follow-up phased cleanup control plan: `docs/audits/2026-05-24-bug-fix-phased-cleanup-plan.md`.

Validation baseline:

- `npm run check` passed on 2026-05-24.
- Gate coverage included scaffold validation, contract validation, Vitest tests, TypeScript typecheck, and Python unittest discovery.
- Python result: 175 tests passed.
- Git worktree was clean before report creation.

## Executive Summary

CareSight has strong architectural guardrails for a hackathon prototype: contract validation passes, the Python runtime has meaningful deterministic tests, forbidden-claim examples exist, and the docs repeatedly preserve the local-first, human-review boundary.

The main risks are not basic syntax failures. They are authority-boundary gaps, operational audit gaps, privacy leakage risks, and maintainability pressure from large scripts that now combine detection, OBS presentation, local LLM drafting, iMessage, FaceTime, reply watching, and TTS playback.

The highest-priority issues to address after the hackathon:

1. Live contact target override can bypass the private allowlist target mapping.
2. Live external action attempts are recorded after the send/call/playback attempt, not before.
3. The live handoff path can send event snapshots externally under live approval, which needs an explicit media-sharing policy and receipt boundary.
4. `v0_floor_stay_live.py` and `sqlite_store.py` are too large for the repo's own file-size rule and now hide multiple ownership boundaries.
5. `v0.local.json` is tracked even though the ignore policy says `*.local.json` should stay local.
6. The current unit gate passes, but it does not exercise a real camera loop, real OBS websocket state, real local LLM endpoint, real `imsg`, real FaceTime, or TTS audio routing.

## Severity Key

- Critical: can cause autonomous unsafe action, privacy disclosure, data loss, or severe misleading claim.
- High: likely to break the bounded control loop, audit trail, or private-data boundary under realistic use.
- Medium: likely operational bug, confusing state, missing validation, or reliability issue.
- Low: cleanup, maintainability, documentation drift, or non-urgent hardening.

## Findings

### F001 - Explicit live target bypasses the allowlist target mapping

Severity: High

Files:

- `apps/caresight-hub/caresight/runtime/agent_assist/live_handoff.py`
- `apps/caresight-hub/scripts/v0_floor_stay_live.py`

Evidence:

- `resolve_contact_target()` returns `explicit_target` immediately before loading the allowlist.
- `execute_live_imessage()` validates that the staged request allows `contact_id`, then passes `target=live_imessage_target`.
- The allowlist proves the `contact_id` is allowed, but the explicit target string can be arbitrary.

Why it matters:

The intended contract is "allowlisted recipient only." In the current path, an operator or script can combine an allowlisted contact ID with a different explicit iMessage or FaceTime target. That weakens the contact-privacy and caregiver-approval boundary.

Risk scenario:

`--allowed-contact-id contact_emergency_primary --live-imessage-target wrong@example.com --live-approved` could send the approved text to a non-allowlisted target while the execution receipt still references the allowlisted contact ID.

Recommended remediation:

- Resolve explicit targets only if they match the allowlist record or a hashed allowlist alias.
- Add a separate `--override-target` escape hatch only for manual test mode, requiring a distinct flag and writing `target_override_used=true`.
- Store the target source and allowlist verification result in the execution attempt.

Validation:

- Add a unit test where a staged request allows `contact_emergency_primary`, but an explicit target does not match its configured channel refs. Expected result: blocked before send/open.
- Add a positive test for an explicit target that matches the private allowlist.

### F002 - Live action attempts are logged after execution instead of before execution

Severity: High

Files:

- `apps/caresight-hub/caresight/runtime/agent_assist/live_handoff.py`
- `DECISIONS.md`

Evidence:

- `send_imessage()` is called before `_build_live_attempt()` and `store.insert_agent_execution_attempt()`.
- `open_facetime()` is called before the FaceTime attempt row is inserted.
- TTS playback is performed before `record_tts_playback_attempt()` inserts the attempt.
- `DECISIONS.md` says external-action attempts should be logged before live execution.

Why it matters:

If iMessage sends successfully and SQLite insertion fails afterward, the system performs an external action without a durable audit row. That violates the blackbox/audit premise.

Recommended remediation:

- Insert a preflight attempt row with `execution_state=pending_execution` before the external action.
- Update that same row to `executed`, `failed`, or `blocked` afterward.
- If the preflight insert fails, do not send/open/play.

Validation:

- Add tests using a store double that fails on attempt insertion. Expected result: no send function is invoked.
- Add tests using a send double that fails after preflight insert. Expected result: attempt row is updated to failed.

### F003 - Event snapshots can leave the local boundary without an explicit media-sharing contract

Severity: High

Files:

- `apps/caresight-hub/scripts/v0_floor_stay_live.py`
- `apps/caresight-hub/caresight/runtime/agent_assist/live_handoff.py`
- `docs/cli/COMMANDS.md`

Evidence:

- No-response escalation can attach `snapshot_path` or OBS `live_preview.jpg`.
- The default escalation copy says "Please see the image attached".
- The architecture says raw video stays local by default. Event-scoped screenshots may be acceptable, but they need a clearer contract than general "raw video stays local" language.

Why it matters:

A snapshot from inside a home can expose a resident, visitor, child, medication area, room layout, or sensitive routine. The current live approval covers a message path, but the media-sharing boundary should be separately explicit.

Recommended remediation:

- Add a `media-sharing-policy` contract or extend `agent-action-request` with `media_attachment_policy`.
- Require explicit operator approval for `send_event_snapshot`, separate from text send approval.
- Redact or blur outside the event box where practical before sending.
- Store `attachment_source`, `redaction_status`, `human_media_approval`, and `attachment_hash` in execution attempts.

Validation:

- Add tests that no-response escalation with an attachment is blocked unless `media_attachment_policy=approved_event_scoped_snapshot`.
- Add receipt tests proving no raw stream/video file is attached.

### F004 - `v0_floor_stay_live.py` has become an unsafe ownership bundle

Severity: High

File:

- `apps/caresight-hub/scripts/v0_floor_stay_live.py`

Evidence:

- File length is 1,778 lines.
- It owns argument parsing, camera capture/reconnect, YOLO result conversion, floor-stay loop, missing-off-camera policy invocation, snapshot writes, MJPEG serving, OBS preview writes, appearance sampling, local Gemma drafting, Hermes dry-run staging, live iMessage, reply watch, FaceTime, TTS, and execution receipts.
- The repo rule says files above 500 lines require extraction or written justification.

Why it matters:

Safety-sensitive logic is now mixed with demo orchestration. Bugs in one layer are harder to isolate, and live external actions are close to event persistence logic.

Recommended remediation:

Extract into explicit modules:

- `runtime/live_loop.py`: frame loop and detector invocation.
- `runtime/preview/mjpeg.py`: MJPEG feed.
- `runtime/post_event_pipeline.py`: dry-run/live post-event orchestration.
- `runtime/handoff/media_policy.py`: snapshot attachment policy.
- `scripts/v0_floor_stay_live.py`: thin CLI only.

Validation:

- Preserve existing 175 Python tests.
- Add module-level tests around post-event state transitions without camera/OpenCV imports.
- Keep CLI help import-light and deterministic.

### F005 - `sqlite_store.py` violates the size rule and mixes storage, migration, domain reads, and write services

Severity: Medium

File:

- `apps/caresight-hub/caresight/storage/sqlite_store.py`

Evidence:

- File length is 1,358 lines.
- It includes schema initialization, additive migrations, event persistence, review lifecycle writes, appearance profile tables, agent draft/action request tables, execution attempts, no-event checks, row mappers, journal text, automation reviewer checks, and migration loading.

Why it matters:

SQLite is the canonical blackbox. A large mixed store makes it harder to enforce non-destructive migrations, transaction boundaries, and test doubles for external-action audit behavior.

Recommended remediation:

Split by durable table ownership:

- `storage/connection.py`
- `storage/events.py`
- `storage/reviews.py`
- `storage/agent_assist.py`
- `storage/appearance.py`
- `storage/observation_checks.py`
- `storage/migrations.py`

Validation:

- Golden tests for existing event, review, journal, handoff, draft, action request, execution attempt, and appearance rows.
- Migration idempotence tests against an older fixture database.

### F006 - `v0.local.json` is tracked despite the local-file ignore policy

Severity: Medium

Files:

- `.gitignore`
- `apps/caresight-hub/config/v0.local.json`

Evidence:

- `.gitignore` ignores `apps/caresight-hub/config/*.local.json`.
- `git ls-files` shows `apps/caresight-hub/config/v0.local.json` is tracked.

Why it matters:

The current file is mostly demo-safe, but tracking a `.local.json` path trains contributors to put local configuration into Git. Future edits could accidentally commit camera IDs, local IPs, room layouts, thresholds, or private source URIs.

Recommended remediation:

- Rename tracked default config to `v0.example.json` or `v0.demo.json`.
- Keep `v0.local.json` ignored and generated by setup.
- Add scaffold validation that fails if new tracked `*.local.*` files appear outside explicitly allowed examples.

Validation:

- `git ls-files | rg '\\.local\\.'` should return only `.local.example` or explicitly documented non-secret templates.

### F007 - `update_obs_overlay()` hard-codes site identity

Severity: Medium

File:

- `apps/caresight-hub/scripts/v0_floor_stay_live.py`

Evidence:

- The helper uses `site_name="Maple Residence"` and `site_mode="Observation Mode"` directly.

Why it matters:

Site identity is operator context, not runtime truth. A hard-coded site label can leak into OBS overlays and receipts even when the config describes a different home.

Recommended remediation:

- Move site display fields into ignored local config or a tracked demo config.
- Include `site_label_source` in the overlay receipt.
- Default to "Local CareSight Demo" when no local site config exists.

Validation:

- Unit test that overlay payload uses local config value.
- Unit test that no default private residence label appears in generated overlay state.

### F008 - FaceTime path validates an iMessage destination rather than an explicit FaceTime handoff permission

Severity: Medium

File:

- `apps/caresight-hub/caresight/runtime/agent_assist/live_handoff.py`

Evidence:

- `execute_facetime_if_yes()` calls `_validate_live_request(... destination="imessage")`.
- The staged request may include response options, but the validator does not require `request_facetime_handoff`.

Why it matters:

The current design treats FaceTime as a reply-gated continuation of an iMessage request. That can be acceptable, but the code should prove the staged request allowed that continuation. Otherwise any staged iMessage request could become a FaceTime attempt after a yes-like reply.

Recommended remediation:

- Add `allowed_followup_actions` or require `request_facetime_handoff` in `response_options`.
- Validate the FaceTime channel and contact ID separately.

Validation:

- Negative test: staged iMessage request without FaceTime response option must not open FaceTime.
- Positive test: staged request with FaceTime response option and yes-like reply may proceed.

### F009 - Yes-like reply parsing is intentionally simple but too permissive for live calls

Severity: Medium

File:

- `apps/caresight-hub/caresight/runtime/agent_assist/live_handoff.py`

Evidence:

- Affirmative terms include short tokens such as `ok`, `please`, `call`, `start`, and `go ahead`.
- Negative terms are checked first, but ambiguous replies like "please wait", "call me later", or "start what?" may still be interpreted incorrectly depending on token content.

Why it matters:

Opening FaceTime after an ambiguous text reply is a user-trust issue. It is not emergency dispatch, but it is still an external action.

Recommended remediation:

- Require an explicit phrase for call actions, such as "yes connect" or "yes FaceTime".
- Add a confirmation reply step for ambiguous positives.
- Classify replies as `yes`, `no`, `ambiguous`, or `timeout`.

Validation:

- Add test cases for "please wait", "call later", "ok no", "yes connect", "start what", and "not now".

### F010 - External live actions are still stored as action attempts, but source action requests remain `not_executed`

Severity: Medium

Files:

- `apps/caresight-hub/caresight/runtime/agent_assist/live_handoff.py`
- `apps/caresight-hub/caresight/storage/sqlite_store.py`

Evidence:

- `_build_live_attempt()` records `execution_state=executed` on the attempt payload.
- The source `agent_action_requests` row is validated as `not_executed` and is not updated.

Why it matters:

Keeping the staged request immutable is defensible, but the operational UI must not show a request as still pending after a live send was executed. The current model relies on consumers joining attempt rows correctly.

Recommended remediation:

- Preserve immutable request rows but add a derived request status read model.
- Or add `last_attempt_state` fields while preserving the original staging fields.

Validation:

- Dashboard/list-action-request tests should show "executed attempt exists" when a live attempt row is present.

### F011 - Real-world runtime surfaces are not covered by the deterministic gate

Severity: Medium

Evidence:

- `npm run check` passes, but the test suite does not prove camera hardware, OBS websocket, MJPEG freshness, local Gemma endpoint, `imsg`, Messages DB access, FaceTime, BlackHole routing, or audio playback.

Why it matters:

The codebase has many local-integration surfaces. Passing tests are necessary but not sufficient for production readiness.

Recommended remediation:

- Keep unit gate as the fast default.
- Add explicit operator-owned runtime gates:
  - camera probe gate
  - detector 90-second gate
  - MJPEG freshness gate
  - OBS source URL gate
  - Gemma endpoint gate
  - Hermes no-send gate
  - iMessage dry-run gate
  - one human-approved live send gate
  - FaceTime no-call setup gate
  - TTS generation and playback gate

Validation:

- Every runtime gate should write a timestamped audit receipt under `docs/audits/production-validation/` or ignored local runtime receipts.

### F012 - Floor-stay posture is box-derived and cannot distinguish many real fall/seated/low-posture cases

Severity: Medium

File:

- `apps/caresight-hub/caresight/events/floor_stay.py`

Evidence:

- `posture_evidence()` uses aspect ratio and center Y.
- `floor_stay_eligible` requires `aspect_ratio >= 2.0`, low center, and floor-zone intersection.

Why it matters:

The wording is bounded, but accuracy will be brittle. A curled person, a partially occluded person, an overhead camera, a wide couch posture, or a pet/person overlap can produce false negatives or false positives.

Recommended remediation:

- Keep current rule as a cheap first pass.
- Add a pose/depth/segmentation comparison lane before any stronger claim.
- Record false positive/false negative fixtures by camera perspective.

Validation:

- Build an evaluation matrix: seated floor, lying floor, couch/recliner, pet occlusion, partial body, overhead camera, far small person, two-person crossing.

### F013 - Missing-off-camera event can become noisy without per-room baseline and visibility state checks

Severity: Medium

Files:

- `apps/caresight-hub/scripts/v0_floor_stay_live.py`
- `apps/caresight-hub/caresight/events/missing_off_camera.py`

Evidence:

- Live loop can emit `missing_off_camera_extended` from a last-seen cache when a tracked person is absent beyond configured seconds.
- Current v0 config sets `missing_seconds` to 30 seconds.

Why it matters:

In a home, people routinely leave a room. This event needs strong per-room expectations and caregiver-configured quiet windows to avoid alert fatigue.

Recommended remediation:

- Add per-camera `absence_expected_after_seconds`.
- Add "room exit expected" zones.
- Add event suppression if another camera sees a likely same person.
- Add quiet hours and caregiver-specific alert thresholds.

Validation:

- Multi-camera tests where a person leaves Living Room and appears in Kitchen should suppress or downgrade missing-off-camera.

### F014 - Local HTTP MJPEG feed has no authentication boundary

Severity: Medium

File:

- `apps/caresight-hub/scripts/v0_floor_stay_live.py`

Evidence:

- The default bind host is `127.0.0.1`, which is good.
- The CLI permits `--obs-browser-feed-host`.

Why it matters:

If bound to `0.0.0.0` or a LAN IP for convenience, the MJPEG feed could expose annotated home video on the network.

Recommended remediation:

- Refuse non-loopback hosts unless `--allow-lan-preview` is provided.
- Print a privacy warning and store a receipt when LAN binding is used.
- Add a tokenized local URL for non-loopback preview.

Validation:

- Unit test default loopback.
- Negative test non-loopback without explicit override.

### F015 - Local runtime model artifacts are ignored, but setup has no manifest verification gate

Severity: Medium

Files:

- `apps/caresight-hub/models/`
- `apps/caresight-hub/scripts/caresight_install_models.py`
- `docs/operations/local_model_operations.md`

Evidence:

- Model artifacts are intentionally ignored.
- The roadmap mentions local model candidates, but the fast gate does not verify model checksums, license terms, or expected path layout.

Why it matters:

Local-first does not remove supply-chain risk. Model swaps can change behavior and licensing posture.

Recommended remediation:

- Add model manifests with source URL, license, checksum, expected size, intended purpose lane, and validation command.
- Add a non-downloading `model doctor` command.

Validation:

- `care_console.py model-doctor` or a script should fail when a model path exists but hash/license metadata is missing.

### F016 - `ensure_column()` uses f-strings for identifiers

Severity: Low

File:

- `apps/caresight-hub/caresight/storage/sqlite_store.py`

Evidence:

- `ensure_column()` builds `PRAGMA table_info({table})` and `ALTER TABLE {table} ADD COLUMN {column} {definition}` using f-strings.

Why it matters:

Current callers pass hard-coded identifiers, so this is not an active injection issue. But it is a risky helper shape in a canonical store.

Recommended remediation:

- Restrict table/column names to a hard-coded allowlist or validate with a strict identifier regex.

Validation:

- Unit test invalid identifier rejection.

### F017 - Review state changes allow repeat confirmations/dismissals without lifecycle transition checks

Severity: Medium

File:

- `apps/caresight-hub/caresight/storage/sqlite_store.py`

Evidence:

- `record_event_review()` updates `events.status` to the requested decision after loading the event.
- It does not appear to reject reviewing an already final event.

Why it matters:

For an auditable blackbox, repeated review actions should be explicit amendments or follow-up notes, not silent state flips.

Recommended remediation:

- Add lifecycle transition validation from `contracts/lifecycle.md`.
- Support `amend_review` or `needs_followup` as separate audit actions.

Validation:

- Tests should reject `human_confirmed -> dismissed` unless an explicit amendment command is used.

### F018 - Journal text includes reviewer free text without redaction or export classification

Severity: Low

File:

- `apps/caresight-hub/caresight/storage/sqlite_store.py`

Evidence:

- `review_journal_body()` appends reviewer note directly.

Why it matters:

Local journal entries may later be exported or summarized. Reviewer notes can contain names, phone numbers, diagnoses, or sensitive family context.

Recommended remediation:

- Add journal export classifications: local-only, caregiver-shareable, clinical-review, do-not-share.
- Add optional redaction before external summaries.

Validation:

- Tests for export modes and blocked external share of local-only notes.

### F019 - Contract count is strong, but live operational contracts are incomplete

Severity: Medium

Evidence:

- Contract validation passes for 15 schemas.
- Current live paths still need contracts for media sharing, reply-gated action continuation, MJPEG feed exposure, model manifest, retention policy, and runtime gate receipts.

Why it matters:

The codebase's best safety property is contract-first governance. The newest live/demo surfaces have outgrown the initial schemas.

Recommended remediation:

Add schemas:

- `media-sharing-policy`
- `runtime-validation-receipt`
- `model-manifest`
- `retention-policy`
- `reply-gated-handoff`
- `local-feed-exposure`

Validation:

- Valid and invalid examples for each.
- Runtime commands should emit these shapes where practical.

### F020 - Current docs are honest but very large, and operational next steps are hard to prioritize

Severity: Low

Files:

- `docs/cli/COMMANDS.md`
- `docs/roadmaps/CURRENT_STATE_AND_NEXT.md`
- `CHANGELOG.md`

Evidence:

- `docs/cli/COMMANDS.md` is 1,342 lines.
- `CURRENT_STATE_AND_NEXT.md` is 394 lines.
- `CHANGELOG.md` is long and contains many fine-grained implementation notes.

Why it matters:

The repo is auditable, but a new contributor or grant reviewer may struggle to find the current proof state and next gate.

Recommended remediation:

- Add a short `docs/status/OPERATING_STATUS.md`.
- Split command docs into categories with generated index.
- Keep detailed changelog, but add a short release-note layer.

Validation:

- New operator can find the current run command, current blocker, and current evidence in under two minutes.

## Positive Findings

- The core quality gate passes.
- The contract corpus includes valid and invalid examples for important claim boundaries.
- The architecture repeatedly separates contracts, TypeScript governance, Python runtime, presentation, and audit planes.
- The code uses parameterized SQL for most runtime data values.
- The local-first posture is present in code, docs, and examples.
- Automation reviewer names are blocked for review lifecycle mutations.
- The live command requires `--live-approved` for non-dry-run iMessage and FaceTime actions.
- The current event language remains mostly bounded: `possible_floor_stay`, `missing_off_camera_extended`, and `*_likely_observed`.

## Recommended Fix Order

1. Fix live target allowlist bypass.
2. Add pre-execution audit rows for live actions.
3. Add media-sharing policy before attaching snapshots to outbound messages.
4. Split `v0_floor_stay_live.py` around clear runtime boundaries.
5. Split `sqlite_store.py` around durable table ownership.
6. Rename tracked `v0.local.json` to a tracked example/demo config and regenerate ignored local config.
7. Add contracts for runtime receipts, media attachments, model manifests, retention, reply-gated handoff, and local feed exposure.
8. Add real-runtime validation ladders for camera, OBS, Gemma, Hermes, iMessage, FaceTime, and TTS.

## Evidence Commands

```bash
git status --short
git ls-files 'apps/caresight-hub/config/*.local.json' 'apps/caresight-hub/config/hermes/*.local.json' 'apps/caresight-hub/config/v0.local.json' 'apps/caresight-hub/models/**' 'apps/caresight-hub/.venv/**' 'apps/caresight-hub/data/**'
git ls-files '*.py' '*.ts' '*.js' '*.sh' '*.md' '*.json' '*.html' '*.css' | xargs wc -l | sort -n | tail -50
npm run check
```

## Non-Findings

- No failing deterministic test was observed.
- No committed model weights were found through `git ls-files`.
- No committed `.venv` or runtime SQLite data was found through `git ls-files`.
- No autonomous emergency-dispatch implementation was found.
- No HIPAA compliance claim was found in current top-level product framing.
