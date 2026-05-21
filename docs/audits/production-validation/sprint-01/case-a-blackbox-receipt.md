# Blackbox Receipt

CareSight has a complete local audit trail for this possible event: observation, human review, journal entry, and report-only handoff are recorded. The current event status is human_confirmed.

## Proof Chain

- Event status: human_confirmed
- Human review: human_confirmed by Steven
- Journal entries: 1
- Report-only handoffs: 1
- Dashboard includes event: yes
- Alert draft has provenance: yes

## Event Details

- Event ID: evt_d9aa38bdc636459c92ea4e25f665cd0d
- Event type: possible_floor_stay
- Occurred at: 2026-05-20T02:36:31.832047Z
- Camera: living_room
- Zone: floor_zone
- Severity: high
- Confidence: high
- Track IDs: track_5
- Observations: 1

## Boundaries

- SQLite is source of truth; dashboard and alert text are derived outputs.
- CareSight did not dispatch emergency services.
- CareSight did not make a medical diagnosis.
- Blocked actions: autonomous_emergency_dispatch, medical_diagnosis
