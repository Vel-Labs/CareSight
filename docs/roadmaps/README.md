# Roadmaps

Feature-level roadmaps should live here.

Root `ROADMAP.md` is the high-level roadmap index. This folder owns operational routing and detailed roadmap plans.

## Structure

- `ROADMAP.md`: root executive roadmap index.
- `docs/roadmaps/CURRENT_STATE_AND_NEXT.md`: operational source of truth for the next agent.
- `docs/roadmaps/caresight_sprint_pack/`: Codex-ready next-sprint pack for demo consolidation, local drafting, appearance profiles, tracking reliability, multi-camera narrative proof, routine-event demos, and product-shape copy.
- `docs/roadmaps/features/`: detailed feature roadmap files.
- `docs/audits/`: phase and closeout evidence.

## Current Sprint Pack

- [`caresight_sprint_pack/README.md`](caresight_sprint_pack/README.md)
- [`caresight_sprint_pack/00-master-codex-prompt.md`](caresight_sprint_pack/00-master-codex-prompt.md)
- [`caresight_sprint_pack/01-sprint-demo-surface-consolidation.md`](caresight_sprint_pack/01-sprint-demo-surface-consolidation.md)
- [`caresight_sprint_pack/02-sprint-agent-llm-drafting-layer.md`](caresight_sprint_pack/02-sprint-agent-llm-drafting-layer.md)
- [`caresight_sprint_pack/03-sprint-daily-appearance-profiles.md`](caresight_sprint_pack/03-sprint-daily-appearance-profiles.md)
- [`caresight_sprint_pack/04-sprint-tracking-reliability-upgrade.md`](caresight_sprint_pack/04-sprint-tracking-reliability-upgrade.md)
- [`caresight_sprint_pack/05-sprint-multi-camera-narrative-proof.md`](caresight_sprint_pack/05-sprint-multi-camera-narrative-proof.md)
- [`caresight_sprint_pack/06-sprint-routine-event-demo.md`](caresight_sprint_pack/06-sprint-routine-event-demo.md)
- [`caresight_sprint_pack/07-contract-json-pack.md`](caresight_sprint_pack/07-contract-json-pack.md)
- [`caresight_sprint_pack/08-readme-product-shape.md`](caresight_sprint_pack/08-readme-product-shape.md)

Recommended execution order:

```text
01 -> 02 -> 03 -> 04 -> 05 -> 06 -> 07 -> 08
```

Rationale: implementation sprints absorb the contract pieces they consume before runtime behavior. Sprint 07 remains a contract continuity audit after those layers exist, rather than a standalone schema-copying sprint.

Suggested pattern:

```text
features/feature-01-core-primitive.md
features/feature-02-first-integration.md
features/feature-03-working-example.md
features/feature-04-hardening.md
features/feature-05-stretch.md
```
