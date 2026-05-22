# Sprint 01/02 Production Validation Checklist

This document is the production-readiness checklist for Sprint 01 demo surfaces and Sprint 02 agent/Hermes escalation behavior. It is not an implementation-complete claim. As the agent proceeds through this checklist, mark completed items with `✅`, leave incomplete items as `❌`, and add a link to the proof artifact or the exact human validation command prompt where human judgment is required.

Proof of function and/or human validation command is sufficient unless a task specifically asks the human to inspect wording, visual output, contact routing, audio playback, or live external action behavior.

## Seeded-Real A/B Validation Set

Use seeded-real data before staging another live test:

- Case A: concerning seeded-real event from the accepted live floor-stay proof.
- Case B: non-concerning seeded-real desk/normal-presence event captured or seeded while the operator is working normally.

The A/B set should let Sprint 01 and Sprint 02 prove both escalation and non-escalation behavior before any new live Hermes/iMessage/FaceTime/TTS operation is attempted.

---

## Seeded-Real Case A: Status ✅

- Description: Accepted live proof event for a concerning possible floor-stay scenario. This is the known positive/concerning seeded-real case.
- Required files for reference when working on this:
  - `docs/audits/2026-05-20-t041-final-live-proof.md`
  - `docs/audits/2026-05-20-sprint-01-demo-surface.md`
  - `apps/caresight-hub/data/caresight-v0.sqlite3`
  - `apps/caresight-hub/data/snapshots/evt_d9aa38bdc636459c92ea4e25f665cd0d.jpg`
  - `apps/caresight-hub/scripts/care_console.py`
- Proof of completion:
  - `docs/audits/2026-05-20-t041-final-live-proof.md`
  - Event ID: `evt_d9aa38bdc636459c92ea4e25f665cd0d`
- Human validation command as needed:
  - Ask: "Please confirm this remains the accepted concerning seeded-real event for production validation case A."

---

## Seeded-Real Case B: Status ✅

- Description: Create or capture a non-concerning seeded-real event while the operator is sitting at the desk or otherwise visibly normal. The expected outcome is no urgent escalation and no emergency-contact handoff recommendation.
- Required files for reference when working on this:
  - `apps/caresight-hub/scripts/v0_floor_stay_live.py`
  - `apps/caresight-hub/scripts/v0_review_events.py`
  - `apps/caresight-hub/scripts/live_proof_audit.py`
  - `apps/caresight-hub/config/v0.local.json`
  - `apps/caresight-hub/data/caresight-v0.sqlite3`
  - `docs/cli/COMMANDS.md`
- Proof of completion:
  - No-event proof: `docs/audits/production-validation/sprint-01/case-b-normal-desk-no-event.md`
  - Machine-readable no-event receipt: `docs/audits/production-validation/sprint-01/case-b-normal-desk-no-event.json`
  - Follow-up implementation: future no-event checks now persist to SQLite `observation_checks` rows with a `check_id`.
  - Operator output: `no_event_persisted {"camera_id": "living_room", "elapsed_seconds": 60.0, "frame_count": 1800, "required_dwell_seconds": 8.0, "status": "no_possible_floor_stay_event", "zone_id": "floor_zone"}`
  - Blocked capture attempt: `docs/audits/production-validation/sprint-01/case-b-normal-desk-capture-attempt.md`
  - False-positive attempt: `docs/audits/production-validation/sprint-01/case-b-normal-desk-false-positive.md`
  - Current result: after the seated-desk false-positive fix, the normal desk rerun produced no `possible_floor_stay` event across 60 seconds / 1800 frames.
- Human validation command as needed:
  - Ask: "Please perform a normal desk/non-concerning posture test after the heuristic/output fix, then provide the resulting `no_event_persisted` line or event ID."

---

# Sprint 01 Production Validation

## Sprint Item: Generate Review Packet For Case A: Status ✅

- Description: Generate a `human-review-packet` for the accepted concerning seeded-real event and store the output as an audit artifact.
- Required files for reference when working on this:
  - `contracts/schemas/human-review-packet.schema.json`
  - `contracts/examples/valid/human-review-packet.possible-floor-stay.json`
  - `apps/caresight-hub/caresight/runtime/demo_surface/review_packet.py`
  - `apps/caresight-hub/scripts/care_console.py`
  - `docs/cli/COMMANDS.md`
- Proof of completion:
  - Artifact: `docs/audits/production-validation/sprint-01/case-a-review-packet.json`
  - Human-readable artifact: `docs/audits/production-validation/sprint-01/case-a-review-packet.md`
  - Generated with: `python3 apps/caresight-hub/scripts/care_console.py review-packet evt_d9aa38bdc636459c92ea4e25f665cd0d --format json --output docs/audits/production-validation/sprint-01/case-a-review-packet.json`
  - Human-facing output generated with: `python3 apps/caresight-hub/scripts/care_console.py review-packet evt_d9aa38bdc636459c92ea4e25f665cd0d --format markdown --output docs/audits/production-validation/sprint-01/case-a-review-packet.md`
  - Preserves: `event_id`, `snapshot_path`, `status`, latest reviewer, review count, SQLite provenance, available human actions, and blocked `autonomous_emergency_dispatch` / `medical_diagnosis` actions.
- Human validation command as needed:
  - `python3 apps/caresight-hub/scripts/care_console.py review-packet evt_d9aa38bdc636459c92ea4e25f665cd0d --format markdown`
  - Ask: "Is this review packet understandable, caregiver-ready, and free of medical/emergency overclaims?"

---

## Sprint Item: Generate Blackbox Receipt For Case A: Status ✅

- Description: Generate a `blackbox-receipt` for the accepted concerning seeded-real event and confirm it preserves observation, review, journal, handoff, dashboard, and alert provenance.
- Required files for reference when working on this:
  - `contracts/schemas/blackbox-receipt.schema.json`
  - `contracts/examples/valid/blackbox-receipt.possible-floor-stay.json`
  - `apps/caresight-hub/caresight/runtime/demo_surface/blackbox_receipt.py`
  - `apps/caresight-hub/scripts/care_console.py`
  - `docs/audits/2026-05-20-t041-final-live-proof.md`
- Proof of completion:
  - Artifact: `docs/audits/production-validation/sprint-01/case-a-blackbox-receipt.json`
  - Human-readable artifact: `docs/audits/production-validation/sprint-01/case-a-blackbox-receipt.md`
  - Generated with: `python3 apps/caresight-hub/scripts/care_console.py blackbox-receipt evt_d9aa38bdc636459c92ea4e25f665cd0d --format json --output docs/audits/production-validation/sprint-01/case-a-blackbox-receipt.json`
  - Human-facing output generated with: `python3 apps/caresight-hub/scripts/care_console.py blackbox-receipt evt_d9aa38bdc636459c92ea4e25f665cd0d --format markdown --output docs/audits/production-validation/sprint-01/case-a-blackbox-receipt.md`
  - Preserves: observation/review/journal/handoff counts, reviewer, review timestamp, event timestamp, local source-of-truth, dashboard/alert derived-output checks, track IDs, and safety boundaries.
- Human validation command as needed:
  - `python3 apps/caresight-hub/scripts/care_console.py blackbox-receipt evt_d9aa38bdc636459c92ea4e25f665cd0d --format markdown`
  - Ask: "Does this receipt give enough proof to trust what happened without implying autonomous dispatch or medical certainty?"

---

## Sprint Item: Generate Review Packet For Case B: Status ✅

- Description: Generate a `human-review-packet` for the non-concerning seeded-real event and verify it does not produce urgent escalation language.
- Required files for reference when working on this:
  - `contracts/schemas/human-review-packet.schema.json`
  - `apps/caresight-hub/caresight/runtime/demo_surface/review_packet.py`
  - `apps/caresight-hub/scripts/care_console.py`
  - Case B event/audit artifact from this checklist.
- Proof of completion:
  - Not applicable because Case B is a valid no-event proof with no `event_id`.
  - Substitute proof: `docs/audits/production-validation/sprint-01/case-b-normal-desk-no-event.md`
  - Machine-readable receipt: `docs/audits/production-validation/sprint-01/case-b-normal-desk-no-event.json`
  - Persistence boundary: normal/no-event checks are retained as SQLite `observation_checks`, not event review packets.
- Human validation command as needed:
  - `python3 apps/caresight-hub/scripts/care_console.py review-packet <case_b_event_id> --format markdown`
  - Ask: "Does this normal/non-concerning packet avoid concern escalation and still preserve useful audit context?"

---

## Sprint Item: Generate Blackbox Receipt For Case B: Status ✅

- Description: Generate a `blackbox-receipt` for the non-concerning seeded-real event and verify it reports the correct non-urgent status and provenance.
- Required files for reference when working on this:
  - `contracts/schemas/blackbox-receipt.schema.json`
  - `apps/caresight-hub/caresight/runtime/demo_surface/blackbox_receipt.py`
  - `apps/caresight-hub/scripts/care_console.py`
  - Case B event/audit artifact from this checklist.
- Proof of completion:
  - Not applicable because Case B is a valid no-event proof with no SQLite event chain.
  - Substitute proof: `docs/audits/production-validation/sprint-01/case-b-normal-desk-no-event.md`
  - Machine-readable receipt: `docs/audits/production-validation/sprint-01/case-b-normal-desk-no-event.json`
  - Persistence boundary: normal/no-event checks are retained as SQLite `observation_checks`, not blackbox receipts for event chains.
- Human validation command as needed:
  - `python3 apps/caresight-hub/scripts/care_console.py blackbox-receipt <case_b_event_id> --format markdown`
  - Ask: "Does this normal/non-concerning receipt show the right evidence without making the event look urgent?"

---

## Sprint Item: Sprint 01 A/B Human Acceptance: Status ✅

- Description: Human validates that Case A and Case B surfaces are distinguishable, understandable, bounded, and ready for operator/demo use.
- Required files for reference when working on this:
  - `docs/audits/production-validation/sprint-01/case-a-review-packet.json`
  - `docs/audits/production-validation/sprint-01/case-a-blackbox-receipt.json`
  - `docs/audits/production-validation/sprint-01/case-b-review-packet.json`
  - `docs/audits/production-validation/sprint-01/case-b-blackbox-receipt.json`
  - `docs/project/PROJECT_BRIEF.md`
  - `docs/architecture/bounded_control_loop.md`
- Proof of completion:
  - `docs/audits/production-validation/sprint-01/human-acceptance.md`
  - Case A human-readable acceptance recorded at `docs/audits/production-validation/sprint-01/case-a-human-readable-acceptance.md`; this accepts the Markdown direction as actionable-ready for audit receipts, while noting that evidence labels need human translation and Gemma should later produce a more succinct outbound alert.
  - User clarified on 2026-05-21 that the A/B outputs were already worked through together for accuracy and human readability, so this acceptance is carried forward for Sprint 01 A/B validation.
- Human validation command as needed:
  - Ask: "Approve Sprint 01 production validation for A/B seeded-real events, or list exact wording/provenance changes needed."

---

# Sprint 02 Product Requirements

## Sprint Item: Local Gemma Endpoint Requirement: Status ✅

- Description: Gemma must be served locally through an OpenAI-compatible endpoint and reachable at the configured Hermes base URL.
- Required files for reference when working on this:
  - `apps/caresight-hub/config/hermes/config.caresight.local.yaml`
  - `apps/caresight-hub/config/hermes/model-routes.json`
  - `apps/caresight-hub/models/reasoning/gemma/`
  - `docs/audits/2026-05-21-sprint-02-agent-model-surface.md`
  - `docs/references/gemma.md`
- Proof of completion:
  - Target artifact: `docs/audits/production-validation/sprint-02/gemma-local-endpoint.json`
  - Current artifact: `docs/audits/production-validation/sprint-02/gemma-local-endpoint.json`
  - Current result: the existing local `gemma-4-e2b-it-4bit` MLX model was served through `mlx-vlm.server` at `http://127.0.0.1:8080/v1`; `/v1/chat/completions` returned a bounded CareSight alert with no cloud fallback and about 3.77 GB peak memory on the smoke request. `mlx_lm.server` remains incompatible with these local Gemma 4 packages, so `mlx-vlm.server` is the selected local runner.
- Human validation command as needed:
  - Not required unless endpoint startup needs operator approval.

---

## Sprint Item: Real Gemma Draft Requirement: Status ✅

- Description: Replace or supplement the fake provider with a real local Gemma provider path that drafts from SQLite-derived audit context only.
- Required files for reference when working on this:
  - `apps/caresight-hub/caresight/runtime/agent_assist/service.py`
  - `apps/caresight-hub/caresight/runtime/agent_assist/harness.py`
  - `contracts/schemas/agent-draft.schema.json`
  - `contracts/schemas/forbidden-claim-vocabulary.schema.json`
  - `docs/roadmaps/caresight_sprint_pack/02-sprint-agent-llm-drafting-layer.md`
- Proof of completion:
  - `docs/audits/production-validation/sprint-02/case-a-gemma-draft.json`
  - `docs/audits/production-validation/sprint-02/case-b-gemma-non-escalation.json`
  - Current result: `care_console.py agent-draft --provider gemma` persisted a validated `provider: gemma_mlx` Case A draft from SQLite-derived audit context only. Case B remained a no-event continuity check and correctly did not create a Gemma caregiver alert or urgent handoff.
- Human validation command as needed:
  - Ask after drafts are generated through the selected `mlx-vlm` local endpoint: "Are these Gemma-generated drafts caregiver-ready, bounded, and meaningfully different for concerning vs non-concerning cases?"

---

## Sprint Item: Hermes Invocation Requirement: Status ✅

- Description: CareSight must invoke Hermes with the staged payload boundary instead of only rendering a local JSON payload.
- Required files for reference when working on this:
  - `apps/caresight-hub/vendor/hermes-agent`
  - `apps/caresight-hub/config/hermes/`
  - `apps/caresight-hub/caresight/runtime/agent_assist/harness.py`
  - `docs/references/hermes.md`
  - `docs/audits/2026-05-21-agent-harness-review.md`
- Proof of completion:
  - `docs/audits/production-validation/sprint-02/hermes-invocation-dry-run.json`
  - Current result: CareSight invoked the vendored Hermes no-send `send_message(action='list')` preflight through `care_console.py hermes-dry-run` using the project-local YOLO MLX venv, persisted an execution-attempt row, and redacted the raw target directory from the receipt.
- Human validation command as needed:
  - Not required for dry-run invocation; required before any external send/call/write.

---

## Sprint Item: Allowlisted Contact Requirement: Status ✅

- Description: Configure real caregiver and emergency-contact records outside Git-tracked secrets, then prove staged iMessage/FaceTime requests cannot target unallowlisted contacts.
- Required files for reference when working on this:
  - `contracts/schemas/agent-action-request.schema.json`
  - `contracts/examples/invalid/agent-action-request-missing-allowlist.json`
  - `apps/caresight-hub/config/hermes/env.caresight.example`
  - `apps/caresight-hub/caresight/runtime/agent_assist/service.py`
  - `docs/architecture/REPO_BOUNDARIES.md`
- Proof of completion:
  - `docs/audits/production-validation/sprint-02/allowlisted-contacts-redacted.json`
  - `apps/caresight-hub/config/hermes/allowlisted-contacts.example.json`
  - `apps/caresight-hub/config/hermes/env.caresight.example`
  - `apps/caresight-hub/caresight/runtime/agent_assist/contacts.py`
  - `apps/caresight-hub/caresight/runtime/agent_assist/service.py`
- Human validation command as needed:
  - Ask: "Please confirm which contact IDs are allowed for caregiver and emergency-contact testing. Do not provide secrets in Git-tracked files."

---

## Sprint Item: Execution Attempt Logging Requirement: Status ✅

- Description: Every real or dry-run external action attempt must be written to SQLite with request ID, target, execution state, timestamp, result, and error if any.
- Required files for reference when working on this:
  - `apps/caresight-hub/caresight/storage/migrations/001_init.sql`
  - `apps/caresight-hub/caresight/storage/sqlite_store.py`
  - `contracts/schemas/agent-action-request.schema.json`
  - `docs/architecture/bounded_control_loop.md`
- Proof of completion:
  - `docs/audits/production-validation/sprint-02/execution-attempt-logging.json`
  - `apps/caresight-hub/caresight/storage/migrations/001_init.sql`
  - `apps/caresight-hub/caresight/storage/sqlite_store.py`
  - `apps/caresight-hub/caresight/runtime/agent_assist/harness.py`
  - `apps/caresight-hub/scripts/care_console.py`
- Human validation command as needed:
  - Not required for dry-run logging.

---

## Sprint Item: Screen Capture Or OBS Requirement: Status ⚠️ Scene Setup Pending

- Description: Configure and validate either a local screen-capture artifact path or OBS virtual camera path before offering visual handoff options.
- Required files for reference when working on this:
  - `docs/architecture/obs_facetime_live_view.md`
  - `docs/references/apple_shortcuts_facetime_notes.md`
  - `apps/caresight-hub/caresight/runtime/agent_assist/harness.py`
  - `docs/cli/COMMANDS.md`
- Proof of completion:
  - `docs/audits/production-validation/sprint-02/screen-capture-obs-readiness.json`
  - `apps/obs-hub/README.md`
  - `apps/obs-hub/tools/setup_obs_scenes.py`
  - `scripts/setup_obs_scene.sh`
  - `apps/obs-hub/tools/update_obs_event.py`
  - `scripts/update_obs_overlay.sh`
  - Current result: OBS is installed, `obsws_python` is importable in `apps/caresight-hub/.venv`, scenes were created, event IDs are shortened in the caregiver-facing panel, and dynamic overlay-state update/watch scripts now exist. Remaining work is operator validation that `current_event.js` updates the scene with real event/recent-activity context and that no private content appears before any capture, virtual camera, or FaceTime handoff proof.
- Human validation command as needed:
  - Ask: "Please confirm the screen capture or OBS virtual camera output displays the intended camera feed and does not show unrelated private desktop content."

---

## Sprint Item: FaceTime Handoff Requirement: Status ⚠️ Approved, Setup Pending

- Description: Configure FaceTime handoff as a human-approved action. It must not auto-call. It must either prepare the call instructions or wait for explicit approval before launching.
- Required files for reference when working on this:
  - `docs/architecture/obs_facetime_live_view.md`
  - `docs/references/apple_shortcuts_facetime_notes.md`
  - `apps/caresight-hub/caresight/runtime/agent_assist/harness.py`
  - `contracts/schemas/agent-action-request.schema.json`
- Proof of completion:
  - `docs/audits/production-validation/sprint-02/facetime-tts-approval-blocked.json`
  - `docs/audits/production-validation/sprint-02/human-validation-feedback-2026-05-21.md`
  - Current result: user approved FaceTime handoff preparation and approved `contact_emergency_primary` for FaceTime testing, but no FaceTime call was started. Remaining work is privacy-safe OBS/visual setup execution and explicit approval for one live handoff test.
- Human validation command as needed:
  - Ask before live action: "Approve one allowlisted FaceTime handoff test, or keep this at prepared-instructions only."

---

## Sprint Item: Local TTS Requirement: Status ⚠️ Playback Validation Pending

- Description: Generate and play local TTS from a validated `tts-utterance`, using Holler or selected local TTS model, without voice cloning or emergency certainty.
- Required files for reference when working on this:
  - `contracts/schemas/tts-utterance.schema.json`
  - `contracts/examples/valid/tts-utterance.possible-floor-stay.json`
  - `apps/caresight-hub/models/tts/holler/`
  - `docs/audits/2026-05-21-sprint-02-agent-model-surface.md`
- Proof of completion:
  - `docs/audits/production-validation/sprint-02/facetime-tts-approval-blocked.json`
  - `docs/audits/production-validation/sprint-02/human-validation-feedback-2026-05-21.md`
  - Current result: runtime dependencies are installed in `apps/caresight-hub/.venv`, `mlx_audio.tts.generate` produced a local WAV, the operator confirmed playback functionally works and sounds clean, and Dakota voice is approved for the shorter alert wording.
- Human validation command as needed:
  - Ask: "Please confirm the TTS message is audible, calm, understandable, and does not imply medical or emergency certainty."

---

# Sprint 02 Production Validation Checklist

## Sprint Item: Case A Agent Draft And Validation: Status ✅

- Description: Run a real local Gemma draft for the concerning seeded-real event, validate forbidden claims, and persist the validated/blocked result in SQLite.
- Required files for reference when working on this:
  - `apps/caresight-hub/scripts/care_console.py`
  - `apps/caresight-hub/caresight/runtime/agent_assist/service.py`
  - `contracts/schemas/agent-draft.schema.json`
  - `contracts/schemas/forbidden-claim-vocabulary.schema.json`
  - Case A event artifact.
- Proof of completion:
  - `docs/audits/production-validation/sprint-02/case-a-agent-draft.json`
  - `docs/audits/production-validation/sprint-02/case-a-gemma-draft.json`
  - `docs/audits/production-validation/sprint-02/human-validation-feedback-2026-05-21.md`
  - Current result: persisted a validated Gemma MLX draft from the SQLite audit chain through the local `mlx-vlm` endpoint. The draft says: "Possible floor stay observed in the Living Room. Needs review."
  - Human result: wording approved, with a follow-up request to add time relevance, unresolved-alert cadence, and resolution-update support.
  - Automation path: `v0_floor_stay_live.py --auto-agent-dry-run` now wires event persistence to OBS overlay update, Gemma draft, staged iMessage request, and Hermes no-send preflight.
- Human validation command as needed:
  - Ask: "Does the concerning-event draft communicate urgency without saying fall, injury, medical emergency, or dispatch?"

---

## Sprint Item: Case B Agent Draft And Validation: Status ✅

- Description: Run a real local Gemma draft for the non-concerning seeded-real event, validate forbidden claims, and persist the validated/blocked result in SQLite.
- Required files for reference when working on this:
  - `apps/caresight-hub/scripts/care_console.py`
  - `apps/caresight-hub/caresight/runtime/agent_assist/service.py`
  - `contracts/schemas/agent-draft.schema.json`
  - Case B event/audit artifact.
- Proof of completion:
  - `docs/audits/production-validation/sprint-02/case-b-agent-draft.json`
  - `docs/audits/production-validation/sprint-02/case-b-gemma-non-escalation.json`
  - Current result: not applicable because Case B is a persisted normal/no-event observation check, not a care event. The Gemma non-escalation receipt confirms no Gemma alert, urgent action request, or Hermes invocation was created for Case B.
- Human validation command as needed:
  - Ask: "Does the non-concerning draft avoid unnecessary escalation while remaining useful?"

---

## Sprint Item: Case A Urgent Handoff Staging: Status ✅

- Description: Stage an urgent handoff for the concerning case with an allowlisted emergency contact and response options for text update, screen capture, and FaceTime handoff.
- Required files for reference when working on this:
  - `contracts/schemas/agent-action-request.schema.json`
  - `contracts/examples/valid/agent-action-request.urgent-handoff.json`
  - `apps/caresight-hub/scripts/care_console.py`
  - `apps/caresight-hub/caresight/runtime/agent_assist/harness.py`
- Proof of completion:
  - `docs/audits/production-validation/sprint-02/case-a-urgent-action-request.json`
  - `docs/audits/production-validation/sprint-02/case-a-hermes-handoff-payload.json`
  - `docs/audits/production-validation/sprint-02/case-a-gemma-urgent-action-request.json`
  - `docs/audits/production-validation/sprint-02/case-a-gemma-hermes-handoff-payload.json`
- Human validation command as needed:
  - `python3 apps/caresight-hub/scripts/care_console.py hermes-handoff-payload <case_a_request_id>`
  - Ask: "Does this staged urgent handoff ask for direction and offer screen capture or FaceTime handoff without initiating either?"

---

## Sprint Item: Case B Non-Urgent Staging: Status ✅

- Description: Stage a non-urgent caregiver update for the non-concerning case. It must not target emergency contacts or offer FaceTime unless a human explicitly asks.
- Required files for reference when working on this:
  - `contracts/schemas/agent-action-request.schema.json`
  - `apps/caresight-hub/scripts/care_console.py`
  - `apps/caresight-hub/caresight/runtime/agent_assist/service.py`
  - Case B event/audit artifact.
- Proof of completion:
  - `docs/audits/production-validation/sprint-02/case-b-nonurgent-action-request.json`
  - Current result: not applicable because no event-backed action request should be staged for a normal/no-event check.
- Human validation command as needed:
  - Ask: "Does the normal-case staged update stay non-urgent and avoid emergency-contact routing?"

---

## Sprint Item: Hermes Dry-Run Invocation On Case A: Status ✅

- Description: Invoke Hermes with the Case A staged urgent payload in dry-run or no-send mode and capture the local output.
- Required files for reference when working on this:
  - `apps/caresight-hub/vendor/hermes-agent`
  - `apps/caresight-hub/config/hermes/config.caresight.local.yaml`
  - `apps/caresight-hub/config/hermes/env.caresight.example`
  - `docs/references/hermes.md`
- Proof of completion:
  - `docs/audits/production-validation/sprint-02/case-a-hermes-dry-run.json`
  - `docs/audits/production-validation/sprint-02/case-a-gemma-hermes-dry-run.json`
  - Current result: execution attempt was persisted with `external_action_performed: false`; Hermes no-send preflight returned ready and raw target names were redacted from the receipt.
- Human validation command as needed:
  - Not required unless Hermes prompts for local credentials or operator setup.

---

## Sprint Item: Hermes Dry-Run Invocation On Case B: Status ✅

- Description: Invoke Hermes with the Case B non-urgent staged payload in dry-run or no-send mode and capture the local output.
- Required files for reference when working on this:
  - `apps/caresight-hub/vendor/hermes-agent`
  - `apps/caresight-hub/config/hermes/config.caresight.local.yaml`
  - `docs/references/hermes.md`
- Proof of completion:
  - `docs/audits/production-validation/sprint-02/case-b-hermes-dry-run.json`
  - Current result: not applicable because Hermes should remain downstream of a staged action request, and Case B created none.
- Human validation command as needed:
  - Not required unless Hermes prompts for local credentials or operator setup.

---

## Sprint Item: Human-Approved iMessage Test: Status ❌

- Description: After dry-run passes, perform one human-approved allowlisted iMessage send. This is the first external messaging proof and must be recorded.
- Required files for reference when working on this:
  - `apps/caresight-hub/config/hermes/env.caresight.example`
  - `docs/references/hermes.md`
  - `docs/cli/COMMANDS.md`
  - `docs/audits/production-validation/sprint-02/case-a-hermes-dry-run.json`
- Proof of completion:
  - Target artifact: `docs/audits/production-validation/sprint-02/human-approved-imessage-send.md`
  - Current result: `contact_emergency_primary` is approved for one iMessage test, and the text is approved: "CareSight alert. Possible floor stay observed in the Living Room. Needs review." The live send has not been executed.
- Human validation command as needed:
  - Ask: "Approve sending one test iMessage to the allowlisted contact. Confirm receipt and whether the text is acceptable."

---

## Sprint Item: Human-Approved Visual Handoff Test: Status ⚠️ Scene Setup Pending

- Description: Validate either screen capture by request or FaceTime handoff by request after human approval. No automatic call or raw-video send.
- Required files for reference when working on this:
  - `docs/architecture/obs_facetime_live_view.md`
  - `docs/references/apple_shortcuts_facetime_notes.md`
  - `docs/audits/production-validation/sprint-02/screen-capture-or-obs.md`
  - `docs/audits/production-validation/sprint-02/facetime-handoff.md`
- Proof of completion:
  - `docs/audits/production-validation/sprint-02/facetime-tts-execution-blocked.json`
  - `docs/audits/production-validation/sprint-02/human-validation-feedback-2026-05-21.md`
  - Current result: user approved the FaceTime handoff direction and the OBS browser-overlay scene architecture, and scenes were created. FaceTime handoff is intentionally held until OBS dynamic overlay updates are validated.
- Human validation command as needed:
  - Ask: "Approve one visual handoff test. Confirm that only the intended camera feed/screen capture is shown."

---

## Sprint Item: Human-Validated TTS Playback: Status ✅

- Description: Play a validated local TTS message for Case A or Case B and have the human confirm the audio quality and wording.
- Required files for reference when working on this:
  - `contracts/schemas/tts-utterance.schema.json`
  - `apps/caresight-hub/models/tts/holler/`
  - `docs/audits/production-validation/sprint-02/tts-playback.md`
- Proof of completion:
  - `docs/audits/production-validation/sprint-02/facetime-tts-execution-blocked.json`
  - `docs/audits/production-validation/sprint-02/case-a-gemma-tts-generated.json`
  - `docs/audits/production-validation/sprint-02/human-validation-feedback-2026-05-21.md`
  - Current result: TTS generation succeeded locally from the Gemma Case A message and produced an ignored local WAV. Operator confirmed audio playback functionally works and sounds clean, then approved the `dakota` voice for the shorter wording.
- Human validation command as needed:
  - Ask: "Confirm the TTS playback was audible, calm, and did not overclaim."

---

## Sprint Item: Sprint 02 Production Acceptance: Status ❌

- Description: Confirm Sprint 02 is production-ready only after local Gemma, Hermes invocation, allowlisted contact routing, dry-run payloads, one human-approved iMessage, visual handoff, TTS playback, and SQLite execution logging all pass.
- Required files for reference when working on this:
  - All artifacts under `docs/audits/production-validation/sprint-02/`
  - `docs/audits/production-validation/sprint-01/human-acceptance.md`
  - `CHANGELOG.md`
  - `DECISIONS.md`
  - `docs/roadmaps/CURRENT_STATE_AND_NEXT.md`
- Proof of completion:
  - `docs/audits/production-validation/sprint-02/production-acceptance.md`
  - Current result: local no-send Sprint 02 operation is validated, Gemma wording is approved, Dakota TTS is approved, and contact mapping/text are approved for `contact_emergency_primary`. Production acceptance remains blocked on dynamic OBS overlay validation, visual privacy confirmation, and live iMessage/FaceTime tests if they remain in scope.
- Human validation command as needed:
  - Ask: "Approve Sprint 02 as production-ready for the current local prototype scope, or list exact remaining blockers."

---

# Pre-Live-Test Gate

## Sprint Item: Seeded-Real A/B Gate Before New Live Test: Status ⚠️ Local No-Send Passed

- Description: Do not stage another live test until seeded-real Case A and Case B pass Sprint 01 and Sprint 02 validation. The seeded-real gate should prove behavior on both concerning and non-concerning cases.
- Required files for reference when working on this:
  - This checklist.
  - `docs/audits/production-validation/sprint-01/`
  - `docs/audits/production-validation/sprint-02/`
  - `docs/audits/2026-05-20-t041-final-live-proof.md`
- Proof of completion:
  - `docs/audits/production-validation/sprint-01-02-seeded-real-gate.md`
  - Current result: seeded-real local no-send A/B proof passed. The next gate is human approval before live iMessage, FaceTime, visual capture, or TTS playback.
- Human validation command as needed:
  - Ask: "Approve moving from seeded-real A/B validation to a staged live test."
