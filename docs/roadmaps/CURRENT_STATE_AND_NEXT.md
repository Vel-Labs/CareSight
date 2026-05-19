# Current State and Next

## Current State

CareSight Hub has adopted the project scaffold as its governance backbone:

- `contracts/` owns canonical care schemas and examples.
- `packages/core/` validates the contract corpus.
- `tests/` runs the shared local quality gate.
- `docs/hackathon/`, `docs/roadmaps/`, `docs/architecture/`, and `docs/references/` now route the imported docs pack.
- `apps/caresight-hub/` exists as the Python runtime boundary.
- YOLO26 MLX is installed under `apps/caresight-hub/vendor/yolo-mlx`.
- `yolo26n.npz` is converted and verified.
- Image and live webcam smoke tests work with usable visual quality, FPS/settings overlay, and COCO labels.
- Smoke checkpoint: `docs/audits/2026-05-18-yolo26-mlx-smoke-checkpoint.md`.
- v0 eventization implementation: `docs/audits/2026-05-18-v0-eventization-implementation.md`.
- v0 review and acknowledgement CLI: `apps/caresight-hub/scripts/v0_review_events.py`.
- Durable CLI registry: `docs/cli/COMMANDS.md`.

## Immediate Next Action

Prove the v0 review and acknowledgement loop:

```text
possible_floor_stay event
  -> local event inbox
  -> human-readable summary
  -> human confirm/dismiss
  -> SQLite status update
  -> journal entry
  -> agent-ready handoff record
```

## Recommended Workstreams

- Contract steward: keep `possible_floor_stay` aligned with `contracts/schemas/care-event.schema.json`.
- Runtime steward: add the Python v0 loop behind the existing `apps/caresight-hub/` boundary.
- Storage steward: add the minimal SQLite schema and one insert/readback path.
- Review steward: keep `v0_review_events.py` human-readable, reviewer-gated, and documented in `docs/cli/COMMANDS.md`.
- Dashboard steward: expose event timeline, model/FPS panel, and journal without becoming canonical truth.
- Audit steward: keep `DECISIONS.md`, `CHANGELOG.md`, roadmap docs, and quality-gate evidence synchronized.

## v0 Resolution Order

1. Run `python apps/caresight-hub/scripts/v0_floor_stay_live.py`.
2. Tune `apps/caresight-hub/config/v0.local.json` if the floor zone is too large or too small.
3. Confirm `event_persisted` prints once per continuous floor-zone dwell.
4. Inspect `apps/caresight-hub/data/caresight-v0.sqlite3`.
5. Run `python apps/caresight-hub/scripts/v0_review_events.py list`.
6. Run `python apps/caresight-hub/scripts/v0_review_events.py show <event_id>`.
7. Confirm or dismiss with an authorized reviewer.
8. Verify `event_reviews`, `journal_entries`, and `agent_handoffs` rows exist.
9. Promote the verified command and observed output into a follow-up audit receipt.

## Validation Before Advancing

```bash
npm run validate:scaffold
npm run validate:contracts
npm run test:focused
npm test
npm run typecheck
npm run py:check
npm run check
```

## Do Not Start Yet

- Ring/Nest adapters.
- HIPAA claims.
- autonomous emergency dispatch.
- cloud raw-video upload defaults.
- multi-camera support before v0 works.
