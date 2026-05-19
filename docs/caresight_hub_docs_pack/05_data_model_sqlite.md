# SQLite Data Model

## Why SQLite

SQLite is the right MVP database because it is local, portable, inspectable, lightweight, and does not require a separate server. It can hold structured event records, JSON payloads, audit logs, and searchable journal text.

## Source-of-truth principle

SQLite should be the canonical care record. Apple Notes, Markdown files, dashboard views, and messages are human-facing surfaces generated from the database.

```text
SQLite = source of truth
Daily Markdown/Apple Notes = human-readable mirror
Dashboard = operational view
OBS/FaceTime = live context view
```

---

# Core entities

## people

Caregivers, nurses, temporary caregivers, pet sitters, owners, residents when appropriate.

## subjects

The people or pets being cared for. Do not require face identity in the MVP.

## cameras

Camera source configuration and room/area metadata.

## zones

Semantic regions inside camera views.

Examples:

- living room floor zone
- medication station
- kitchen table
- pet bowl area
- front door

## routines

Expected windows and evidence requirements.

Examples:

- morning medication
- breakfast check
- pet feeding
- evening room check

## events

The main care event records.

Examples:

- possible_floor_stay
- medication_routine_likely_observed
- pet_food_activity_observed
- camera_offline
- missed_routine

## event_observations

Frame/object-level evidence attached to an event.

## journal_entries

Human-readable summaries linked to events.

## alerts

Messages or actions sent to caregivers.

## audit_log

Who confirmed, dismissed, exported, or modified data.

---

# Recommended schema

See `templates/sqlite_schema.sql` for a copy-paste schema.

## Schema notes

- Store bounding boxes and evidence as JSON text.
- Store timestamps as ISO 8601 UTC strings.
- Use foreign keys.
- Keep raw frames/clips out of the core database unless you intentionally add retention rules.
- Use confirmation status on events and journal entries.

---

# Event status lifecycle

```text
observed
  → likely
    → alert_sent
      → acknowledged
        → confirmed
        → dismissed
        → unresolved
```

Recommended statuses:

- `observed`
- `likely`
- `alert_sent`
- `acknowledged`
- `confirmed`
- `dismissed`
- `unresolved`
- `expired`

---

# Example event JSON

```json
{
  "event_type": "possible_floor_stay",
  "subject_id": "subject_001",
  "camera_id": "living_room_cam",
  "zone_id": "living_room_floor",
  "timestamp": "2026-05-18T15:22:04Z",
  "duration_seconds": 34,
  "severity": "high",
  "confidence": 0.87,
  "confidence_label": "high",
  "evidence": {
    "objects": ["person"],
    "temporal_threshold_met": true,
    "movement_low": true,
    "raw_video_uploaded": false
  },
  "recommended_actions": [
    "text_primary_caregiver",
    "switch_obs_event_view",
    "offer_facetime"
  ],
  "status": "alert_sent"
}
```

---

# Daily journal generation

A journal entry should be generated from events, not manually maintained as the canonical data.

Example:

```text
CareSight Daily Journal — 2026-05-18

Medication
☐ Morning medication confirmed
  8:03 AM — Medication routine likely observed.
  Evidence: person at medication station, bottle/cup visible.
  Status: awaiting confirmation.

Safety
⚠ 10:22 AM — Possible floor-stay event in living room.
  Duration: 31 seconds.
  Alert sent to: Sarah.
  Status: acknowledged.

Pet Care
☑ 7:16 AM — Dog food area activity observed.
  Confirmed by: temporary pet sitter.
```

---

# Future search

SQLite FTS5 can index journal text, event summaries, and care notes for queries such as:

- “medicine this week”
- “floor-stay events”
- “pet feeding by sitter”
- “unconfirmed routines”

---

# Retention model

Recommended MVP retention:

- Event metadata: retained locally until deleted by owner.
- Snapshots/clips: disabled by default or short retention only.
- Raw video: not stored by default.
- Journal entries: retained locally and exportable.

Future versions should support configurable retention and deletion.
