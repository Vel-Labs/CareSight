# Event Engine, Confidence, and Escalation

## Core principle

The engine should not simply report detections. It should produce care-relevant events from repeated observations, zones, routines, and time thresholds.

```text
object detections + zones + time + routine config + history = care event
```

---

# Event types for MVP

## possible_floor_stay

A person appears low in a configured floor zone for longer than a threshold.

Evidence:

- person detected
- floor zone match
- duration threshold crossed
- low movement or persistent position
- not in excluded bed/couch zone

Recommended language:

> Possible floor-stay event in Living Room. Person has been low in the floor zone for 31 seconds. Raw video remains local.

## medication_routine_likely_observed

A person is present at a medication station during the expected routine window, with optional object evidence such as bottle/cup.

Evidence:

- person in medication zone
- routine time window active
- object evidence if available
- presence duration threshold crossed

Recommended language:

> Medication routine likely observed. Evidence: person present at medication station, cup/bottle visible. Awaiting caregiver confirmation.

## pet_food_activity_observed

A dog/cat is present near a configured food/water zone.

Evidence:

- dog/cat detected
- pet bowl zone match
- duration threshold crossed

Recommended language:

> Pet food area activity observed. Dog present near bowl for 42 seconds.

---

# Future event types

- missed_routine
- no_motion_after_expected_window
- camera_offline
- package_arrived
- door_activity
- unsafe_zone_entry
- walker_not_near_chair
- hydration_station_activity
- caregiver_arrival_departure
- resident_room_check

---

# Confidence scoring

Use a transparent weighted score. Do not hide behind the model confidence alone.

## Components

```text
vision confidence
+ zone confidence
+ temporal confidence
+ routine confidence
+ history confidence
+ confirmation state
= event confidence
```

## Example scoring

```python
score = (
    0.35 * vision_score +
    0.20 * zone_score +
    0.20 * temporal_score +
    0.15 * routine_score +
    0.10 * history_score
)
```

## Labels

- `low`: score < 0.50
- `medium`: 0.50–0.75
- `high`: > 0.75

---

# Severity vs confidence

Confidence and severity are not the same.

Examples:

- High confidence, low severity: pet food activity observed.
- Medium confidence, high severity: possible floor-stay event.
- Low confidence, medium severity: medication evidence unclear.

## Severity levels

- `info`
- `low`
- `medium`
- `high`
- `urgent`

---

# Escalation ladder

```text
Level 0 — observe only
Level 1 — journal entry
Level 2 — notify low priority
Level 3 — notify and request acknowledgement
Level 4 — escalate to secondary caregiver if no acknowledgement
Level 5 — urgent call/FaceTime handoff prompt
```

## MVP policy

```yaml
possible_floor_stay:
  severity: high
  min_confidence: 0.65
  actions:
    - create_journal_entry
    - show_dashboard_alert
    - notify_primary_caregiver
    - switch_obs_event_view
    - offer_facetime

medication_routine_likely_observed:
  severity: medium
  min_confidence: 0.60
  actions:
    - create_journal_entry
    - request_confirmation

pet_food_activity_observed:
  severity: low
  min_confidence: 0.50
  actions:
    - create_journal_entry
    - notify_temporary_caregiver_if_enabled
```

---

# De-duplication

Avoid spamming caregivers.

Recommended rules:

- Collapse repeated events of same type/camera/zone within a cooldown period.
- Update the existing event duration instead of creating a new event every frame.
- Require event resolution before re-alerting.

Example:

```text
possible_floor_stay cooldown: 5 minutes
medication_routine cooldown: 1 routine window
pet_food_activity cooldown: 30 minutes
```

---

# Human confirmation

CareSight should separate observation from confirmation.

```text
Model observed evidence
  → event likely
    → caregiver/nurse confirms or dismisses
      → audit log records action
```

Recommended statuses:

- `awaiting_confirmation`
- `confirmed`
- `dismissed_false_positive`
- `acknowledged_not_confirmed`
- `resolved`

---

# Agent validation

Gemma/OpenClaw can help summarize and recommend an action, but the rules engine should own escalation thresholds.

Recommended LLM output shape:

```json
{
  "caregiver_summary": "Possible floor-stay event in Living Room. Person has been low in the floor zone for 31 seconds.",
  "recommended_action": "notify_primary_caregiver",
  "requires_human_confirmation": true,
  "allowed_actions": ["notify_primary_caregiver", "create_journal_entry", "offer_facetime"]
}
```

The agent should never invent evidence not present in event JSON.
