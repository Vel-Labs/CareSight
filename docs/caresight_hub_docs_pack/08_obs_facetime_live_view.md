# OBS, FaceTime, and Live Event View

## Product role of OBS

OBS should be the caregiver presentation bus, not the primary perception source.

```text
CareSight analyzes raw camera feeds.
OBS presents the right feed/context to humans.
```

This preserves reliable YOLO processing while making live caregiver view polished.

---

# Recommended OBS architecture

```text
CareSight event engine
  → event fired with camera_id and summary
  → OBS bridge switches to relevant scene
  → OBS scene shows camera feed + event overlay
  → OBS Virtual Camera exposes that scene
  → FaceTime can use OBS Virtual Camera
```

---

# OBS scenes

## Idle View

- CareSight logo/title.
- Camera health status.
- “Monitoring locally” message.

## Living Room Event

- Living room camera feed.
- Event overlay: event type, timestamp, confidence.
- Privacy message: raw video local.

## Medication Station Event

- Kitchen/medication station feed.
- Routine overlay.
- Confirmation status.

## Pet Care Event

- Pet bowl or door zone feed.
- Temporary caregiver note.

## Dashboard Scene

- Browser source showing CareSight dashboard.

---

# OBS WebSocket control

Modern OBS includes WebSocket support. CareSight can use a Python client to:

- connect to OBS
- switch scenes
- update text sources
- start/stop virtual camera
- optionally start/stop local recording

## Example pseudocode

```python
from obsws_python import ReqClient

client = ReqClient(host="localhost", port=4455, password="CHANGE_ME")
client.set_current_program_scene("Living Room Event")
client.set_input_settings(
    "Event Summary Text",
    {"text": "Possible floor-stay event · Confidence High"},
    True,
)
```

---

# Virtual camera setup

OBS Virtual Camera lets an OBS scene appear as a webcam to other apps. For the demo:

1. Open OBS.
2. Build CareSight scenes.
3. Start Virtual Camera.
4. Open FaceTime.
5. Choose OBS Virtual Camera from FaceTime camera options.
6. Trigger a CareSight event.
7. CareSight switches OBS to the event scene.

---

# FaceTime handoff

FaceTime should be treated as a handoff layer, not the canonical live-view system.

Recommended alert actions:

```text
[View Event]
[FaceTime Caregiver]
[Acknowledge]
[Mark False Positive]
```

For the MVP, a FaceTime handoff can be a button that opens:

```text
facetime:caregiver@example.com
```

MacOS may prompt before initiating a call. Document this honestly.

---

# Caregiver live-view options

## Option A — FaceTime with OBS Virtual Camera

Pros:

- Familiar to families.
- Polished demo.
- No custom live-video stack needed.

Cons:

- Requires user-session state.
- May require manual camera selection.
- May prompt before calls.
- Not ideal as a guaranteed unattended emergency path.

## Option B — Local CareSight event page

Pros:

- More controllable.
- Can show timeline, snapshots, and actions.
- Better product path.

Cons:

- Remote access/security is more complex.

## Option C — Hybrid

Best product path:

```text
Alert → View Event page → optional FaceTime handoff
```

---

# Hackathon implementation order

1. Create OBS profile manually.
2. Add WebSocket password.
3. Build `obs_bridge.py` with scene switch function.
4. Trigger scene switch on event.
5. Add event overlay text.
6. Start OBS Virtual Camera manually.
7. Add FaceTime link/button.

---

# Security notes

- Use WebSocket password.
- Bind to localhost when possible.
- Do not expose OBS control to the public internet.
- Do not let LLM call OBS commands except through an allow-listed function.
- Log all scene switches triggered by care events.
