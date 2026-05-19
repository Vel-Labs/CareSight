# Demo Script and Storytelling

## Core story

> Many people who need care cannot reliably press a button, open an app, remember a routine, or explain what happened. CareSight Hub gives the home its own local memory. It observes care-relevant events with YOLO26 MLX, stores them locally, and escalates to the right caregiver only when needed.

---

# 60-second demo script

## 0–8 seconds — problem

“Care often depends on someone remembering to press a button or write down what happened. But the people who need the most help may not have that ability in the moment.”

Visual:

- Show title card: CareSight Hub.
- Show Mac mini/MacBook + camera.

## 8–18 seconds — architecture

“CareSight runs locally on Apple Silicon using YOLO26 MLX. Raw video stays on the base unit. The system converts camera feeds into structured care events.”

Visual:

- Live camera feed.
- YOLO overlay.
- Local dashboard.

## 18–32 seconds — safety event

“Here is a possible floor-stay event.”

Visual:

- Person simulates low/floor state.
- Event fires after threshold.
- Dashboard shows confidence, duration, camera, zone.

Overlay:

```text
Possible floor-stay event
Living Room · 31s · Confidence High
Raw video local
```

## 32–44 seconds — routine event

“CareSight also tracks care routines without claiming more than it knows.”

Visual:

- Person enters medication zone with cup/bottle.
- Journal entry appears.

Overlay:

```text
Medication routine likely observed
Awaiting confirmation
```

## 44–52 seconds — caregiver action

“Caregivers can acknowledge, FaceTime, or review the daily journal.”

Visual:

- Alert card.
- Optional OBS scene switch.
- FaceTime handoff button.

## 52–60 seconds — close

“YOLO sees objects. CareSight coordinates care.”

Visual:

- Daily journal.
- Benchmark panel.
- Repo/README/submission slide.

---

# One-line pitch options

- “CareSight Hub is a local-first care event engine for homes and small care environments.”
- “A camera sees objects. CareSight coordinates care.”
- “Ambient care without requiring the cared-for person to operate anything.”
- “Life Alert is a button. CareSight is a local safety layer.”
- “A Mac mini, ordinary cameras, and YOLO26 MLX become a privacy-first care base unit.”

---

# Demo shots to capture

- Hardware shot: MacBook/Mac mini + camera.
- Live YOLO overlay.
- Zone editor/config.
- Possible floor-stay event firing.
- Medication routine journal entry.
- SQLite/event timeline screen.
- OBS scene switch if implemented.
- FaceTime handoff if implemented.
- README benchmark table.

---

# README hero paragraph

```text
CareSight Hub is a set-and-forget care appliance that runs on Apple Silicon. It uses YOLO26 MLX to detect care-relevant events from local cameras, stores structured observations in SQLite, and routes alerts/journal entries to permissioned caregivers. The person being cared for does not need to press a button, open an app, or remember a routine.
```

---

# Social post draft

```text
Built CareSight Hub for the YOLO26 MLX Build Challenge: a local-first care event engine that turns a Mac + ordinary cameras into an ambient caregiver safety layer.

YOLO26 MLX runs on-device, SQLite stores the care record, and the system can route events into alerts, journals, OBS live-view, and FaceTime handoff.

Goal: help families and caregivers notice meaningful events without streaming private home video to the cloud.
```

---

# What judges should remember

- This is not a bounding-box demo.
- It is a local perception-to-action care engine.
- It has a real TAM: family caregiving, pets, home safety, facilities.
- It is privacy-aligned by design.
- It uses YOLO26 MLX meaningfully and centrally.
- It has a credible roadmap beyond the hackathon.

---

# Backup demo plan

If live camera fails:

- Use a prerecorded local video file.
- Show YOLO inference on that file.
- Show event JSON and SQLite output.
- Show dashboard with generated events.
- Explain webcam path in README.

If Shortcuts/FaceTime fails:

- Show local alert mock.
- Show generated command/log line.
- Show OBS scene switch as independent proof.

If Gemma fails:

- Use deterministic alert templates.
- Keep Gemma as stretch/future feature.
