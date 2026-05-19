# Project Brief

## Project Name

CareSight Hub

## One-Liner

CareSight Hub is a local-first care event engine that uses YOLO26 MLX on Apple Silicon to observe possible safety and routine events, store them locally, and alert permissioned caregivers.

## Problem

Home care and delegated caregiving often depend on someone noticing a safety issue, remembering a routine, or manually reporting what happened. Many camera products default to surveillance or cloud video instead of structured local care memory.

## Solution

Build a Mac-based hub that consumes one local camera feed, runs YOLO26 MLX locally, converts observations into bounded care events, stores structured records in SQLite, creates a daily journal, and escalates to authorized humans.

## Primary Users

- Family caregivers.
- Care workers or temporary caregivers who need scoped awareness.
- The cared-for person, who should not need to operate the system during an event.

## MVP

- Run one camera through YOLO26 MLX on Apple Silicon.
- Create `possible_floor_stay` and `medication_routine_likely_observed` events through deterministic temporal rules.
- Store events locally and show a dashboard, daily journal, and caregiver alert.

## Non-Goals

- No medical-device claims.
- No HIPAA compliance claims.
- No autonomous emergency dispatch.
- No confirmation of medication administration from vision alone.
- No default raw-video cloud upload.
- No Ring/Nest adapter work in v1/v2.

## Success Criteria

- A judge can understand the bounded local-first architecture from the repo.
- A local run can show perception-to-event-to-journal-to-alert behavior.
- The safety boundaries are encoded in contracts and examples, not only prose.
