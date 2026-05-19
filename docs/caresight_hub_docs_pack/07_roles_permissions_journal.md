# Roles, Permissions, and Care Journal

## Product principle

CareSight becomes valuable when the right event reaches the right person with the right permission level.

The cared-for person should not need to interact with the system.

---

# Role model

## Owner / installer

Can configure cameras, roles, routines, retention, and integrations.

## Family caregiver

Can receive alerts, view event summaries, acknowledge events, initiate FaceTime handoff, and view daily journal.

## Nurse / care worker

Can confirm care routines, add notes, review assigned events, and export relevant care logs.

## Temporary caregiver

Time-limited role for pet sitter, home aide, house sitter, or short-term family support.

## Pet sitter

Can receive pet-related alerts and confirm pet tasks only.

## Emergency contact

Can receive high-severity alerts but may have limited journal access.

---

# Permission examples

## Family caregiver

```json
{
  "role": "family_caregiver",
  "can_receive_alerts": true,
  "can_view_daily_journal": true,
  "can_acknowledge_events": true,
  "can_initiate_facetime": true,
  "can_confirm_medication": false
}
```

## Nurse

```json
{
  "role": "nurse",
  "can_receive_alerts": true,
  "can_view_assigned_subjects": true,
  "can_confirm_medication": true,
  "can_add_care_notes": true,
  "can_export_care_log": true
}
```

## Temporary pet sitter

```json
{
  "role": "temporary_pet_sitter",
  "active_until": "2026-05-21T18:00:00Z",
  "allowed_subject_types": ["pet"],
  "allowed_event_types": ["pet_food_activity_observed", "pet_left_room", "door_activity"],
  "can_view_live_feed": false,
  "can_view_elder_care_notes": false,
  "can_confirm_pet_tasks": true
}
```

---

# Chain of care

Use “chain of care” instead of “chain of custody” for product language.

A chain-of-care record should include:

- what was observed
- when it was observed
- where it was observed
- what evidence supported it
- who was alerted
- who acknowledged it
- who confirmed/dismissed it
- what follow-up note was added

---

# Daily journal design

The journal is the human-readable surface for care history.

## Recommended sections

- Safety events
- Medication routines
- Meals / hydration
- Pet care
- Door/package activity
- Caregiver notes
- Unresolved items

## Example daily journal

```text
CareSight Daily Journal — May 18, 2026

Safety
⚠ 10:22 AM — Possible floor-stay event in Living Room.
  Duration: 31 seconds.
  Confidence: High.
  Alert sent to: Sarah.
  Status: acknowledged at 10:24 AM.

Medication
☐ Morning medication confirmation pending.
  8:03 AM — Medication routine likely observed.
  Evidence: person at medication station, cup/bottle visible.
  Camera: Kitchen counter.
  Status: awaiting confirmation.

Meals / Hydration
• 8:44 AM — Kitchen table activity observed for 12 minutes.

Pet Care
☑ 7:16 AM — Dog food area activity observed.
  Confirmed by: Jamie, temporary pet sitter.

Open Items
- Morning medication requires confirmation.
```

---

# Confirmation wording

Use conservative language before human confirmation.

| System observation | Human confirmation |
|---|---|
| Medication routine likely observed | Nurse confirmed morning medication |
| Pet food activity observed | Pet sitter confirmed dog was fed |
| Possible floor-stay event | Family caregiver acknowledged / dismissed |

---

# Shared Notes strategy

Apple Notes can be used as a shared journal surface, but not as the system database.

Recommended flow:

```text
SQLite event
  → generated daily Markdown
  → optional Apple Shortcut appends to shared Note
  → caregiver confirmation captured in dashboard
  → confirmation written back to SQLite
```

---

# Future care-plan model

A care plan can be represented as routine templates:

```json
{
  "routine_id": "morning_meds",
  "subject_id": "subject_001",
  "name": "Morning medication",
  "expected_window": {"start": "08:00", "end": "09:00"},
  "evidence_required": ["person_in_med_zone", "cup_or_bottle_visible"],
  "confirmation_required_by_role": "nurse_or_family",
  "missed_routine_grace_minutes": 15,
  "escalation_policy": "medium_priority"
}
```
