# Human Review Packet

CareSight recorded a possible event in Living Room.
A human should use the local record and care plan before deciding what to do next.

## At a Glance

- Event: Possible Floor Stay in Living Room
- Current status: human_confirmed
- Latest human review: human_confirmed by Steven
- Evidence: 1 observation, track track_5
- Snapshot: apps/caresight-hub/data/snapshots/evt_d9aa38bdc636459c92ea4e25f665cd0d.jpg

## Suggested Next Step

This event has already been human-confirmed. Review the snapshot and journal if more context is needed.

## Boundaries

- CareSight did not dispatch emergency services.
- CareSight did not make a medical diagnosis.
- SQLite is source of truth; this message is a readable summary of the local audit record.

## Audit Details

- Event ID: evt_d9aa38bdc636459c92ea4e25f665cd0d
- Source fields: events, event_observations, event_reviews, journal_entries, agent_handoffs
- Available human actions: confirm, dismiss, needs_followup
- Blocked actions: autonomous_emergency_dispatch, medical_diagnosis
