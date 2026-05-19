# Scope Decisions

## Hackathon product goal

Demonstrate a complete care event loop:

```text
local camera → YOLO26 MLX → care event → local database → journal/alert → caregiver action
```

Not every integration needs to be complete. The strongest demo is a reliable engine with one or two polished extensions.

---

# Build now

## Must build

- YOLO26 MLX webcam inference.
- One reliable camera source.
- Zone-based event detection.
- `possible_floor_stay` event.
- `medication_routine_likely_observed` event or a simpler routine proxy.
- SQLite event storage.
- Local dashboard or clear terminal/UI event timeline.
- Daily journal output.
- One alert mechanism.
- README, benchmark, demo video.

## Should build if time allows

- OBS scene switching.
- FaceTime handoff link.
- Apple Shortcut for message/journal.
- Gemma summary from event JSON.
- Pet event demonstration.
- Role/permission config demo.

## Should not build during hackathon unless already easy

- Ring integration.
- Nest integration.
- ONVIF discovery.
- Fully secure remote access.
- Clinical compliance workflows.
- Custom fine-tuning.
- Voice cloning.
- Multi-resident facility mode.
- Automated emergency dispatch.

---

# Integration philosophy

## Demo with local controllable inputs

Use a webcam, iPhone Continuity Camera, or local RTSP test stream. Avoid depending on third-party cloud APIs during the submission demo.

## Document future adapters

It is acceptable and impressive to show adapter interfaces for Ring/Nest/Home Assistant, as long as the README is honest about MVP support.

## Keep magic behind feature flags

```text
--enable-obs
--enable-shortcuts
--enable-gemma
--enable-pet-demo
```

If a feature fails, the core product should still run.

---

# Language scope

Use careful labels:

| Avoid | Use instead |
|---|---|
| Fall detected | Possible floor-stay event |
| Took medicine | Medication routine likely observed |
| Patient | Loved one / resident / person being cared for |
| Emergency dispatch | Caregiver escalation / FaceTime handoff |
| Proof of care | Care observation + human confirmation |
| Surveillance | Local care awareness |

---

# Technical scope cuts

## Floor-stay detection

Do not try to solve all fall detection. Use a transparent heuristic:

- person detected in a floor zone
- vertical position / bbox shape suggests low posture
- low movement persists for N seconds
- optional zone excludes couch/bed

## Medication routine

Do not claim actual ingestion. Use evidence:

- person present at medication station
- object evidence such as bottle/cup/organizer if detectable
- routine window active
- event persists
- human confirmation pending

## Pet logic

Use pet logic to show system range, not as the core. One event is enough:

- dog/cat in bowl zone for N seconds

## Alerts

One channel is enough for MVP:

- local dashboard alert
- macOS notification
- Shortcut-driven message
- mock SMS in terminal

---

# What to fake responsibly

## FaceTime live view

Acceptable MVP behavior:

- Button opens FaceTime URL.
- OBS Virtual Camera is configured manually.
- README explains setup.

Avoid claiming fully automatic call connection if macOS prompts or permissions interfere.

## Apple Notes

Acceptable MVP behavior:

- Generate Markdown daily journal.
- Optional Shortcut appends to Notes.

Do not make Notes the source of truth.

## Gemma/OpenClaw

Acceptable MVP behavior:

- Convert event JSON into a human summary.
- Recommend an action from an allow-list.

Do not let the LLM execute arbitrary scripts.

---

# Final MVP checklist

A submission is strong if it answers:

- What real care problem does this solve?
- Why must it run on-device?
- How does YOLO26 MLX create meaningful events?
- What happens after an event is detected?
- How is the cared-for person spared from needing to operate anything?
- What is local, what is shared, and who can see it?
- What are the limitations?
