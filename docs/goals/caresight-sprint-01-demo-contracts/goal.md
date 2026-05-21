# CareSight Sprint 01 Demo Surface and Contract Pack

## Objective

Implement Sprint 01 Demo Surface Consolidation for CareSight and, if it remains a quick bounded tack-on, reconcile the Sprint 07 contract JSON pack before starting the Agent/LLM drafting layer.

## Original Request

Prepare GoalBuddy for Sprint 01, and potentially 07 if it seems like a reasonable quick tack-on while in progress. Review `00-master-codex-prompt.md` as needed. Work agents in parallel to make sure all functionality is carried out efficiently.

## Intake Summary

- Input shape: `existing_plan`
- Audience: CareSight operators, future Codex agents, hackathon demo reviewers, and caregiver-aware product reviewers.
- Authority: `requested`
- Proof type: `test`
- Completion proof: Sprint 01 behavior is implemented, documented, and verified by concrete commands, with contract-backed review-packet and blackbox-receipt outputs for the proven event.
- Goal oracle: `npm run check` passes and the focused proof event `evt_d9aa38bdc636459c92ea4e25f665cd0d` can produce a review packet and blackbox receipt from SQLite without mutating event lifecycle state.
- Likely misfire: GoalBuddy could create contracts or docs only and miss the actual CLI/runtime/dashboard behavior, or jump into Agent/LLM drafting before the receipt and contract boundaries are concise.
- Blind spots considered: contract-validator compatibility, stale `docs/FILE_TREE.md`, human-review authority boundaries, stale awaiting-review backlog handling, generated receipt completeness, and whether Sprint 07 is small alignment work or a larger contract migration.
- Existing plan facts: Preserve order `01 -> 07 -> 02 -> 03 -> 04 -> 05 -> 06 -> 08`; start with Sprint 01; use `07-contract-json-pack.md` as a contract-normalization checkpoint; do not start Gemma/OpenClaw/Hermes until Sprint 01 and contract alignment are proven.

## Goal Oracle

The oracle for this goal is:

`npm run check` passes, and `care_console.py review-packet` plus `care_console.py blackbox-receipt` produce schema-valid, SQLite-derived, bounded outputs for `evt_d9aa38bdc636459c92ea4e25f665cd0d`.

The PM must keep comparing task receipts to this oracle. Planning, discovery, contract files alone, or a clean-looking board is not enough. The goal finishes only when a final Judge/PM audit maps receipts and verification back to this oracle and records `full_outcome_complete: true`.

## Goal Kind

`existing_plan`

## Current Tranche

Complete the largest safe local tranche that gets Sprint 01 working end to end:

1. Review the sprint pack and current repo surface.
2. Decide whether Sprint 07 contract JSON alignment is quick enough to fold into the Sprint 01 contract slice.
3. Add or reconcile Sprint 01 contracts and examples.
4. Implement read-only review-packet and blackbox-receipt services from SQLite audit chains.
5. Add documented `care_console.py` commands.
6. Make focused dashboard state explicitly separate the selected proof event from stale awaiting-review backlog.
7. Verify with deterministic tests and the repo gate.
8. Record a durable audit receipt and update docs/changelog/file tree as required.

## Non-Negotiable Constraints

- Follow `AGENTS.md` for CareSight safety, local-first, architecture, CLI, and Definition of Done rules.
- Do not describe CareSight as a medical device.
- Do not claim HIPAA compliance.
- Do not implement autonomous emergency dispatch.
- Do not confirm medication administration, hydration completion, injury, diagnosis, or medical state from vision alone.
- Use `possible event`, `likely observed`, or human-review-qualified language.
- Preserve the bounded control loop: observation, policy, human confirmation, journal, audit.
- Keep SQLite canonical; dashboard, alerts, packets, receipts, and agents are derived.
- Do not let dashboard or receipt code become canonical truth.
- Every new CLI command must be documented in `docs/cli/COMMANDS.md`.
- Every behavior change needs deterministic tests where practical.
- Update `CHANGELOG.md`, `DECISIONS.md` when architecture changes, and `docs/FILE_TREE.md` when validation requires it.
- Do not start Agent/LLM drafting implementation in this tranche.

## Parallel Work Policy

The user explicitly requested parallel agents. Use parallel Scout/Judge work for read-only mapping immediately. Use parallel Worker agents only after Judge proves the write scopes are disjoint and `state.yaml` names the allowed files for each Worker. At most one Worker may touch any given file.

## Stop Rule

Stop only when a final audit proves the full original outcome for this tranche is complete.

Do not stop after planning, discovery, or Judge selection if a safe Worker task can be activated.

Do not stop after the contract slice if runtime, CLI, docs, tests, or audit evidence remain required for Sprint 01.

If Sprint 07 turns out larger than a quick contract-normalization tack-on, block or defer it with a receipt and continue Sprint 01 without letting Agent/LLM scope leak into the tranche.

## Slice Sizing

Safe means bounded, explicit, verified, and reversible. It does not mean tiny.

A good Worker slice should produce a contract-backed behavior milestone: schema/examples, read-only services, CLI/dashboard surface, or docs/audit verification. Repeated same-shape contract examples or tests belong in one Worker package when safe.

## Canonical Board

Machine truth lives at:

`docs/goals/caresight-sprint-01-demo-contracts/state.yaml`

If this charter and `state.yaml` disagree, `state.yaml` wins for task status, active task, receipts, verification freshness, and completion truth.

## Run Command

```text
/goal Follow docs/goals/caresight-sprint-01-demo-contracts/goal.md.
```

## PM Loop

On every `/goal` continuation:

1. Read this charter.
2. Read `state.yaml`.
3. Run the bundled GoalBuddy update checker when available and mention a newer version without blocking.
4. Work only on the active board task.
5. Use `goalbuddy parallel-plan docs/goals/caresight-sprint-01-demo-contracts` for the opening parallel read-only mapping, then dispatch only the safe roles it recommends.
6. Write compact receipts after each task.
7. Keep the board moving until the final audit maps implementation, documentation, and verification back to the oracle.
