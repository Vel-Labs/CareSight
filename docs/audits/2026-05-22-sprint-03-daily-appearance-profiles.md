# Sprint 03 Daily Appearance Profiles

Date: 2026-05-22

## Scope

Started Sprint 03 as a bounded, local-first daily appearance profile lane. The implementation stores non-biometric same-day appearance context in SQLite, derives coarse clothing descriptors from real event observations plus local snapshots, and can collect capped quality-gated periodic appearance samples for stronger same-day support.

This receipt does not claim biometric identity, face recognition, named-person identification, diagnosis, fall detection, medical-device behavior, HIPAA compliance, or autonomous emergency dispatch.

## Files

- `contracts/schemas/appearance-profile.schema.json`
- `contracts/examples/valid/appearance-profile.daily-resident.json`
- `contracts/examples/invalid/appearance-profile-biometric-identity.json`
- `contracts/examples/invalid/appearance-profile-cross-day-identity.json`
- `contracts/examples/invalid/appearance-profile-face-match.json`
- `contracts/examples/invalid/appearance-profile-named-role.json`
- `apps/caresight-hub/caresight/storage/migrations/003_appearance_profiles.sql`
- `apps/caresight-hub/caresight/runtime/appearance/`
- `apps/caresight-hub/scripts/care_console.py`
- `apps/caresight-hub/scripts/v0_floor_stay_live.py`
- `apps/caresight-hub/tests/test_appearance_profiles.py`
- `apps/caresight-hub/tests/test_sqlite_store.py`
- `apps/caresight-hub/tests/test_care_console.py`

## Dynamic Proof

The proof used a copied SQLite database, not the live runtime database:

```bash
cp /Users/steven/Workspace/40_Code/hackathons/CareSight/apps/caresight-hub/data/caresight-v0.sqlite3 /tmp/caresight-sprint03-proof.sqlite3
/Users/steven/Workspace/40_Code/hackathons/CareSight/apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/care_console.py --db /tmp/caresight-sprint03-proof.sqlite3 appearance-profile derive-from-event evt_67f81ae3d0df49fd92832766b94be216
/Users/steven/Workspace/40_Code/hackathons/CareSight/apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/care_console.py --db /tmp/caresight-sprint03-proof.sqlite3 appearance-profile show appearance_2026_05_22_track_29
```

Observed receipt fields:

- `event_id`: `evt_67f81ae3d0df49fd92832766b94be216`
- `observation_id`: `30`
- `track_id`: `track_29`
- `snapshot_path`: `/Users/steven/Workspace/40_Code/hackathons/CareSight/apps/caresight-hub/data/snapshots/evt_67f81ae3d0df49fd92832766b94be216.jpg`
- `appearance_profile_id`: `appearance_2026_05_22_track_29`
- `descriptor_source`: `runtime_observation`
- `descriptor_status`: `available`
- `identity_boundary`: `non_biometric_daily_appearance_only`
- `role_assignment`: `unknown_person`
- `upper_body_color`: `light gray`
- `lower_body_color`: `gray`
- summary: `unknown-person profile for today; light gray upper clothing; gray lower clothing; last seen in Living Room.`

Follow-up operator feedback showed single event frames can be a poor appearance source when the event is prone, occluded, or bottom-truncated. The branch now fails closed for those poor frames and adds periodic quality-gated sample support so daily profiles can aggregate better frames over time.

The descriptor path now also carries bounded accessory-like attributes when image quality supports them:

- `headwear`: coarse color only; no face recognition or named-person identity.
- `footwear`: coarse color only; unavailable when feet are not visible or the bbox is bottom-truncated.

Still images can be checked without writing profile rows:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python \
  apps/caresight-hub/scripts/care_console.py \
  appearance-profile describe-image /tmp/person.ppm --bbox 20,20,80,90
```

## Periodic Sample Support

Live runs can now capture local appearance samples without waiting for an event:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python \
  apps/caresight-hub/scripts/v0_floor_stay_live.py \
  --camera-id living_room \
  --max-seconds 600 \
  --appearance-sampling \
  --appearance-sample-interval-seconds 20 \
  --appearance-max-samples-per-profile 5
```

Sample rows are stored in `appearance_profile_samples` and capped per profile/day by retained quality rank. Local sample files live under `apps/caresight-hub/data/appearance-samples/`; lower-ranked samples are deleted during pruning. `care_console.py appearance-profile summarize-today` reports support ratios such as `blue upper clothing: 2/3 good samples`.

This proves the Sprint 03 path can read real event feeds and local snapshots while avoiding one-frame overclaims. It is not a seeded appearance fixture.

## Boundaries

- Profiles expire within the same-day local scope.
- Appearance samples are capped per profile/day to avoid unbounded file growth.
- Role assignment is bounded to daily roles such as `resident_primary`, `caregiver_known`, `visitor_unknown`, or `unknown_person`.
- Agents and dashboards may show bounded appearance context, but SQLite records and authorized human review remain the source of truth.
- Missing, unreadable, or invalid image evidence returns unavailable descriptor state instead of hallucinated clothing attributes.

## Remaining Gates

- Human assign/confirm any resident, caregiver, or visitor role before role-specific caregiver copy uses it.
- Run the same derivation on an operator-approved live/demo event database before calling Sprint 03 production-ready.
- Review dashboard wording with a human to confirm it stays useful and bounded.
- Keep Sprint 04 tracking reliability work separate from named identity or cross-day matching.
