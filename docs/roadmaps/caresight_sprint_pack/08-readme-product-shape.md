# CareSight Product Shape and README Copy

## Recommended README positioning

Use this as an insert for the root `README.md` or hackathon submission narrative.

```markdown
## Product Vision

CareSight is a local-first care awareness hub for families and caregiver teams. It runs on Apple Silicon, observes configured household care signals with local vision models, stores structured events in SQLite, and helps permissioned humans review what happened.

CareSight is designed for peace of mind without cloud surveillance by default. A Mac mini in the home can run the core loop locally:

```text
camera input
  -> YOLO26 MLX local perception
  -> deterministic care-event rules
  -> SQLite blackbox memory
  -> human review
  -> journal and caregiver alert draft
  -> optional OBS / FaceTime handoff
```

The goal is not to replace caregivers, doctors, or emergency services. The goal is continuity: a clear local record of what CareSight observed, which policy created the event, who reviewed it, what was drafted, and which actions remained blocked.

For families caring for elders, children, pets, or a home while away, CareSight can provide a bounded local “black box” for care context: possible floor-stay events, routine windows likely observed, missing-off-camera concerns, caregiver alerts, daily journal entries, and calm handoff summaries.
```

## Stronger sales pitch

```markdown
CareSight brings local AI into the home care loop without asking families to accept cloud video as the default. A low-cost Apple Silicon Mac can run the vision model, language drafts, SQLite memory, dashboard, and handoff tools locally. When something important happens, CareSight does not pretend to be a doctor or dispatcher. It creates a structured record, asks an authorized human to review it, preserves the audit trail, and prepares calm next-step drafts for the caregiver.

The product promise is simple: observe locally, record carefully, escalate responsibly.
```

## Hackathon demo story

```text
1. Camera sees the living room locally.
2. YOLO26 MLX detects a person in the configured floor/low zone.
3. Deterministic same-track dwell policy emits possible_floor_stay.
4. SQLite stores the event, observation, track id, snapshot path, blocked actions, and provenance.
5. Human reviewer confirms or dismisses.
6. CareSight creates a journal row and report-only handoff row.
7. Dashboard focuses on the selected proof event while stale rows remain in backlog.
8. Local Gemma drafts caregiver copy from SQLite JSON only.
9. Optional OBS scene switch and FaceTime handoff present the event to a human.
10. Optional TTS calmly reads a bounded summary.
```

## Product ethos

CareSight should feel serious, calm, and trustworthy.

Use these words often:

```text
local-first
bounded
auditable
human-confirmed
caregiver-aware
report-only
draft-first
non-destructive
SQLite-backed
privacy-preserving
configured care event
likely observed
possible concern
```

Avoid these words unless carefully qualified:

```text
medical device
diagnosis
fall detector
emergency dispatch
HIPAA compliant
surveillance
identity recognition
medication taken
hydration completed
```

## Broader caregiver ecosystem value-adds

Future paid or managed product layers can include:

1. Installation and hardware packaging.
2. Managed updates for local models and contracts.
3. Camera compatibility and calibration support.
4. Care plan templates for family caregivers.
5. Multi-caregiver role and permission setup.
6. Local dashboard polish and mobile companion views.
7. OBS/FaceTime handoff templates.
8. Apple Notes, Reminders, Shortcuts, and iMessage workflows.
9. Training mode for caregivers and temporary care workers.
10. Facility/foster/pet-care variants with different contracts.
11. Audit export packages for family review.
12. Offline-first continuity reports.

Keep the public baseline inspectable. Sell reliability, setup, packaging, support, updates, workflows, and peace of mind.

## Buyer personas

### Family elder-care household

Needs:

- possible floor-stay awareness
- routine reminders and likely-observed logs
- journal continuity
- alert drafts
- privacy assurances

CareSight promise:

> A local care record that helps the family notice and review important events without streaming private home video to the cloud by default.

### Parent or guardian

Needs:

- local home awareness
- bounded alerts
- no creepy identity model
- reliable audit trail

CareSight promise:

> Configured local observations and reviewable event records, not an always-watching cloud surveillance product.

### Pet-care household

Needs:

- food/water/pet-door routine observations
- caregiver handoff notes
- local snapshots or event records

CareSight promise:

> Local routine context and daily logs for pets and caregivers.

### Temporary caregiver / care worker

Needs:

- scoped permissions
- clear handoff packets
- daily journal
- not responsible for operating complex software during events

CareSight promise:

> A bounded local event inbox and journal that supports the care plan without giving agents authority over care decisions.

## Suggested repo tagline alternatives

```text
CareSight: local-first care awareness for families.
CareSight: observe locally, record carefully, escalate responsibly.
CareSight: a SQLite-backed home care blackbox for human-reviewed events.
CareSight: local AI care context without cloud surveillance by default.
```

## Demo closing line

```text
CareSight does not replace a caregiver. It gives caregivers a local, auditable memory of what happened and a safer way to decide what to do next.
```
