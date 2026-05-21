# Sprint 04 — Tracking Reliability Upgrade

## Goal

Make floor-stay and missing-off-camera behavior more resilient in multi-person scenes while preserving conservative thresholds, auditability, and no autonomous emergency dispatch.

## Current foundation to preserve

CareSight already has:

- deterministic tracking foundation under `caresight/runtime/tracking/`
- `track_id` event-observation persistence
- same-track dwell evidence for `possible_floor_stay`
- short occlusion grace
- missing-off-camera policy foundation

This sprint hardens the policy and makes severity scaling explainable.

## Product value

Caregiving failures often happen in ambiguous moments: a person lowers to the floor, disappears behind furniture, gets up briefly, falls again, or multiple people cross the same room. The system should avoid spam while surfacing a clear escalation stage to caregivers.

## Non-goals

- No medical diagnosis.
- No injury detection claim.
- No emergency dispatch.
- No fall confirmation from vision alone.
- No identity recognition.
- No aggressive thresholds that generate noisy demos.

## Event language

Allowed:

```text
possible_floor_stay
same tracked person remained low in configured floor zone
early concern
prolonged concern
critical attention recommended
caregiver review required
```

Forbidden:

```text
fall detected
person injured
medical emergency confirmed
911 called
resident cannot get up
```

## Policy model

Use severity and escalation stage separately.

Current `severity` enum can remain:

```text
low
medium
high
```

Add an evidence field:

```json
{
  "escalation_stage": "early_concern",
  "dwell_seconds": 31,
  "same_track_dwell_seconds": 31,
  "occlusion_grace_seconds": 3,
  "dedupe_window_seconds": 90,
  "policy_version": "floor_stay_v1_tracking_reliability"
}
```

Suggested escalation stages:

```text
observe_only
early_concern
prolonged_concern
critical_attention
```

Mapping:

```text
observe_only: below event threshold; no event persisted
early_concern: threshold crossed; awaiting review; severity low/medium depending config
prolonged_concern: longer dwell; severity medium/high
critical_attention: very long dwell or repeated same-track event; severity high; caregiver alert draft emphasized
```

Important: `critical_attention` still does not dispatch emergency services.

## Config

Add or extend floor-stay config:

```json
{
  "floor_stay": {
    "dwell_seconds": 30,
    "prolonged_dwell_seconds": 90,
    "critical_dwell_seconds": 180,
    "occlusion_grace_seconds": 5,
    "dedupe_window_seconds": 90,
    "same_track_required": true,
    "min_person_confidence": 0.35,
    "severity_by_stage": {
      "early_concern": "medium",
      "prolonged_concern": "high",
      "critical_attention": "high"
    }
  }
}
```

Keep defaults conservative and configurable.

## Runtime changes

Update relevant modules:

```text
apps/caresight-hub/caresight/runtime/tracking/state.py
apps/caresight-hub/caresight/events/floor_stay.py
apps/caresight-hub/caresight/events/missing_off_camera.py
apps/caresight-hub/caresight/runtime/config.py
```

Expected behavior:

1. A floor-stay event requires the same `track_id` low in configured floor zone for the threshold.
2. Short occlusion within grace does not reset dwell.
3. Leaving the floor zone beyond grace resets dwell.
4. A get-up/fall-again within dedupe window updates evidence or stages follow-up rather than spamming duplicate events.
5. Repeated prolonged concern can escalate stage but still not dispatch.
6. Multi-person scenes track each candidate separately.
7. Missing-off-camera uses last known track/profile context but avoids identity claims.
8. Every persisted event includes policy version, dwell seconds, and stage.

## Event examples

`possible_floor_stay` evidence should look like:

```json
{
  "raw_video_stays_local": true,
  "model": "yolo26n-mlx",
  "track_id": "track_5",
  "same_track_dwell_seconds": 31,
  "occlusion_grace_seconds": 5,
  "dedupe_window_seconds": 90,
  "escalation_stage": "early_concern",
  "policy_version": "floor_stay_v1_tracking_reliability",
  "not_claimed": ["fall_confirmed", "injury_detected", "medical_emergency"]
}
```

`missing_off_camera_extended` evidence should look like:

```json
{
  "raw_video_stays_local": true,
  "track_id": "track_5",
  "last_seen_camera_id": "kitchen",
  "last_seen_room": "Kitchen",
  "last_seen_at": "2026-05-20T02:20:00Z",
  "missing_seconds": 300,
  "appearance_profile_id": "appearance_2026_05_20_001",
  "continuity_claim": "likely_same_tracked_person",
  "policy_version": "missing_off_camera_v1_tracking_reliability",
  "not_claimed": ["person_lost", "medical_emergency", "named_identity"]
}
```

## Contract work

If existing `care-event.schema.json` already permits evidence `additionalProperties`, do not broaden event type semantics unless necessary.

Add valid examples:

```text
contracts/examples/valid/possible-floor-stay.tracking-reliability.event.json
contracts/examples/valid/missing-off-camera.tracking-reliability.event.json
```

Add invalid examples:

```text
contracts/examples/invalid/floor-stay-emergency-dispatch.event.json
contracts/examples/invalid/missing-off-camera-named-identity.event.json
contracts/examples/invalid/floor-stay-fall-confirmed-without-human.event.json
```

## Dashboard and review packet changes

Show stage but keep language bounded:

```json
{
  "event_type": "possible_floor_stay",
  "severity": "high",
  "escalation_stage": "prolonged_concern",
  "caregiver_copy": "Same tracked person remained low in the configured Living Room floor zone long enough to require human review."
}
```

Do not show “fall detected.”

## Tests

Add or extend:

```text
apps/caresight-hub/tests/test_tracking_state.py
apps/caresight-hub/tests/test_floor_stay.py
apps/caresight-hub/tests/test_missing_off_camera.py
apps/caresight-hub/tests/test_v0_floor_stay_live.py
```

Required cases:

1. Same-track dwell emits event at threshold.
2. Different track entering floor zone does not inherit dwell.
3. Short occlusion preserves dwell.
4. Long occlusion resets dwell.
5. Dedupe suppresses duplicate same-track event within window.
6. Prolonged dwell escalates `escalation_stage` without dispatch.
7. Critical attention keeps blocked actions.
8. Multi-person scene tracks candidates independently.
9. Missing-off-camera includes last seen context and no identity claim.
10. All event evidence includes policy version.
11. Dashboard uses bounded wording.
12. Alert draft does not say fall, injury, or emergency.

## Docs

Update:

```text
docs/architecture/ARCHITECTURE.md
docs/cli/COMMANDS.md
docs/roadmaps/CURRENT_STATE_AND_NEXT.md
CHANGELOG.md
docs/audits/YYYY-MM-DD-tracking-reliability-upgrade.md
```

`DECISIONS.md` only needed if adding new state semantics beyond evidence fields.

## Definition of done

- Floor-stay logic is same-track, stage-aware, and deduped.
- Missing-off-camera remains bounded and non-diagnostic.
- Tests cover multi-person and occlusion edge cases.
- No escalation path triggers emergency dispatch.
- `npm run check` passes.

## Pasteable Codex prompt

```text
Implement Sprint 04 Tracking Reliability Upgrade. Harden same-track floor-stay dwell, occlusion grace, dedupe, multi-person independence, missing-off-camera context, and stage-aware evidence. Keep severity enum low/medium/high and add escalation_stage in evidence unless a contract change is truly necessary. Do not claim fall, injury, emergency, or identity. Add valid/invalid contract examples around tracking evidence and forbidden claims. Update dashboard/review/alert wording to show early_concern/prolonged_concern/critical_attention with bounded language. Tests must cover same-track dwell, different-track isolation, short/long occlusion, dedupe, severity stage, multi-person scenes, missing-off-camera, and blocked actions. Update docs, changelog, CLI docs if needed, and audit receipt. Run npm run check.
```
