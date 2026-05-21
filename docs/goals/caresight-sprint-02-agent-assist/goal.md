# CareSight Sprint 02 Agent Assist

## Objective

Prepare and execute Sprint 02 as a bounded, local-first agent-assist layer for CareSight Hub: contracts first, fake provider first, validated local persistence, staged action requests only, CLI/docs coverage, and model selection only after fake-provider proof passes.

## Original Request

The next move is Sprint 02: add contracts for agent-draft, agent-action-request, tts-utterance, and forbidden-claim vocabulary; add valid/invalid examples; implement fake provider first; store validated/blocked drafts in SQLite; add action-request staging only with no external execution; add CLI commands and docs; after fake provider passes, identify which Gemma MLX model is best fit, considering Gemma MLX and TTS MLX options for a 16 GB Mac mini.

## Intake Summary

- Input shape: `existing_plan`
- Audience: CareSight Hub demo operators, caregivers, and future coding agents working in this repository.
- Authority: `requested`
- Proof type: `test`
- Completion proof: deterministic contract/runtime/CLI checks pass, docs and changelog are updated, staged action requests never execute externally, and a source-backed Gemma/TTS model recommendation is recorded after fake-provider proof.
- Goal oracle: a final Judge audit maps task receipts to passing contract tests, valid/invalid examples, fake-provider SQLite persistence, staging-only action-request behavior, documented CLI commands, and a source-backed model recommendation constrained to a 16 GB Mac mini.
- Likely misfire: implementing a real LLM/TTS provider, external action execution, or caregiver-facing claims before the safety contracts and fake-provider guardrails prove the loop.
- Blind spots considered: forbidden medical/emergency claims, autonomous dispatch risk, local-first privacy, SQLite auditability, CLI documentation drift, model memory pressure on 16 GB hardware, and the difference between blocked drafts and human-confirmed statements.
- Existing plan facts:
  - Add Sprint 02 contracts first: `agent-draft`, `agent-action-request`, `tts-utterance`, and forbidden-claim vocabulary.
  - Add valid and invalid examples.
  - Implement a fake provider before any Gemma/OpenClaw provider.
  - Store validated and blocked drafts in SQLite.
  - Add action-request staging only; no external execution.
  - Add CLI commands and update `docs/cli/COMMANDS.md`.
  - After fake provider passes, identify the best Gemma MLX model for the system budget.
  - User-named model candidates: `mlx-community/gemma-4-e4b-it-4bit`, `mlx-community/gemma-4-e2b-it-4bit`, `sentiuminc/holler-0.6b`, and `sentiuminc/holler-0.6b-6bit`.

## Goal Oracle

The oracle for this goal is:

`A final Judge audit confirms that Sprint 02 contracts, examples, fake-provider validation/persistence, staged-only action requests, CLI docs, and source-backed local-model recommendations are all present and verified without medical-device, HIPAA, emergency-dispatch, medication-confirmation, or external-execution overclaims.`

The PM must keep comparing task receipts to this oracle. Planning, discovery, a passing tiny slice, or a clean-looking board is not enough. The goal finishes only when a final Judge/PM audit maps receipts and verification back to this oracle and records `full_outcome_complete: true`.

## Goal Kind

`existing_plan`

## Current Tranche

This tranche is Sprint 02. It should proceed continuously through the largest safe verified slices: validate the user plan and repo boundaries, implement the contract/example layer, implement the fake-provider and SQLite persistence layer, add staged action-request CLI/docs, then perform source-backed Gemma/TTS model selection after fake-provider proof passes.

## Non-Negotiable Constraints

- Do not describe CareSight as a medical device.
- Do not claim HIPAA compliance.
- Do not implement autonomous emergency dispatch.
- Do not confirm medication administration from vision alone.
- Use `likely observed` or `possible event` unless confirmed by an authorized human.
- Keep YOLO26 MLX as the vision lane.
- Keep Gemma/OpenClaw as summary or orchestration only.
- Store structured events locally first.
- Do not add Ring/Nest integrations to v1/v2 unless explicitly moved into scope.
- Preserve the bounded loop: observation, policy, human confirmation, journal, audit.
- Every supported CLI command must be documented in `docs/cli/COMMANDS.md`.
- Agents must not confirm or dismiss events unless explicitly instructed by a human.
- Action requests are staged only in Sprint 02; no external execution.
- Model recommendation must be source-backed and constrained to the ability to contain the full system on a 16 GB RAM Mac mini.

## Stop Rule

Stop only when a final audit proves the full original outcome is complete.

Do not stop after planning, discovery, or Judge selection if a safe Worker task can be activated.

Do not stop after a single verified Worker package when the broader Sprint 02 outcome still has safe local follow-up work. Advance the board to the next highest-leverage safe Worker package and continue unless a phase, risk, rejected-verification, ambiguity, or final-completion review is due.

Do not create one Worker/Judge pair per repeated schema, example, route, or helper. Put repeated same-shape work into one Worker package and review the package as a whole.

## Slice Sizing

Safe means bounded, explicit, verified, and reversible. It does not mean tiny.

A good task is the largest safe useful slice. For Sprint 02, contracts/examples are one coherent first implementation package; fake-provider SQLite behavior is one coherent second package; staged action-request CLI/docs are one coherent third package; model selection is source-backed research only after fake-provider proof.

## Canonical Board

Machine truth lives at:

`docs/goals/caresight-sprint-02-agent-assist/state.yaml`

If this charter and `state.yaml` disagree, `state.yaml` wins for task status, active task, receipts, verification freshness, and completion truth.

## Run Command

```text
/goal Follow docs/goals/caresight-sprint-02-agent-assist/goal.md.
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
10. Review at phase, risk, rejected-verification, ambiguity, or final-completion boundaries; do not review every small Worker by habit.
11. Finish only with a Judge/PM audit receipt that maps receipts and verification back to the original user outcome and records `full_outcome_complete: true`.
