# CareSight Sprint 01/02 Production Validation

## Objective

Execute the production-readiness validation ladder for CareSight Sprint 01 and Sprint 02 using the seeded-real A/B strategy in `docs/roadmaps/caresight_sprint_pack/09-sprint-01-02-production-validation.md`.

The goal is not to prove that scaffolding exists. The goal is to make Sprint 01 and Sprint 02 production-ready for the current local prototype scope: real local artifacts, real seeded-real validation, real Gemma serving where required, real Hermes invocation where required, explicit human approval where required, and durable proof receipts.

## Original Request

Use GoalBuddy goal prep with `docs/roadmaps/caresight_sprint_pack/09-sprint-01-02-production-validation.md` to build a detailed task board for Sprint 01/02 production validation. No shortcuts. The production standard is operational readiness, not fixtures, templates, fake providers, or dry-run-only claims.

## Intake Summary

- Input shape: `existing_plan`
- Audience: CareSight operators, caregivers, future coding agents, and hackathon/product reviewers.
- Authority: `approved`
- Proof type: `artifact`, `test`, `demo`, and `review`
- Completion proof: the checklist has been executed with `✅` status updates, linked artifacts, human validation receipts where required, passing repo checks, and a final Judge/PM audit stating `full_outcome_complete: true`.
- Goal oracle: Sprint 01 and Sprint 02 are production-ready only when seeded-real Case A and Case B pass the checklist, real runtime integrations work where required, external actions remain human-approved and allowlisted, and all proof artifacts are linked from the checklist.
- Likely misfire: marking Sprint 01/02 complete because contracts, fake providers, templates, or dry-run payloads exist, while real Gemma/Hermes/contact/screen/FaceTime/TTS paths remain unproven.
- Blind spots considered: seeded-real non-concerning case capture, local model serving feasibility, Hermes invocation boundary, credential/allowlist handling, execution-attempt logging, visual privacy, TTS audibility, human approval capture, and final live-test gate.

## Existing Plan Facts

- Use Case A: `evt_d9aa38bdc636459c92ea4e25f665cd0d` from `docs/audits/2026-05-20-t041-final-live-proof.md`.
- Create or capture Case B as a non-concerning seeded-real desk/normal-presence case.
- Validate Sprint 01 packet/receipt behavior on both cases.
- Validate Sprint 02 real product requirements, not only staged scaffolding.
- Do not stage another live test until seeded-real A/B validation passes.
- Mark checklist items `✅` only when proof artifacts or human validation prompts are recorded.

## Non-Negotiable Constraints

- Do not describe CareSight as a medical device.
- Do not claim HIPAA compliance.
- Do not implement autonomous emergency dispatch.
- Do not confirm medication administration from vision alone.
- Use `possible event` or `likely observed` unless an authorized human confirmation exists.
- Keep YOLO26 MLX as the vision lane.
- Keep Gemma/Hermes as summary/orchestration/service-wrapper lanes only.
- Store structured events and execution attempts locally first.
- Do not add Ring/Nest integrations.
- Preserve the bounded loop: observation, policy, human confirmation, journal, audit.
- No external iMessage, FaceTime, screen-sharing, OBS, or TTS live action without explicit human approval.
- No raw video to Gemma or Hermes as decision-maker.
- Do not commit secrets or real contact credentials.

## Goal Oracle

The oracle for this goal is:

`The Sprint 01/02 production validation checklist shows ✅ for all required production gates, with linked proof artifacts under docs/audits/production-validation/, passing npm run check, seeded-real A/B evidence for concerning and non-concerning cases, real local Gemma/Hermes/TTS/visual-handoff validation or explicitly blocked human-approved receipts, and a final audit receipt that records full_outcome_complete: true.`

## Current Tranche

This is a production-readiness execution tranche. It should proceed continuously through safe local work, using human approval only for the specific items that require human judgment, credentials, camera operation, messaging, visual handoff, or audio confirmation.

## Canonical Board

Machine truth lives at:

`docs/goals/caresight-sprint-01-02-production-validation/state.yaml`

If this charter and `state.yaml` disagree, `state.yaml` wins for task status, active task, receipts, verification freshness, and completion truth.

## Run Command

```text
/goal Follow docs/goals/caresight-sprint-01-02-production-validation/goal.md.
```

## PM Loop

On every `/goal` continuation:

1. Read this charter.
2. Read `state.yaml`.
3. Use the checklist as the production gate.
4. Work only on the active task.
5. Mark checklist items `✅` only after proof is present.
6. Keep blocked human/credential/live-action tasks explicit and continue safe local work around them.
7. Run verification after write-capable tasks.
8. Finish only with a final Judge/PM audit receipt proving the full owner outcome.
