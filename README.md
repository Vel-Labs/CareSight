# CareSight Hub

CareSight Hub is a local-first caregiver awareness prototype for the YOLO26 MLX hackathon. It uses the project scaffold as the repo backbone for governance, contracts, quality gates, and agent-safe collaboration, then keeps the Python/MLX runtime in a separate app boundary.

CareSight is not a medical device, certified fall detector, alarm service, emergency dispatch product, or HIPAA-compliant clinical system. The MVP creates local care observations that authorized humans can acknowledge, confirm, or dismiss.

## Current Ship Goal

Build the v1/v2 hackathon MVP:

```text
camera input
  -> YOLO26 MLX local perception
  -> bounded event rules and confidence scoring
  -> SQLite local memory
  -> daily care journal
  -> caregiver alert
  -> optional OBS / FaceTime handoff
```

## Repo Shape

- `contracts/`: canonical schemas, examples, lifecycle, and fail-closed behavior.
- `packages/core/`: TypeScript validation and contract enforcement helpers.
- `tests/`: shared local quality gate for governance and contracts.
- `apps/caresight-hub/`: bounded Python runtime for YOLO26 MLX, camera handling, SQLite, alerts, and dashboard work.
- `docs/`: project brief, architecture, hackathon docs, roadmaps, references, and the imported docs pack.

## Start Here

1. Read `AGENTS.md`.
2. Read `docs/project/PROJECT_BRIEF.md`.
3. Read `docs/architecture/REPO_BOUNDARIES.md`.
4. Read `docs/roadmaps/CURRENT_STATE_AND_NEXT.md`.
5. Run the quality gate:

```bash
npm run install:local
npm run check
```

The npm gate validates scaffold structure, contract schemas/examples, TypeScript tests, and the current Python runtime skeleton.

## Roadmaps

- Hackathon plan: `docs/hackathon/hackathon_roadmap.md`
- Future product plan: `docs/roadmaps/future_roadmap.md`
- Operational next steps: `docs/roadmaps/CURRENT_STATE_AND_NEXT.md`
- Imported docs pack: `docs/caresight_hub_docs_pack/`

## Safety Posture

CareSight events use language like `possible_floor_stay` and `medication_routine_likely_observed`. Vision alone must not confirm medication administration, diagnose a condition, or trigger autonomous emergency dispatch. Human confirmation is part of the product boundary.
