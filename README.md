# CareSight Hub

CareSight Hub is a local-first caregiver awareness system for homes where peace of mind matters: an aging parent living alone, a child at home, a pet, or any loved one you want to know is okay without turning the home into a cloud surveillance product.

The long-term vision is simple: a small Mac mini-class appliance that runs local vision, text-to-speech, and language models, records structured care events, preserves a non-destructive SQLite blackbox, and creates caregiver handoff paths when attention may be needed.

CareSight does not try to replace a caregiver, diagnose a condition, or dispatch emergency services. It gives the home a local memory: what was observed, when it happened, what evidence exists, who reviewed it, what was journaled, and what draft alert or handoff was prepared.

The current hackathon build uses the project scaffold as the repo backbone for governance, contracts, quality gates, and agent-safe collaboration, then keeps the Python/MLX runtime in a separate app boundary.

CareSight is not a medical device, certified fall detector, alarm service, emergency dispatch product, or HIPAA-compliant clinical system. The MVP creates local care observations that authorized humans can acknowledge, confirm, or dismiss.

## Why CareSight Exists

Many care moments are stressful because the people responsible for helping do not have continuity. They may not know when something happened, where someone was last seen, what they were wearing, whether an event was already reviewed, or what the next appropriate handoff should be.

CareSight is designed around that gap.

It acts like a local black box for care-relevant observations: raw video stays local, models run locally, SQLite remains the source of truth, and every event has an audit trail. The goal is not to create fear or automate authority. The goal is to preserve context so help is easier to coordinate when something feels wrong.

In a perfect-world product footprint, this runs on the lowest-cost practical Apple hardware, such as a Mac mini, and becomes a quiet home appliance for local care awareness.

## Project Ethos

CareSight is being built in public because trust, safety, and caregiving should be accessible to people who are willing to learn, assemble, and run local tools for their own families. The open-source hackathon build should be capable enough to help real households experiment with local-first care awareness without waiting for a commercial gatekeeper.

That does not mean every future product layer must be free or unmanaged. A sustainable CareSight business would likely focus on reliable packaging, installation, support, managed updates, hardware compatibility, caregiver workflows, and other value-added services. The baseline loop should remain understandable and inspectable: observe locally, create bounded events, ask humans to confirm, journal what happened, and preserve auditability.

## License

CareSight Hub is licensed under `AGPL-3.0-only` for the public hackathon repository.

This posture is deliberate. The current runtime uses the `thewebAI/yolo-mlx` Git submodule under `apps/caresight-hub/vendor/yolo-mlx`, which is also licensed under `AGPL-3.0-only`. For the hackathon build, that keeps the local-first baseline open, inspectable, and reciprocal while still leaving room for future packaged services, support, managed updates, hardware compatibility work, and other value-added product layers.

See `LICENSE`, `NOTICE.md`, and `docs/legal/LICENSE_NOTES.md`.

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

1. Clone with submodules:

```bash
git clone --recurse-submodules https://github.com/Vel-Labs/CareSight.git
cd CareSight
```

2. Read `AGENTS.md`.
3. Read `docs/project/PROJECT_BRIEF.md`.
4. Read `docs/architecture/REPO_BOUNDARIES.md`.
5. Read `docs/roadmaps/CURRENT_STATE_AND_NEXT.md`.
6. Run the quality gate:

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
