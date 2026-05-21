# CareSight Sprint Pack

Prepared for the next CareSight hackathon/product sprint on 2026-05-20.

This pack is written to be pasted directly into Codex sessions or copied into `docs/roadmaps/features/` and related repo documentation. It assumes the current repo state where:

- `contracts/` is canonical project truth.
- `packages/core/` validates contracts and governance.
- `apps/caresight-hub/` owns Python runtime behavior.
- SQLite remains the blackbox source of truth.
- Agents, dashboards, alerts, Apple Notes, iMessage, OBS, FaceTime, and TTS are downstream presentation/drafting/action layers.

## Files

1. `00-master-codex-prompt.md` — one comprehensive prompt for the whole sprint.
2. `01-sprint-demo-surface-consolidation.md` — focused demo/dashboard/review/blackbox receipt sprint.
3. `02-sprint-agent-llm-drafting-layer.md` — Gemma MLX, local draft schemas, action gateway, TTS, and tool boundaries.
4. `03-sprint-daily-appearance-profiles.md` — non-biometric daily appearance continuity.
5. `04-sprint-tracking-reliability-upgrade.md` — same-track dwell, occlusion grace, dedupe, escalation stages.
6. `05-sprint-multi-camera-narrative-proof.md` — explicit local multi-camera proof without cloud/LAN discovery.
7. `06-sprint-routine-event-demo.md` — medication/hydration routine demo without overclaiming.
8. `07-contract-json-pack.md` — contract continuity audit source pack for checking absorbed schema work.
9. `08-readme-product-shape.md` — product story, README copy, value-adds, and demo narrative.

## Recommended execution order

```text
01 -> 02 -> 03 -> 04 -> 05 -> 06 -> 07 -> 08
```

Use `07-contract-json-pack.md` as a contract continuity audit after the implementation layers have absorbed the contract pieces they consume. Sprint 01 owns `human-review-packet` and `blackbox-receipt`; Sprint 02 owns `agent-draft`, `agent-action-request`, `tts-utterance`, and forbidden claim/action vocabulary; Sprint 03 owns `appearance-profile`.

## Global rule

Do not make CareSight more impressive by making it less safe. The winning product shape is boring, local, auditable, and human-authority preserving.
