# CareSight Hub Architecture

## High-level diagram

```text
Camera sources
  ├── Mac webcam / USB webcam
  ├── iPhone Continuity Camera
  ├── RTSP / ONVIF IP camera
  ├── Home Assistant camera entity
  └── optional Ring / Nest adapters

        ↓ frames

Vision engine
  ├── YOLO26 MLX inference
  ├── detection filtering
  ├── tracking / temporal smoothing
  ├── zone membership
  └── object state memory

        ↓ observations

Event engine
  ├── floor-stay detector
  ├── medication routine detector
  ├── pet activity detector
  ├── missed routine detector
  ├── camera health detector
  └── confidence / severity scoring

        ↓ structured events

Local memory
  ├── SQLite source of truth
  ├── event observations
  ├── journal entries
  ├── alerts
  ├── audit log
  └── daily Markdown/Notes journal

        ↓ actions

Caregiver layer
  ├── dashboard
  ├── alert templates
  ├── Apple Shortcuts
  ├── OBS scene bridge
  ├── FaceTime handoff
  └── Gemma/OpenClaw summarizer/router
```

## Module boundaries

### Camera layer

Responsibilities:

- Open camera sources.
- Reconnect dropped feeds.
- Normalize frames.
- Attach camera ID, room, timestamp.

Non-responsibilities:

- No care inference.
- No alert logic.

### Vision layer

Responsibilities:

- Run YOLO26 MLX.
- Return object detections.
- Optionally track persistent IDs.
- Evaluate zone membership.
- Produce frame-level observations.

Non-responsibilities:

- No caregiver communication.
- No medical claims.

### Event layer

Responsibilities:

- Convert observations into care-relevant events.
- Apply temporal thresholds.
- Apply routine windows.
- Score confidence and severity.
- De-duplicate repeated events.

Non-responsibilities:

- No free-form LLM decisions.
- No raw camera streaming to third parties.

### Data layer

Responsibilities:

- Store canonical structured records.
- Support event lookup and journal generation.
- Maintain audit trail.
- Support future search/export.

Non-responsibilities:

- Not the user-facing live view.

### Agent/action layer

Responsibilities:

- Summarize event JSON.
- Generate caregiver-friendly wording.
- Invoke approved actions only.
- Route alerts based on configured policies.

Non-responsibilities:

- No arbitrary shell access.
- No unsandboxed autonomous emergency actions.

### Presentation layer

Responsibilities:

- Local dashboard.
- OBS scene selection.
- FaceTime handoff.
- Daily journal display.

Non-responsibilities:

- Not the canonical source of truth.

---

# Recommended repo structure

```text
caresight/
  __init__.py

  config/
    default.yaml
    cameras.yaml
    routines.yaml
    roles.yaml

  cameras/
    base.py
    webcam.py
    rtsp.py
    continuity_camera.md
    home_assistant.py
    ring_adapter_stub.py
    nest_adapter_stub.py

  vision/
    yolo26_runner.py
    detections.py
    tracker.py
    zones.py
    benchmarks.py

  events/
    engine.py
    floor_stay.py
    medication.py
    pet_food.py
    missed_routine.py
    confidence.py

  data/
    db.py
    schema.sql
    migrations/
    journal.py

  actions/
    alerts.py
    shortcuts.py
    facetime.py
    obs_bridge.py
    templates.py

  agent/
    gemma_client.py
    openclaw_bridge.py
    policy_guard.py
    prompts.py

  app/
    dashboard.py
    api.py
    static/
    templates/

  cli.py

tests/
  test_events.py
  test_confidence.py
  test_schema.py

docs/
  architecture.md
  safety.md
  demo.md

README.md
pyproject.toml
```

---

# Data flow examples

## Possible floor-stay

```text
Frame captured
  → person detected
  → bbox center/height indicates person is in floor zone
  → tracker says same person remains low for 30 seconds
  → event engine creates possible_floor_stay
  → SQLite stores event and observations
  → dashboard updates
  → alert policy sends high-priority caregiver alert
  → OBS switches to Event View
  → daily journal entry created
```

## Medication routine likely observed

```text
Frame captured
  → person detected in medication zone
  → cup/bottle/object detected nearby
  → routine window is active
  → evidence persists for N seconds
  → event engine creates medication_routine_likely_observed
  → journal entry status = awaiting confirmation
  → caregiver/nurse can confirm or dismiss
```

## Pet activity

```text
Frame captured
  → dog/cat detected near pet bowl zone
  → presence persists for N seconds
  → event engine creates pet_food_activity_observed
  → pet sitter/family can receive summary
```

---

# Recommended local services

## Core runtime

- Python process for camera, YOLO, event engine.
- SQLite database file.
- Dashboard server.

## macOS user-session helpers

- OBS.
- Apple Shortcuts.
- FaceTime.
- Notes automation.

## Why split runtime and user-session helpers

Some macOS integrations depend on an interactive user session and permissions. Treat them as optional action adapters, not as dependencies for the core event engine.
