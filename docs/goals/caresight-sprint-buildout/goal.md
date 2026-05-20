# CareSight Sprint Buildout Goal

> **For agentic workers:** REQUIRED SUB-SKILL: Use GoalBuddy task prompts and the required `goal_scout`, `goal_judge`, or `goal_worker` agent type for each active task. This board is the source of truth; follow `docs/goals/caresight-sprint-buildout/state.yaml`.

## Original Request

Turn the CareSight sprint plan into GoalBuddy so agents can rapidly and safely action the buildout with a proven audit trail.

## Interpreted Outcome

Prepare and execute a safe, auditable CareSight buildout from the current v0 loop through blackbox evidence, review console, YOLO26 inference harness, tracking, v1 event policies, segmentation evaluation, dashboard/journal/alerts, local multi-camera support, and constrained agent/LLM assistance.

## Input Shape

`existing_plan`

The user provided a detailed sprint plan and approved defaults for scope, safety boundaries, blackbox SQLite logging, review authority, real-live-data demo proof, multi-camera narrative, code cleanliness, CLI wrappers, agent skills, and documentation.

## Audience

CareSight maintainers, hackathon judges, local caregivers evaluating the prototype, and future coding agents that need clear contracts and receipts.

## Goal Oracle

The goal remains active until the board produces an auditable CareSight demo tranche where:

- A real live-camera `possible_floor_stay` is persisted to SQLite.
- The event can be listed, shown, reviewed, journaled, and handed off.
- SQLite contains blackbox-style records for events, observations, reviews, journal entries, generated handoffs, and relevant provenance.
- CLI commands and dashboard/review-console behavior use the same service boundaries.
- YOLO26 MLX inference is behind a CareSight-owned runner with detection/observation separation and camera/room metadata.
- Tracking and event policy work is verified by deterministic tests before demo claims expand.
- Every completed task has a GoalBuddy receipt with changed files, commands, and remaining risks.

## Completion Proof

Completion for this tranche requires a final Judge or PM audit receipt with:

- `full_outcome_complete: true`
- exact commands run
- verification status
- dirty diff summary
- links or paths to audit receipts
- evidence that no required Worker task remains queued or active

## Non-Negotiable Constraints

- Preserve resident and caregiver safety.
- Do not describe CareSight as a medical device.
- Do not claim HIPAA compliance.
- Do not implement autonomous emergency dispatch.
- Do not confirm medication administration from vision alone.
- Do not identify a specific medication as taken.
- Do not add Ring/Nest/cloud camera integrations to hackathon core.
- Keep raw video local by default.
- Keep YOLO26 MLX as the vision lane.
- Keep Gemma/OpenClaw/Hermes/LLM layers constrained to summaries, drafts, audit, and handoff assistance.
- Agents may read, list, show, summarize, draft, and audit; agents must not confirm, dismiss, dispatch, diagnose, delete records, or become reviewer of record.
- SQLite is the unbiased blackbox source of truth.
- Scripts should be thin wrappers; runtime behavior belongs in focused modules.
- Keep files below 350 lines where practical; files above 500 lines require extraction or written justification.
- Every supported CLI command must be documented in `docs/cli/COMMANDS.md`.
- Behavior changes require docs, tests or deterministic checks where practical, `CHANGELOG.md`, and `DECISIONS.md` when architecture changes.
- “Delivered” demo proof should use live data. Seeded/synthetic data is acceptable only for deterministic tests and smoke checks.

## Existing Plan Facts To Preserve

- Sprint 1: close v0 live loop with real data and detailed blackbox audit receipt.
- Sprint 2: build review console and keep CLI wrappers documented.
- Sprint 3: wrap YOLO26 MLX behind a CareSight-owned inference harness.
- Sprint 4: add track-aware floor-stay, missing-off-camera logic, severity scaling, and multi-room narrative.
- Sprint 5: add deterministic v1 event engine for floor-stay, missing-off-camera, medication routine likely observed, and hydration routine likely observed.
- Sprint 6: evaluate segmentation only if it improves evidence or demo clarity without delaying v1.
- Sprint 7: build dashboard, journal, Apple Notes-style logging, and text-to-FaceTime escalation artifacts.
- Sprint 8: support practical local multi-camera configuration, ideally two local cameras with room labels and RTSP.
- Sprint 9: add constrained agent/LLM assistance with provenance and forbidden-action tests.

## Likely Misfire To Avoid

Do not produce a broad roadmap or a visually impressive dashboard while the actual blackbox loop, review authority, event policies, and verification evidence remain weak. Do not let agents, dashboard code, or LLM output become canonical truth.

## Current Tranche

This GoalBuddy board should first validate the sprint plan against the repo, then execute the largest safe useful slices in order:

1. v0 blackbox live-loop closeout.
2. review service and console boundary.
3. YOLO26 inference harness.
4. tracking and multi-room event reliability.
5. v1 event policies.
6. dashboard/journal/escalation and constrained agent assistance.

The PM may reorder queued tasks after Scout/Judge receipts if verification, risk, or existing code shape demands it.

## Starter Command

```text
/goal Follow docs/goals/caresight-sprint-buildout/goal.md.
```
