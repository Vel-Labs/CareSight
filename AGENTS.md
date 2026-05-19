# AGENTS

This file defines how humans and coding agents should operate in this repository.

## Mission

Build `CareSight Hub` as a bounded, local-first caregiver awareness prototype that is clear, auditable, safety-aware, and credible for a hackathon demo.

## Priority Order

1. Preserve resident and caregiver safety.
2. Preserve the bounded control loop.
3. Preserve local-first privacy defaults.
4. Preserve architectural clarity between contracts, TypeScript governance, and Python runtime.
5. Preserve auditability and reproducible checks.
6. Keep docs tied to working behavior.

## Required Reading Before Structural Changes

- `README.md`
- `ROADMAP.md`
- `REPO_PROFILE.json`
- `docs/project/PROJECT_BRIEF.md`
- `docs/architecture/ARCHITECTURE.md`
- `docs/architecture/REPO_BOUNDARIES.md`
- `docs/roadmaps/CURRENT_STATE_AND_NEXT.md`
- `docs/hackathon/hackathon_roadmap.md`
- `contracts/README.md`

## CareSight-Specific Rules

- Do not describe CareSight as a medical device.
- Do not claim HIPAA compliance.
- Do not implement autonomous emergency dispatch.
- Do not confirm medication administration from vision alone.
- Use `likely observed` or `possible event` unless confirmed by an authorized human.
- Keep YOLO26 MLX as the vision lane.
- Keep Gemma/OpenClaw as summary or orchestration only.
- Store structured events locally first.
- Do not add Ring/Nest integrations to v1/v2 unless explicitly moved into scope.
- Preserve the bounded control loop: observation, policy, human confirmation, journal, audit.

## CLI and Review Flow Rules

- Every supported CLI command must be documented in `docs/cli/COMMANDS.md`.
- Agents may run event `list` and `show` commands.
- Agents may summarize events.
- Agents may draft caregiver messages.
- Agents must not confirm or dismiss events unless explicitly instructed by a human.
- Agents must not trigger emergency dispatch.
- Agents must preserve `snapshot_path`, `event_id`, `reviewer`, timestamps, and `status`.
- Every event lifecycle change needs a deterministic test where practical.

## Architecture Rules

- `contracts/` owns canonical schemas and examples.
- `packages/core/` owns TypeScript validation and contract enforcement helpers.
- `tests/` owns shared governance and contract quality gates.
- `apps/caresight-hub/` owns the Python runtime boundary.
- `docs/` owns roadmap, architecture, hackathon, references, and audit context.

Do not put runtime implementation in `packages/core/`. Do not let dashboard code become canonical truth. Do not add live integrations without a matching contract and decision record.

## Working Rules

- Keep changes scoped.
- Do not hard-code values that should come from config, contracts, schemas, or source-of-truth records.
- Do not claim a feature works without evidence.
- Keep large files below 350 lines where practical.
- Files above 500 lines require extraction or written justification.
- Update docs when behavior changes.
- Record architectural decisions in `DECISIONS.md`.
- Record notable changes in `CHANGELOG.md`.
- Keep validation output concrete in handoffs.

## Multi-Agent Development Rules

Use separate worktrees for parallel coding agents. No two agents should own the same files unless coordinated by a human.

Each agent must declare:

- workstream
- files it expects to touch
- files it must not touch
- dependencies
- validation plan
- docs to update

## Definition of Done

A change is not done unless:

- behavior is documented
- tests or deterministic checks exist where practical
- relevant risks are noted
- changelog is updated
- decisions are recorded when architecture changes
- no unrelated files are staged
