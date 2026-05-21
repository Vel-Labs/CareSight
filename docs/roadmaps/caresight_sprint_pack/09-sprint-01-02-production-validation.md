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

## Seeded-Real Case B: Status ❌

- Description: Create or capture a non-concerning seeded-real event while the operator is sitting at the desk or otherwise visibly normal. The expected outcome is no urgent escalation and no emergency-contact handoff recommendation.
- Required files for reference when working on this:
  - `apps/caresight-hub/scripts/v0_floor_stay_live.py`
  - `apps/caresight-hub/scripts/v0_review_events.py`
  - `apps/caresight-hub/scripts/live_proof_audit.py`
  - `apps/caresight-hub/config/v0.local.json`
  - `apps/caresight-hub/data/caresight-v0.sqlite3`
  - `docs/cli/COMMANDS.md`
- Proof of completion:
  - Add event ID, snapshot path if present, audit output, and any generated Sprint 01/Sprint 02 artifacts here.
- Human validation command as needed:
  - Ask: "Please perform a normal desk/non-concerning posture test, then provide the resulting event ID or confirm that no event should be created."

---

# Sprint 01 Production Validation

## Sprint Item: Generate Review Packet For Case A: Status ❌

- Description: Generate a `human-review-packet` for the accepted concerning seeded-real event and store the output as an audit artifact.
- Required files for reference when working on this:
  - `contracts/schemas/human-review-packet.schema.json`
  - `contracts/examples/valid/human-review-packet.possible-floor-stay.json`
  - `apps/caresight-hub/caresight/runtime/demo_surface/review_packet.py`
  - `apps/caresight-hub/scripts/care_console.py`
  - `docs/cli/COMMANDS.md`
- Proof of completion:
  - Target artifact: `docs/audits/production-validation/sprint-01/case-a-review-packet.json`
- Human validation command as needed:
  - `python3 apps/caresight-hub/scripts/care_console.py review-packet evt_d9aa38bdc636459c92ea4e25f665cd0d --format markdown`
  - Ask: "Is this review packet understandable, caregiver-ready, and free of medical/emergency overclaims?"

---

## Sprint Item: Generate Blackbox Receipt For Case A: Status ❌

- Description: Generate a `blackbox-receipt` for the accepted concerning seeded-real event and confirm it preserves observation, review, journal, handoff, dashboard, and alert provenance.
- Required files for reference when working on this:
  - `contracts/schemas/blackbox-receipt.schema.json`
  - `contracts/examples/valid/blackbox-receipt.possible-floor-stay.json`
  - `apps/caresight-hub/caresight/runtime/demo_surface/blackbox_receipt.py`
  - `apps/caresight-hub/scripts/care_console.py`
  - `docs/audits/2026-05-20-t041-final-live-proof.md`
- Proof of completion:
  - Target artifact: `docs/audits/production-validation/sprint-01/case-a-blackbox-receipt.json`
- Human validation command as needed:
  - `python3 apps/caresight-hub/scripts/care_console.py blackbox-receipt evt_d9aa38bdc636459c92ea4e25f665cd0d --format markdown`
  - Ask: "Does this receipt give enough proof to trust what happened without implying autonomous dispatch or medical certainty?"

---

## Sprint Item: Generate Review Packet For Case B: Status ❌

- Description: Generate a `human-review-packet` for the non-concerning seeded-real event and verify it does not produce urgent escalation language.
- Required files for reference when working on this:
  - `contracts/schemas/human-review-packet.schema.json`
  - `apps/caresight-hub/caresight/runtime/demo_surface/review_packet.py`
  - `apps/caresight-hub/scripts/care_console.py`
  - Case B event/audit artifact from this checklist.
- Proof of completion:
  - Target artifact: `docs/audits/production-validation/sprint-01/case-b-review-packet.json`
- Human validation command as needed:
  - `python3 apps/caresight-hub/scripts/care_console.py review-packet <case_b_event_id> --format markdown`
  - Ask: "Does this normal/non-concerning packet avoid concern escalation and still preserve useful audit context?"

---

## Sprint Item: Generate Blackbox Receipt For Case B: Status ❌

- Description: Generate a `blackbox-receipt` for the non-concerning seeded-real event and verify it reports the correct non-urgent status and provenance.
- Required files for reference when working on this:
  - `contracts/schemas/blackbox-receipt.schema.json`
  - `apps/caresight-hub/caresight/runtime/demo_surface/blackbox_receipt.py`
  - `apps/caresight-hub/scripts/care_console.py`
  - Case B event/audit artifact from this checklist.
- Proof of completion:
  - Target artifact: `docs/audits/production-validation/sprint-01/case-b-blackbox-receipt.json`
- Human validation command as needed:
  - `python3 apps/caresight-hub/scripts/care_console.py blackbox-receipt <case_b_event_id> --format markdown`
  - Ask: "Does this normal/non-concerning receipt show the right evidence without making the event look urgent?"

---

## Sprint Item: Sprint 01 A/B Human Acceptance: Status ❌

- Description: Human validates that Case A and Case B surfaces are distinguishable, understandable, bounded, and ready for operator/demo use.
- Required files for reference when working on this:
  - `docs/audits/production-validation/sprint-01/case-a-review-packet.json`
  - `docs/audits/production-validation/sprint-01/case-a-blackbox-receipt.json`
  - `docs/audits/production-validation/sprint-01/case-b-review-packet.json`
  - `docs/audits/production-validation/sprint-01/case-b-blackbox-receipt.json`
  - `docs/project/PROJECT_BRIEF.md`
  - `docs/architecture/bounded_control_loop.md`
- Proof of completion:
  - Target artifact: `docs/audits/production-validation/sprint-01/human-acceptance.md`
- Human validation command as needed:
  - Ask: "Approve Sprint 01 production validation for A/B seeded-real events, or list exact wording/provenance changes needed."

---

# Sprint 02 Product Requirements

## Sprint Item: Local Gemma Endpoint Requirement: Status ❌

- Description: Gemma must be served locally through an OpenAI-compatible endpoint and reachable at the configured Hermes base URL.
- Required files for reference when working on this:
  - `apps/caresight-hub/config/hermes/config.caresight.local.yaml`
  - `apps/caresight-hub/config/hermes/model-routes.json`
  - `apps/caresight-hub/models/reasoning/gemma/`
  - `docs/audits/2026-05-21-sprint-02-agent-model-surface.md`
  - `docs/references/gemma.md`
- Proof of completion:
  - Target artifact: `docs/audits/production-validation/sprint-02/gemma-local-endpoint.json`
- Human validation command as needed:
  - Not required unless endpoint startup needs operator approval.

---

## Sprint Item: Real Gemma Draft Requirement: Status ❌

- Description: Replace or supplement the fake provider with a real local Gemma provider path that drafts from SQLite-derived audit context only.
- Required files for reference when working on this:
  - `apps/caresight-hub/caresight/runtime/agent_assist/service.py`
  - `apps/caresight-hub/caresight/runtime/agent_assist/harness.py`
  - `contracts/schemas/agent-draft.schema.json`
  - `contracts/schemas/forbidden-claim-vocabulary.schema.json`
  - `docs/roadmaps/caresight_sprint_pack/02-sprint-agent-llm-drafting-layer.md`
- Proof of completion:
  - Target artifact: `docs/audits/production-validation/sprint-02/gemma-draft-case-a.json`
  - Target artifact: `docs/audits/production-validation/sprint-02/gemma-draft-case-b.json`
- Human validation command as needed:
  - Ask after drafts are generated: "Are these Gemma-generated drafts caregiver-ready, bounded, and meaningfully different for concerning vs non-concerning cases?"

---

## Sprint Item: Hermes Invocation Requirement: Status ❌

- Description: CareSight must invoke Hermes with the staged payload boundary instead of only rendering a local JSON payload.
- Required files for reference when working on this:
  - `apps/caresight-hub/vendor/hermes-agent`
  - `apps/caresight-hub/config/hermes/`
  - `apps/caresight-hub/caresight/runtime/agent_assist/harness.py`
  - `docs/references/hermes.md`
  - `docs/audits/2026-05-21-agent-harness-review.md`
- Proof of completion:
  - Target artifact: `docs/audits/production-validation/sprint-02/hermes-invocation-dry-run.json`
- Human validation command as needed:
  - Not required for dry-run invocation; required before any external send/call/write.

---

## Sprint Item: Allowlisted Contact Requirement: Status ❌

- Description: Configure real caregiver and emergency-contact records outside Git-tracked secrets, then prove staged iMessage/FaceTime requests cannot target unallowlisted contacts.
- Required files for reference when working on this:
  - `contracts/schemas/agent-action-request.schema.json`
  - `contracts/examples/invalid/agent-action-request-missing-allowlist.json`
  - `apps/caresight-hub/config/hermes/env.caresight.example`
  - `apps/caresight-hub/caresight/runtime/agent_assist/service.py`
  - `docs/architecture/REPO_BOUNDARIES.md`
- Proof of completion:
  - Target artifact: `docs/audits/production-validation/sprint-02/allowlisted-contacts-redacted.json`
- Human validation command as needed:
  - Ask: "Please confirm which contact IDs are allowed for caregiver and emergency-contact testing. Do not provide secrets in Git-tracked files."

---

## Sprint Item: Execution Attempt Logging Requirement: Status ❌

- Description: Every real or dry-run external action attempt must be written to SQLite with request ID, target, execution state, timestamp, result, and error if any.
- Required files for reference when working on this:
  - `apps/caresight-hub/caresight/storage/migrations/001_init.sql`
  - `apps/caresight-hub/caresight/storage/sqlite_store.py`
  - `contracts/schemas/agent-action-request.schema.json`
  - `docs/architecture/bounded_control_loop.md`
- Proof of completion:
  - Target artifact: `docs/audits/production-validation/sprint-02/execution-attempt-logging.json`
- Human validation command as needed:
  - Not required for dry-run logging.

---

## Sprint Item: Screen Capture Or OBS Requirement: Status ❌

- Description: Configure and validate either a local screen-capture artifact path or OBS virtual camera path before offering visual handoff options.
- Required files for reference when working on this:
  - `docs/architecture/obs_facetime_live_view.md`
  - `docs/references/apple_shortcuts_facetime_notes.md`
  - `apps/caresight-hub/caresight/runtime/agent_assist/harness.py`
  - `docs/cli/COMMANDS.md`
- Proof of completion:
  - Target artifact: `docs/audits/production-validation/sprint-02/screen-capture-or-obs.md`
- Human validation command as needed:
  - Ask: "Please confirm the screen capture or OBS virtual camera output displays the intended camera feed and does not show unrelated private desktop content."

---

## Sprint Item: FaceTime Handoff Requirement: Status ❌

- Description: Configure FaceTime handoff as a human-approved action. It must not auto-call. It must either prepare the call instructions or wait for explicit approval before launching.
- Required files for reference when working on this:
  - `docs/architecture/obs_facetime_live_view.md`
  - `docs/references/apple_shortcuts_facetime_notes.md`
  - `apps/caresight-hub/caresight/runtime/agent_assist/harness.py`
  - `contracts/schemas/agent-action-request.schema.json`
- Proof of completion:
  - Target artifact: `docs/audits/production-validation/sprint-02/facetime-handoff.md`
- Human validation command as needed:
  - Ask before live action: "Approve one allowlisted FaceTime handoff test, or keep this at prepared-instructions only."

---

## Sprint Item: Local TTS Requirement: Status ❌

- Description: Generate and play local TTS from a validated `tts-utterance`, using Holler or selected local TTS model, without voice cloning or emergency certainty.
- Required files for reference when working on this:
  - `contracts/schemas/tts-utterance.schema.json`
  - `contracts/examples/valid/tts-utterance.possible-floor-stay.json`
  - `apps/caresight-hub/models/tts/holler/`
  - `docs/audits/2026-05-21-sprint-02-agent-model-surface.md`
- Proof of completion:
  - Target artifact: `docs/audits/production-validation/sprint-02/tts-playback.md`
- Human validation command as needed:
  - Ask: "Please confirm the TTS message is audible, calm, understandable, and does not imply medical or emergency certainty."

---

# Sprint 02 Production Validation Checklist

## Sprint Item: Case A Agent Draft And Validation: Status ❌

- Description: Run a real local Gemma draft for the concerning seeded-real event, validate forbidden claims, and persist the validated/blocked result in SQLite.
- Required files for reference when working on this:
  - `apps/caresight-hub/scripts/care_console.py`
  - `apps/caresight-hub/caresight/runtime/agent_assist/service.py`
  - `contracts/schemas/agent-draft.schema.json`
  - `contracts/schemas/forbidden-claim-vocabulary.schema.json`
  - Case A event artifact.
- Proof of completion:
  - Target artifact: `docs/audits/production-validation/sprint-02/case-a-agent-draft.json`
- Human validation command as needed:
  - Ask: "Does the concerning-event draft communicate urgency without saying fall, injury, medical emergency, or dispatch?"

---

## Sprint Item: Case B Agent Draft And Validation: Status ❌

- Description: Run a real local Gemma draft for the non-concerning seeded-real event, validate forbidden claims, and persist the validated/blocked result in SQLite.
- Required files for reference when working on this:
  - `apps/caresight-hub/scripts/care_console.py`
  - `apps/caresight-hub/caresight/runtime/agent_assist/service.py`
  - `contracts/schemas/agent-draft.schema.json`
  - Case B event/audit artifact.
- Proof of completion:
  - Target artifact: `docs/audits/production-validation/sprint-02/case-b-agent-draft.json`
- Human validation command as needed:
  - Ask: "Does the non-concerning draft avoid unnecessary escalation while remaining useful?"

---

## Sprint Item: Case A Urgent Handoff Staging: Status ❌

- Description: Stage an urgent handoff for the concerning case with an allowlisted emergency contact and response options for text update, screen capture, and FaceTime handoff.
- Required files for reference when working on this:
  - `contracts/schemas/agent-action-request.schema.json`
  - `contracts/examples/valid/agent-action-request.urgent-handoff.json`
  - `apps/caresight-hub/scripts/care_console.py`
  - `apps/caresight-hub/caresight/runtime/agent_assist/harness.py`
- Proof of completion:
  - Target artifact: `docs/audits/production-validation/sprint-02/case-a-urgent-action-request.json`
  - Target artifact: `docs/audits/production-validation/sprint-02/case-a-hermes-handoff-payload.json`
- Human validation command as needed:
  - `python3 apps/caresight-hub/scripts/care_console.py hermes-handoff-payload <case_a_request_id>`
  - Ask: "Does this staged urgent handoff ask for direction and offer screen capture or FaceTime handoff without initiating either?"

---

## Sprint Item: Case B Non-Urgent Staging: Status ❌

- Description: Stage a non-urgent caregiver update for the non-concerning case. It must not target emergency contacts or offer FaceTime unless a human explicitly asks.
- Required files for reference when working on this:
  - `contracts/schemas/agent-action-request.schema.json`
  - `apps/caresight-hub/scripts/care_console.py`
  - `apps/caresight-hub/caresight/runtime/agent_assist/service.py`
  - Case B event/audit artifact.
- Proof of completion:
  - Target artifact: `docs/audits/production-validation/sprint-02/case-b-nonurgent-action-request.json`
- Human validation command as needed:
  - Ask: "Does the normal-case staged update stay non-urgent and avoid emergency-contact routing?"

---

## Sprint Item: Hermes Dry-Run Invocation On Case A: Status ❌

- Description: Invoke Hermes with the Case A staged urgent payload in dry-run or no-send mode and capture the local output.
- Required files for reference when working on this:
  - `apps/caresight-hub/vendor/hermes-agent`
  - `apps/caresight-hub/config/hermes/config.caresight.local.yaml`
  - `apps/caresight-hub/config/hermes/env.caresight.example`
  - `docs/references/hermes.md`
- Proof of completion:
  - Target artifact: `docs/audits/production-validation/sprint-02/case-a-hermes-dry-run.json`
- Human validation command as needed:
  - Not required unless Hermes prompts for local credentials or operator setup.

---

## Sprint Item: Hermes Dry-Run Invocation On Case B: Status ❌

- Description: Invoke Hermes with the Case B non-urgent staged payload in dry-run or no-send mode and capture the local output.
- Required files for reference when working on this:
  - `apps/caresight-hub/vendor/hermes-agent`
  - `apps/caresight-hub/config/hermes/config.caresight.local.yaml`
  - `docs/references/hermes.md`
- Proof of completion:
  - Target artifact: `docs/audits/production-validation/sprint-02/case-b-hermes-dry-run.json`
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
- Human validation command as needed:
  - Ask: "Approve sending one test iMessage to the allowlisted contact. Confirm receipt and whether the text is acceptable."

---

## Sprint Item: Human-Approved Visual Handoff Test: Status ❌

- Description: Validate either screen capture by request or FaceTime handoff by request after human approval. No automatic call or raw-video send.
- Required files for reference when working on this:
  - `docs/architecture/obs_facetime_live_view.md`
  - `docs/references/apple_shortcuts_facetime_notes.md`
  - `docs/audits/production-validation/sprint-02/screen-capture-or-obs.md`
  - `docs/audits/production-validation/sprint-02/facetime-handoff.md`
- Proof of completion:
  - Target artifact: `docs/audits/production-validation/sprint-02/human-approved-visual-handoff.md`
- Human validation command as needed:
  - Ask: "Approve one visual handoff test. Confirm that only the intended camera feed/screen capture is shown."

---

## Sprint Item: Human-Validated TTS Playback: Status ❌

- Description: Play a validated local TTS message for Case A or Case B and have the human confirm the audio quality and wording.
- Required files for reference when working on this:
  - `contracts/schemas/tts-utterance.schema.json`
  - `apps/caresight-hub/models/tts/holler/`
  - `docs/audits/production-validation/sprint-02/tts-playback.md`
- Proof of completion:
  - Target artifact: `docs/audits/production-validation/sprint-02/human-validated-tts.md`
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
  - Target artifact: `docs/audits/production-validation/sprint-02/production-acceptance.md`
- Human validation command as needed:
  - Ask: "Approve Sprint 02 as production-ready for the current local prototype scope, or list exact remaining blockers."

---

# Pre-Live-Test Gate

## Sprint Item: Seeded-Real A/B Gate Before New Live Test: Status ❌

- Description: Do not stage another live test until seeded-real Case A and Case B pass Sprint 01 and Sprint 02 validation. The seeded-real gate should prove behavior on both concerning and non-concerning cases.
- Required files for reference when working on this:
  - This checklist.
  - `docs/audits/production-validation/sprint-01/`
  - `docs/audits/production-validation/sprint-02/`
  - `docs/audits/2026-05-20-t041-final-live-proof.md`
- Proof of completion:
  - Target artifact: `docs/audits/production-validation/sprint-01-02-seeded-real-gate.md`
- Human validation command as needed:
  - Ask: "Approve moving from seeded-real A/B validation to a staged live test."
