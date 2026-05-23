# Sprint 03 Validation Checklist

Date: 2026-05-22

Status: implementation-ready, not production-validated.

This checklist covers Sprint 03 Daily Appearance Profiles only. It must stay bounded to local-first caregiver awareness, possible events, and human review. It must not claim medical-device behavior, HIPAA compliance, fall detection, diagnosis, biometric identity, named-person identification, cross-day identity, or autonomous emergency dispatch.

## Merge Readiness

- [x] Appearance-profile contract, valid example, and invalid forbidden-claim examples exist.
- [x] Contract corpus includes `appearance-profile`.
- [x] SQLite migration adds same-day appearance profiles, observations, and capped samples.
- [x] Runtime descriptor path reads frames or local snapshots dynamically instead of seeded appearance fixtures.
- [x] Descriptor path fails closed for missing, unreadable, invalid, or low-quality prone image evidence.
- [x] CLI documents and exposes `appearance-profile list`, `show`, `list-samples`, `summarize-today`, `describe-image`, `derive-from-event`, and `assign-role`.
- [x] `describe-image` is read-only and does not write profile rows.
- [x] Live loop can collect capped, quality-gated periodic appearance samples without waiting for a care event.
- [x] Dashboard/agent context uses bounded daily appearance language and keeps SQLite as source of truth.
- [x] `npm run check` passes on the Sprint 03 branch.

## Human Review Gates

- [ ] Operator reviews at least 10 still images across lighting, sitting, standing, partial, and prone-ish postures.
- [ ] Operator confirms whether upper-body color support is useful enough for caregiver awareness.
- [ ] Operator confirms whether lower-body color support is useful enough when visible.
- [ ] Operator confirms whether headwear should remain informational only or contribute to continuity confidence.
- [ ] Operator confirms whether footwear should remain informational only or contribute to continuity confidence.
- [ ] Operator reviews dashboard wording and summary wording for usefulness and safety boundaries.
- [ ] Operator assigns any resident/caregiver/visitor role with `assign-role` before role-specific copy is used.
- [ ] Operator approves retained-sample count and file-retention behavior after a longer run.

## Dynamic Proof Gates

- [ ] Run still-image descriptor checks against operator-selected local images:

```bash
python apps/caresight-hub/scripts/care_console.py \
  appearance-profile describe-image /tmp/person.ppm --bbox 20,20,80,90
```

- [ ] Run event derivation on a copied demo database, not the live DB:

```bash
cp apps/caresight-hub/data/caresight-v0.sqlite3 /tmp/caresight-sprint03-validation.sqlite3
python apps/caresight-hub/scripts/care_console.py \
  --db /tmp/caresight-sprint03-validation.sqlite3 \
  appearance-profile derive-from-event <event_id>
```

- [ ] Run longer visible live sampling with bounded retention:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python \
  apps/caresight-hub/scripts/v0_floor_stay_live.py \
  --camera-id living_room \
  --max-seconds 600 \
  --appearance-sampling \
  --appearance-sample-interval-seconds 20 \
  --appearance-max-samples-per-profile 5 \
  --appearance-min-quality-score 0.62
```

- [ ] Summarize same-day sample support:

```bash
python apps/caresight-hub/scripts/care_console.py \
  appearance-profile summarize-today --active-date 2026-05-22
```

- [ ] Inspect retained sample records and verify stored snapshot files are capped:

```bash
python apps/caresight-hub/scripts/care_console.py \
  appearance-profile list-samples <appearance_profile_id>
```

## Quality Gates To Tune

- [ ] Minimum detection confidence: current implementation rejects below `0.45`.
- [ ] Minimum sample quality score: default operator command uses `0.62`.
- [ ] Retained sample count per profile/day: default operator command uses `5`.
- [ ] Headwear descriptor behavior: coarse color only; returns unknown for likely skin/hair-like hues.
- [ ] Footwear descriptor behavior: only available when lower bbox region is visible and not bottom-truncated.
- [ ] Summary support ratio threshold for caregiver-facing wording: not yet product-decided.

## Merge Notes

- This branch is ready for merge preparation after Sprint 02 lands, but should not be called production-ready until the unchecked human and dynamic proof gates above are completed.
- Before merging, rebase or merge the updated Sprint 02 branch/main into this worktree and rerun `npm run check`.
- Do not resolve future conflicts by dropping Sprint 02 production-validation receipts or live-handoff status docs.
- Do not merge active OBS troubleshooting changes into Sprint 03 unless the human explicitly coordinates that lane.

