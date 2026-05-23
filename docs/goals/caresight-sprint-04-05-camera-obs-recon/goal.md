# CareSight Sprint 04/05 Camera and OBS Recon

## Objective

Execute the sprint 04 and sprint 05 plan from `docs/superpowers/plans/2026-05-23-sprint-04-05-camera-obs-recon.md`, then review sprint readiness and runtime blockers across Sprint 02, Sprint 03, Sprint 04, Sprint 05, and any fixed issues with concrete validation receipts.

## Original Request

Use the sprint 04/05 camera OBS recon plan as task scope; proceed autonomously through understanding, discovery, resolution, implementation, and detailed validation cycles; do not get hung up on human review; do not engage FaceTime calling functionality overnight; do sprint 04, sprint 05, then review sprint items including Sprint 02 FaceTime x OBS virtual camera/TTS, Sprint 03 internet still-image testing for hats, outfits, and footwear, and thorough review of sprint 04/05 plus any fixes or researched solution proposals.

## Intake Summary

- Input shape: `existing_plan`
- Audience: CareSight hackathon owner and local demo operator
- Authority: `approved`
- Proof type: `test`
- Completion proof: Sprint 04 and Sprint 05 implementation/recovery tasks are either completed or explicitly blocked with evidence; Sprint 02 runtime handoff blockers are tested without overnight FaceTime calling; Sprint 03 visual cases are validated with sourced still images; docs, CLI references, changelog, and decisions are updated where behavior changes; final audit maps every sprint item to receipts, commands, artifacts, and remaining blockers.
- Goal oracle: `npm run check` plus targeted Python/CLI/browser/OBS-safe deterministic checks, artifact receipts, sourced-image test records, no-send/no-call handoff receipts, and final Judge/PM audit with `full_outcome_complete: true`.
- Likely misfire: Completing only planning, docs, or a single OBS slice while leaving Sprint 04/05 execution, Sprint 02 runtime gates, or Sprint 03 clothing/footwear validation untested.
- Blind spots considered: macOS OBS virtual camera permission may be system-level rather than repo logic; FaceTime must not be engaged overnight; human review is an operator task, not a reason to stall; internet images need source records and bounded non-medical claims; MJPEG/browser-feed is acceptable for local demo proof but not a production video architecture claim.
- Existing plan facts: Preserve the supplied plan path as primary scope: `docs/superpowers/plans/2026-05-23-sprint-04-05-camera-obs-recon.md`; preserve sprint order: Sprint 04 first, Sprint 05 second, then cross-sprint review; preserve CareSight AGENTS constraints and required reading before structural changes; keep YOLO26 MLX as vision lane; keep Gemma/OpenClaw as summary/orchestration only; never claim medical-device behavior, HIPAA compliance, autonomous emergency dispatch, or medication confirmation from vision alone.

## Goal Oracle

The oracle for this goal is:

`A final sprint audit that points to current receipts for Sprint 04, Sprint 05, Sprint 02 FaceTime/OBS/TTS gates, Sprint 03 still-image clothing/accessory/footwear validation, changed files, docs updates, and passing deterministic checks, while preserving no-call overnight and local-first human-review boundaries.`

The PM must keep comparing task receipts to this oracle. Planning, discovery, a passing tiny slice, or a clean-looking board is not enough. The goal finishes only when a final Judge/PM audit maps receipts and verification back to this oracle and records `full_outcome_complete: true`.

## Goal Kind

`existing_plan`

## Current Tranche

Run a continuous execution tranche: validate the supplied plan and repo state, complete Sprint 04, complete Sprint 05, then perform cross-sprint validation for Sprint 02 and Sprint 03 blockers, adding implementation fixes, documentation, tests, and research notes as needed. Continue through safe local work without waiting for human review, credentials, or overnight call approval; mark only the exact blocked item as blocked and proceed to adjacent deterministic work.

## Non-Negotiable Constraints

- Do not engage FaceTime calling functionality overnight.
- Do not trigger emergency dispatch.
- Do not confirm or dismiss events unless explicitly instructed by a human.
- Do not claim human review, production readiness, medical-device status, HIPAA compliance, or physical-device proof without current evidence.
- Preserve the bounded control loop: observation, policy, human confirmation, journal, audit.
- Store structured events locally first and preserve `snapshot_path`, `event_id`, `reviewer`, timestamps, and `status`.
- Every supported CLI command must be documented in `docs/cli/COMMANDS.md`.
- Behavior changes require docs updates, `CHANGELOG.md`, tests or deterministic checks where practical, and `DECISIONS.md` entries when architecture changes.
- Keep runtime implementation out of `packages/core/`; keep canonical schemas in `contracts/`; keep Python runtime boundary in `apps/caresight-hub/`.
- Treat OBS virtual camera failures as potentially macOS permission/setup failures before calling them CareSight-code failures.
- Treat MJPEG/browser-feed as local-demo architecture only unless a decision record explicitly changes that claim.

## Stop Rule

Stop only when a final audit proves the full original outcome is complete.

Do not stop after planning, discovery, or Judge selection if a safe Worker task can be activated.

Do not stop after a single verified Worker package when the broader owner outcome still has safe local follow-up work. Advance the board to the next highest-leverage safe Worker package and continue unless a phase, risk, rejected-verification, ambiguity, or final-completion review is due.

Do not stop because a slice needs owner input, credentials, production access, destructive operations, or policy decisions. Mark that exact slice blocked with a receipt, create the smallest safe follow-up or workaround task, and continue all local, non-destructive work that can still move the goal toward the full outcome.

## Slice Sizing

Safe means bounded, explicit, verified, and reversible. It does not mean tiny.

A good task is the largest safe useful slice.

Small is not the goal. Useful is the goal.

A Worker should finish the whole assigned slice. A Judge should judge the whole assigned slice. A PM should reorient the board when tasks are safe but not moving the outcome.

## Canonical Board

Machine truth lives at:

`docs/goals/caresight-sprint-04-05-camera-obs-recon/state.yaml`

If this charter and `state.yaml` disagree, `state.yaml` wins for task status, active task, receipts, verification freshness, and completion truth.

## Run Command

```text
/goal Follow docs/goals/caresight-sprint-04-05-camera-obs-recon/goal.md.
```

## PM Loop

On every `/goal` continuation:

1. Read this charter.
2. Read `state.yaml`.
3. Run the bundled GoalBuddy update checker when available and mention a newer version without blocking.
4. Re-check the intake: original request, input shape, authority, proof, blind spots, existing plan facts, and likely misfire.
5. Work only on the active board task.
6. Assign Scout, Judge, Worker, or PM according to the task.
7. Write a compact task receipt.
8. Update the board.
9. If safe local work remains, choose the next largest reversible Worker package and continue unless blocked.
10. Review at phase, risk, rejected-verification, ambiguity, or final-completion boundaries.
11. Finish only with a Judge/PM audit receipt that maps receipts and verification back to the original user outcome and records `full_outcome_complete: true`.
