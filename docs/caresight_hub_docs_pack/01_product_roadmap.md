# CareSight Hub Product Roadmap

## North star

CareSight Hub turns a low-cost Apple Silicon base unit and existing cameras into an ambient care event engine. It runs locally, observes care-relevant patterns, stores a structured history, and escalates to permissioned people without requiring the cared-for person to operate an app or press a button.

## Strategic product shape

```text
Base unit at location
  → camera feeds
  → YOLO26 MLX local perception
  → care event engine
  → SQLite event memory
  → local dashboard / journal
  → caregiver alert and escalation
  → optional OBS + FaceTime live handoff
```

The key product is not a camera viewer. It is a **chain of care** system: observed event, confidence, context, human acknowledgement, journal, and audit trail.

---

# v0 — Technical smoke test

## Goal

Prove the core engine works in the simplest possible way.

## Timebox

Half day to one day.

## Target demo

A MacBook/Mac mini webcam feed runs YOLO26 MLX. A person enters a zone, stays there for a threshold, and the app writes a structured event to SQLite.

## Required features

- Install YOLO26 MLX and run webcam inference.
- Process one camera source.
- Detect person objects.
- Define one rectangular or polygon zone.
- Track dwell time in the zone.
- Create a JSON event when threshold is crossed.
- Insert event into SQLite.
- Print event to terminal or show in a minimal dashboard.

## Non-goals

- No Ring/Nest.
- No OpenClaw.
- No Gemma.
- No FaceTime automation.
- No Apple Notes.
- No multi-camera support.
- No custom training.

## Success criteria

- Reproducible local run command.
- Event record generated with timestamp, camera, zone, event type, duration, confidence.
- README includes hardware, model variant, setup steps, and limitations.

---

# v1 — Hackathon MVP

## Goal

Ship an elegant, credible care event engine in the challenge window.

## Recommended positioning

> CareSight Hub is a local-first care event engine that uses YOLO26 MLX on Apple Silicon to observe safety and routine events, store them in a local care journal, and alert permissioned caregivers.

## Required features

### Vision and event engine

- One reliable camera source: Mac webcam, USB webcam, or iPhone Continuity Camera.
- YOLO26 MLX running on-device.
- Model variant: start with `yolo26n`; optionally compare `yolo26s`.
- Two event types:
  1. `possible_floor_stay`
  2. `medication_routine_likely_observed`
- Basic tracking or temporal smoothing.
- Zone definitions stored in config.
- Event confidence labels: low, medium, high.

### Data layer

- SQLite local database.
- Tables for cameras, zones, events, observations, alerts, journal entries.
- Daily care journal generated as Markdown.

### UI

- Local dashboard showing:
  - live annotated feed or frame preview
  - current detections
  - event timeline
  - daily journal
  - model/hardware/FPS panel

### Alerts

- One working alert channel:
  - terminal notification, local browser alert, macOS notification, or Apple Shortcut message.
- The alert should include:
  - event type
  - location
  - confidence
  - recommended action
  - “raw video local” statement

### Submission assets

- Public GitHub repo.
- README with challenge checklist.
- 60-second demo video.
- Social post draft.

## Recommended v1 stack

```text
Python
YOLO26 MLX
OpenCV / native camera capture
SQLite
FastAPI or Streamlit dashboard
Markdown daily journal
Optional macOS Shortcut for message/journal action
```

## Success criteria

- A judge can run the repo locally on Apple Silicon.
- The demo shows more than bounding boxes: it shows care events and escalation logic.
- The README explains why on-device matters.
- The project clearly avoids medical-device claims.

---

# v2 — Hackathon stretch MVP

## Goal

Add the “this feels like a product” layer without risking the core demo.

## Stretch features in priority order

### 1. OBS live-view bridge

- OBS profile with scenes:
  - Idle View
  - Living Room Event
  - Medication Station Event
  - Dashboard Scene
- CareSight switches scenes through obs-websocket.
- OBS Virtual Camera is ready for FaceTime.

### 2. FaceTime handoff

- Button/action opens a FaceTime URL for a configured caregiver.
- Product language: “FaceTime handoff,” not emergency dispatch.

### 3. Apple Shortcut automation

- Shortcut called `CareSight Alert` or `CareSight Journal Append`.
- CareSight invokes the shortcut with JSON or Markdown input.

### 4. Gemma local summarizer

- Local Gemma endpoint converts structured event JSON into caregiver-friendly language.
- Gemma must not be responsible for raw vision or emergency authority.

### 5. Role demo

- Add caregiver roles:
  - family caregiver
  - nurse/care worker
  - temporary caregiver/pet sitter
- Add one temporary-access example.

### 6. Pet event demo

- Add `pet_food_activity_observed` or `pet_left_room`.
- This is a range demonstration, not the core mission.

## Success criteria

- OBS scene changes when an event fires.
- The daily journal includes generated caregiver-friendly summaries.
- A caregiver-facing alert can trigger a FaceTime handoff.
- The system still runs if the stretch features are disabled.

---

# v3 — Home pilot

## Goal

Turn the hackathon demo into a realistic home appliance pilot.

## Features

- Multi-camera configuration.
- RTSP camera support.
- ONVIF discovery or manual camera setup.
- Home Assistant camera entity support.
- launchd-based auto-start.
- Dedicated non-admin macOS user.
- Camera health checks.
- Reconnect logic.
- Local settings UI.
- Privacy mode / quiet hours.
- Better zone editor.
- Local retention policy.
- Basic encryption-at-rest plan.
- Caregiver acknowledgement workflow.

## Success criteria

- System can run unattended after reboot.
- Cameras reconnect after network interruptions.
- Alerts are not noisy.
- Daily journal is useful to a family caregiver.

---

# v4 — Care network

## Goal

Make delegated care the core product.

## Features

- Role-based access control.
- Time-limited temporary access.
- Event acknowledgement and escalation ladder.
- Daily/weekly summaries.
- Care plans and routine windows.
- Missed-routine detection.
- Secure remote event view.
- Snapshot/video clip approval workflow.
- Family/nurse/pet-sitter separation.
- Searchable journal using SQLite FTS.
- Human confirmation status:
  - observed
  - likely
  - confirmed
  - dismissed
  - unresolved

## Success criteria

- A family can share only the right events with the right person.
- A temporary caregiver can confirm only their assigned tasks.
- Journal history is searchable and exportable.

---

# v5 — Model and device optimization

## Goal

Make the system scalable and accessible across lower-power devices.

## Features

- Benchmark `yolo26n`, `yolo26s`, and possibly segmentation variants.
- Frame skipping and tracking between inference frames.
- Adaptive FPS per camera.
- Low-power mode.
- Event-triggered high-resolution inference.
- Model confidence calibration.
- Optional fine-tuned classes:
  - walker
  - pill bottle
  - medication organizer
  - pet bowl
  - package
  - wheelchair
- Synthetic/staged dataset collection workflow.
- Evaluation metrics for false positives/false negatives.

## Success criteria

- System runs on low-cost Apple Silicon hardware.
- README includes FPS/latency benchmarks.
- Model choices are explained by use case.

---

# v6 — Facility / enterprise pilot

## Goal

Extend from home care to assisted living, nursing homes, and small care facilities.

## Features

- Multi-room/multi-resident event routing.
- Staff role model.
- Shift handoff summaries.
- Care-plan task logs.
- Medication routine observation with human confirmation.
- Audit exports.
- Retention and deletion policy.
- Compliance review path.
- Facility camera fleet support.
- Event-only storage mode.
- Optional no-identity/anonymous occupancy mode.

## Success criteria

- A facility can use the system as a supplemental care awareness layer.
- Staff can document care without overclaiming that vision alone proves care.
- Legal/compliance boundaries are explicit.

---

# v7 — Commercialization path

## Product variants

### Home Basic

- One base unit.
- Two to four cameras.
- Family alerts.
- Daily journal.

### Home Plus

- More cameras.
- Temporary caregiver access.
- FaceTime/OBS handoff.
- Custom routines.

### Pet Care

- Pet sitter delegation.
- Feeding and room-presence logs.
- Door/yard alerts.

### Care Facility

- Role-based staff access.
- Shift handoff.
- Care-plan observations.
- Audit and compliance tooling.

## Business advantages

- Local-first ownership.
- Low base unit cost.
- Commodity cameras.
- Existing Apple/macOS ecosystem.
- Privacy-forward design.
- Broad care TAM: aging, family caregiving, pets, facilities.

## Moat candidates

- Event engine and routine scoring.
- Privacy-preserving care journal.
- Role-based delegated care workflows.
- Model/device optimization on Apple Silicon.
- Carefully designed caregiver UX.
