# OBS Scene Plan

## Scene: CareSight Idle

Sources:

- Text: “CareSight Hub — Monitoring Locally”
- Browser Source: dashboard health page
- Text: camera status

## Scene: Living Room Event

Sources:

- Video source: Living Room camera
- Text: event title
- Text: confidence/severity
- Text: “Raw video local”
- Optional browser source: event timeline

## Scene: Medication Station Event

Sources:

- Video source: Kitchen/Medication camera
- Text: routine title
- Text: confirmation status
- Browser source: daily journal section

## Scene: Pet Care Event

Sources:

- Video source: pet area camera
- Text: pet event summary
- Text: temporary caregiver status

## Scene switching rules

- `possible_floor_stay` → Living Room Event
- `medication_routine_likely_observed` → Medication Station Event
- `pet_food_activity_observed` → Pet Care Event
- no active event for 5 minutes → CareSight Idle
