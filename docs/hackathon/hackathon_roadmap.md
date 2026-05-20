# CareSight Hub — Hackathon Roadmap

## Product thesis

CareSight Hub is a bounded, local-first care loop:

```text
Camera input
→ YOLO26 MLX local perception
→ event rules and confidence scoring
→ SQLite local memory
→ daily care journal
→ caregiver alert
→ optional OBS / FaceTime handoff
```

The hackathon build should prove one thing exceptionally well:

> A Mac-based local care appliance can observe meaningful care events, record them responsibly, and escalate them to the right caregiver without requiring the person at home to operate anything.

This roadmap intentionally limits scope to **v0, v1, and v2**. Everything else belongs in `future_roadmap.md`.

---

## Hackathon north star

Build a polished demo that shows:

1. **On-device YOLO26 MLX inference**
2. **A meaningful care event**
3. **Local structured memory**
4. **A human-readable care journal**
5. **A caregiver alert**
6. **A set-and-forget resident experience**

The cared-for person should not need to press a button, answer a prompt, open an app, or understand the device.

---

## Non-goals for the hackathon

Do **not** depend on these for the submitted MVP:

- Ring / Nest / Google Home integration
- full ONVIF discovery
- multi-home cloud account system
- HIPAA-ready deployment
- autonomous emergency dispatch
- medical-grade fall detection claims
- voice cloning
- EHR integration
- biometric identity recognition / face recognition
- nursing-home compliance workflows
- perfect medication proof

The demo should say **“likely observed,” “possible event,” “requires acknowledgement,” and “caregiver confirmed”** rather than overclaiming certainty.

Non-biometric daily appearance profiles are allowed as a bounded future sprint: clothing/accessory descriptors, last-seen room, and human-assigned roles for the day. They must not claim durable identity or face recognition.

---

# v0 — Technical smoke test

## Goal

Prove the minimal perception-to-memory loop works.

```text
one camera
→ YOLO26 MLX
→ one zone/dwell rule
→ one SQLite event row
→ terminal or simple dashboard output
```

## Build scope

### Camera

- Mac webcam, USB webcam, or iPhone Continuity Camera.
- One stream only.

### Vision

- Run YOLO26 MLX with `yolo26n` first.
- Detect `person`.
- Draw bounding boxes or print detections.

### Event rule

Create one deterministic rule:

```text
If person is detected in configured floor/low zone
and remains there for N seconds,
create possible_floor_stay event.
```

### Storage

Write the event to SQLite:

```text
events
- id
- timestamp
- event_type
- camera_id
- zone_id
- severity
- confidence
- status
- evidence_json
```

### Output

Any of these is enough:

- terminal log
- simple local web page
- Streamlit page
- plain JSON file
- markdown event output

## Acceptance criteria

v0 is complete when:

- YOLO26 MLX runs locally on the Mac.
- A live camera frame can be processed.
- A care event is triggered by a visible action.
- The event is saved in SQLite.
- The event can be replayed or inspected after the app exits.

## Demo line

> “This is the core loop: local perception creates a structured care event without sending raw video to the cloud.”

---

# v1 — Hackathon MVP

## Goal

Ship the most elegant bounded MVP.

```text
camera
→ YOLO26 MLX
→ two care event rules
→ SQLite event log
→ daily care journal
→ caregiver alert
→ local dashboard
```

## Recommended v1 features

### 1. Camera input

Support one primary camera source:

- Mac webcam
- USB webcam
- iPhone Continuity Camera

Optional config field:

```yaml
camera:
  id: living_room
  name: Living Room
  source_type: webcam
  source_uri: 0
```

### 2. YOLO26 MLX local perception

Use YOLO26 MLX as the core vision engine.

Recommended model order:

1. `yolo26n` for real-time stability
2. `yolo26s` only if accuracy is materially better and latency is acceptable

### 3. Two care events

Build exactly two v1 events:

#### Event A — possible_floor_stay

Purpose:

```text
Detect a possible safety event when a person is low/in a floor zone for a sustained duration.
```

Example logic:

```text
person detected
+ bounding box center in floor zone
+ low vertical position or configured zone overlap
+ dwell time >= 20–30 seconds
= possible_floor_stay
```

Output wording:

```text
Possible floor-stay event in Living Room.
Person has been low/in the floor zone for 31 seconds.
Status: awaiting caregiver acknowledgement.
```

#### Event B — medication_routine_likely_observed

Purpose:

```text
Detect that a medication routine may have occurred, without claiming medical certainty.
```

Example logic:

```text
person detected near medication zone
+ cup or bottle visible
+ event occurs during configured routine window
+ dwell time >= threshold
= medication_routine_likely_observed
```

Output wording:

```text
Medication routine likely observed.
Evidence: person at medication station, cup/bottle visible.
Status: awaiting confirmation.
```

### 4. SQLite local memory

SQLite should be the source of truth.

Minimum tables:

```text
cameras
zones
routines
events
event_observations
journal_entries
alerts
people
```

### 5. Daily care journal

Generate a markdown journal from SQLite.

Example:

```markdown
# CareSight Daily Journal — 2026-05-18

## Medication
- [ ] 8:03 AM — Medication routine likely observed.
  Evidence: person at medication station, cup/bottle visible.
  Status: awaiting caregiver confirmation.

## Safety
- [ ] 10:22 AM — Possible floor-stay event in Living Room.
  Duration: 31 seconds.
  Alert sent to: Primary caregiver.
  Status: awaiting acknowledgement.
```

### 6. Caregiver alert

Use one reliable alert action.

Acceptable v1 options:

- local dashboard alert
- desktop notification
- generated message template
- Apple Shortcut that sends a text/iMessage
- copied alert text with clickable action buttons in dashboard

Recommended for demo reliability:

```text
Dashboard alert + generated caregiver text
```

Stretch within v1:

```text
Apple Shortcut sends caregiver alert.
```

### 7. Local dashboard

The dashboard should show:

- live camera feed
- detection overlay
- current event state
- event timeline
- daily journal preview
- model variant
- hardware used
- raw video policy: local only

## v1 acceptance criteria

v1 is complete when:

- The demo can run from a clean README.
- YOLO26 MLX processes the live camera feed.
- At least two care events can be triggered live.
- Events are stored in SQLite.
- The daily journal can be generated.
- A caregiver alert can be shown or sent.
- The README documents hardware, model variant, and how to run.
- The demo does not rely on external camera APIs.

## v1 demo script

### 0–8 seconds

> “CareSight Hub is a local care appliance for people who may not be able to press a button or operate an app during a care event.”

### 8–18 seconds

Show the local dashboard:

> “It runs YOLO26 MLX on this Mac, watches a camera feed locally, and stores only structured care events in SQLite.”

### 18–32 seconds

Trigger possible floor-stay:

> “Here, the system detects a possible floor-stay event after the person remains in the configured floor zone.”

Show:

```text
Possible floor-stay event
Duration: 31 seconds
Severity: high
Status: awaiting acknowledgement
```

### 32–44 seconds

Trigger medication routine:

> “This does not claim medication was taken. It says the routine was likely observed and asks an authorized caregiver to confirm.”

Show:

```text
Medication routine likely observed
Evidence: person + medication zone + cup/bottle
Status: awaiting confirmation
```

### 44–54 seconds

Show caregiver alert and journal:

> “The event is logged locally, summarized for the caregiver, and added to the daily care journal.”

### 54–60 seconds

Close with:

> “A camera sees objects. CareSight coordinates care.”

---

# v2 — Hackathon stretch MVP

## Goal

Add the live-caregiver experience and local agent polish after v1 is stable.

```text
v1 core loop
+ OBS scene switching
+ FaceTime handoff
+ Apple Shortcut automation
+ local Gemma summary
+ optional pet / temporary caregiver event
```

Do v2 only after v1 is reliable.

---

## v2 stretch 1 — OBS Event View

### Purpose

OBS becomes the visual presentation layer for caregivers.

```text
CareSight analyzes raw feeds.
OBS shows the right scene to humans.
```

### Build

Create OBS scenes:

```text
Idle View
Living Room Event View
Medication Station Event View
Journal / Dashboard View
```

When an event fires:

```text
CareSight event
→ OBS WebSocket
→ switch to relevant event scene
→ update overlay text
→ start/ensure OBS Virtual Camera
```

### Acceptance criteria

- Event triggers OBS scene switch.
- Event scene shows relevant feed and summary.
- OBS Virtual Camera can be selected in FaceTime or another video app.

---

## v2 stretch 2 — FaceTime handoff

### Purpose

Give caregivers a familiar live escalation path.

### Build

Add a dashboard button or alert action:

```text
[FaceTime caregiver]
```

Implementation options:

```bash
open "facetime:caregiver@example.com"
```

or:

```bash
shortcuts run "CareSight FaceTime Caregiver"
```

### Product rule

FaceTime is a **handoff**, not guaranteed emergency dispatch.

The system should still work if FaceTime fails:

```text
primary: FaceTime handoff
fallback: dashboard event view
fallback: text summary
```

---

## v2 stretch 3 — Apple Shortcut alert / journal append

### Purpose

Use the Mac’s native tools as part of the appliance story.

### Build

Create one or two Shortcuts:

```text
CareSight Send Alert
CareSight Append Journal
```

CareSight writes JSON or markdown, then invokes the Shortcut.

Example:

```bash
shortcuts run "CareSight Send Alert" --input-path ./out/latest_alert.txt
```

### Acceptance criteria

- Alert text can be sent or staged through Shortcuts.
- Journal entry can be appended or exported.
- If Shortcuts fail, local dashboard still shows the event.

---

## v2 stretch 4 — Local Gemma summary

### Purpose

Use a local language model for caregiver-friendly wording, Apple Notes drafts, handoff packets, and audit summaries, not vision or authority.

Recommended local stack:

```text
SQLite blackbox
→ structured event JSON / audit chain
→ local Gemma MLX service
→ OpenClaw/Hermes agent wrapper
→ constrained draft JSON
→ human review / Apple Notes / alert text
```

### Input

Gemma receives structured event JSON and local audit context:

```json
{
  "event_type": "possible_floor_stay",
  "room": "Living Room",
  "duration_seconds": 31,
  "severity": "high",
  "confidence": 0.87,
  "status": "human_confirmed",
  "reviewer": "Steven",
  "blocked_actions": ["autonomous_emergency_dispatch", "medical_diagnosis"]
}
```

### Output

Gemma returns constrained draft JSON:

```json
{
  "caregiver_summary": "A possible floor-stay event was confirmed in the Living Room.",
  "apple_notes_entry": "CareSight confirmed a possible floor-stay event in the Living Room. Reviewed by Steven.",
  "alert_draft": "CareSight confirmed a possible floor-stay event in the Living Room. Please review the local record and follow your care plan.",
  "safety_boundaries": ["draft_only", "human_review_required"]
}
```

### Safety boundary

Gemma/OpenClaw/Hermes does not:

- analyze raw video
- inspect raw snapshots unless a later explicit local image-summary scope is approved
- confirm or dismiss events
- decide medical status
- directly dispatch emergency services
- run arbitrary shell commands
- override escalation policy
- delete or rewrite SQLite records
- claim medication was taken

### Acceptance criteria

- The model is served locally through an MLX runtime.
- Inputs are structured event/audit JSON, not raw video.
- Outputs are constrained JSON with purpose and provenance.
- Apple Notes and caregiver alerts are draft-only unless a human approves a local automation.
- Forbidden-action tests prove the agent cannot confirm, dismiss, dispatch, diagnose, delete, or become reviewer of record.

---

## v2 stretch 5 — Pet / temporary caregiver event

### Purpose

Show that the engine generalizes beyond elder care.

Example:

```text
Pet food area activity observed.
Dog/cat present near food bowl for 42 seconds.
Temporary caregiver notified or journal updated.
```

This is a strong value-add because it demonstrates:

- different subject type
- different role
- different permissions
- same event engine

Keep it optional.

---

## v2 stretch 6 — Daily Appearance Profiles

### Purpose

Give caregivers a local, practical last-seen description without claiming biometric identity.

This is especially useful for wandering or missing-off-camera concerns, where a caregiver may need a quick answer to:

```text
Who was last seen?
Where were they last seen?
What were they wearing today?
Was this likely the same tracked person as the prior room?
```

### Build

Create daily, expiring appearance profiles from person observations:

```text
track_id
+ clothing color descriptors
+ visible accessories
+ carried objects
+ last seen room/camera/time
+ optional human-assigned role for the day
= daily appearance profile
```

Example:

```json
{
  "appearance_profile_id": "appearance_2026_05_20_001",
  "role_assignment": "resident_primary",
  "assignment_source": "human_confirmed",
  "active_date": "2026-05-20",
  "expires_at": "2026-05-21T04:00:00Z",
  "attributes": {
    "upper_body_color": { "value": "blue", "confidence": 0.72 },
    "lower_body_color": { "value": "black", "confidence": 0.68 },
    "headwear": { "value": "dark hat", "confidence": 0.66 },
    "eyewear": { "value": "glasses", "confidence": 0.58 }
  },
  "last_seen": {
    "camera_id": "hallway",
    "room": "Hallway",
    "timestamp": "2026-05-20T14:04:12Z",
    "direction_hint": "toward front door"
  }
}
```

### Output wording

Allowed:

```text
Likely same tracked person based on clothing, accessories, timing, and room transition.
```

```text
Last seen in Hallway wearing a blue upper layer, dark hat, and black pants.
```

Not allowed:

```text
Identity confirmed.
This is Steven.
Biometric match.
```

### Acceptance criteria

- Profiles are local-only SQLite records.
- Profiles refresh daily and expire after a configured window.
- Matching uses conservative confidence thresholds.
- Human assignment can label a profile as resident/caregiver/visitor for the day.
- Event language remains `likely`, `possible`, or `human assigned`.
- No face recognition or durable biometric identity claim is introduced.

### Demo line

> “CareSight does not need to know a person’s identity to be helpful. It can remember today’s local appearance and last-seen context so a caregiver has a useful description when something feels wrong.”

---

# Six-day build plan

## Day 1 — v0

- Get YOLO26 MLX running.
- Process camera feed.
- Define a zone.
- Trigger one dwell event.
- Save one event to SQLite.

Kill gate:

```text
If camera + YOLO + SQLite do not work by end of Day 1,
cut all v2 features.
```

## Day 2 — v1 event engine

- Add event state machine.
- Add possible_floor_stay.
- Add medication_routine_likely_observed.
- Add confidence/severity fields.
- Add replay/test fixtures.

Kill gate:

```text
If two events are unreliable,
ship only the strongest one but make the journal/alert excellent.
```

## Day 3 — dashboard and journal

- Build local dashboard.
- Show feed, detections, current state, event timeline.
- Generate daily markdown journal.
- Add README installation/run instructions.

## Day 4 — caregiver alert and polish

- Add alert template.
- Optional Apple Shortcut alert.
- Add acknowledgement buttons.
- Add false-positive/dismiss state.
- Prepare demo staging.

Kill gate:

```text
If alerts are flaky,
use dashboard alert + generated message text instead of live iMessage.
```

## Day 5 — v2 stretch

Choose at most two:

1. OBS scene switching
2. FaceTime handoff
3. Apple Shortcut journal append
4. Local Gemma summary
5. Pet/temporary caregiver event

Recommended order:

```text
OBS scene switching
→ FaceTime handoff
→ Gemma summary
```

## Day 6 — submission package

- Record 60-second demo.
- Finish README.
- Add hardware/model benchmark table.
- Add architecture diagram.
- Add limitations and safety statement.
- Push public repo.
- Prepare social post.

---

# Judging alignment

## Meaningful use of YOLO26 MLX

CareSight uses YOLO26 MLX as the local perception layer for people, objects, zones, dwell time, and care events.

## On-device execution

The core loop runs on the Mac. The product promise is local-first and raw-video-minimizing.

## Demo quality

The demo shows a complete loop:

```text
visible real-world event
→ detection
→ structured event
→ journal
→ alert
→ optional live handoff
```

## Technical execution

The app includes:

- camera processing
- model inference
- event state machine
- local database
- dashboard
- alert/journal pipeline
- optional OBS/FaceTime integration

## Creativity

The project reimagines Life Alert as ambient local care infrastructure rather than a button.

## Usefulness

It helps caregivers know when something care-relevant happened, even if the person at home cannot operate a device.

## Storytelling

The narrative is human and direct:

> “CareSight Hub gives a home its own memory, without turning the home into a cloud surveillance product.”

---

# Final hackathon scope statement

The submitted build should be described as:

> **CareSight Hub is a set-and-forget, on-device care event engine. It runs on a Mac, uses YOLO26 MLX to detect meaningful care events from a local camera, stores structured observations in SQLite, generates a daily care journal, and alerts permissioned caregivers when attention is needed.**

Optional v2 line:

> **With OBS and FaceTime handoff, CareSight can also switch the live caregiver view to the room where the event happened.**

---

# Open Questions

Question: Should the hackathon demo default to the proof event or unresolved concerns?
Suggested Answer: Default to a focused proof-event view and show unresolved concerns as a separate backlog.
Rationale: Judges need a coherent loop, but the blackbox record should still expose unresolved state.

Question: Should Gemma/OpenClaw/Hermes draft Apple Notes entries automatically?
Suggested Answer: It should draft entries automatically, but appending to Apple Notes should require explicit local automation approval.
Rationale: Drafting is low-risk and useful; writing to user-visible systems needs an audit boundary.

Question: Should the LLM see raw video or snapshots?
Suggested Answer: No for the next sprint. The LLM should only consume structured event JSON, audit chains, and bounded descriptors.
Rationale: YOLO26 MLX owns perception, while the LLM owns wording and summarization.

Question: Should Daily Appearance Profiles be part of v1 or v2?
Suggested Answer: Treat them as the next major v2 value sprint after demo-surface and agent drafting are stable.
Rationale: They are highly valuable but depend on reliable tracking, profile expiration, and careful safety language.

Question: Should Daily Appearance Profiles identify named people?
Suggested Answer: No. They should describe today’s local appearance and optional human-assigned role, not durable identity.
Rationale: Clothing/accessory descriptors are not biometric identity and should refresh daily.

Question: What is the right expiration window for appearance profiles?
Suggested Answer: Same-day expiration with a configurable 12-18 hour active window.
Rationale: This balances caregiver utility with the reality that clothing changes day to day.

Question: Should multi-camera include discovery?
Suggested Answer: Not yet. Use explicit local camera/RTSP configuration first.
Rationale: Discovery adds network, credential, and privacy risk before it is needed for the room-to-room demo.

Question: Should routine events claim medication taken or hydration completed?
Suggested Answer: No. Use “routine likely observed” language and require human confirmation.
Rationale: Vision can support care awareness, not medication adherence or health-state proof.

Question: Should severity escalation trigger emergency dispatch?
Suggested Answer: No. It may escalate draft messaging and FaceTime/text handoff prompts only.
Rationale: CareSight remains a caregiver-awareness prototype, not an emergency dispatch or medical-device system.

Question: Should old demo events be deleted to clean the dashboard?
Suggested Answer: No. Add demo filters or archive/backlog states; deletion remains forbidden.
Rationale: SQLite is the blackbox source of truth and should preserve audit history.
