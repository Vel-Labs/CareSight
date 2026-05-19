# Six-Day Hackathon Build Plan

## Guiding principle

Build the engine first. Add magic only after the core system is stable.

The core demo should work even if OBS, FaceTime, Gemma, and Shortcuts are disabled.

---

# Day 0 / setup

## Outcome

A working repo skeleton and a proven YOLO26 MLX webcam loop.

## Tasks

- Create repository.
- Install Python environment.
- Install YOLO26 MLX.
- Convert/download `yolo26n`.
- Run basic webcam inference.
- Confirm hardware and FPS.
- Create `README.md` draft.
- Create sample config file.

## Deliverables

- `python -m caresight.vision.webcam_demo` runs.
- Screenshot or short clip of live detections.
- Initial benchmark note.

## Cut line

If anything is unstable, do not touch OBS/Gemma/Shortcuts yet.

---

# Day 1 — zones and temporal events

## Outcome

YOLO detections become care events.

## Tasks

- Add zone config.
- Add detection filtering.
- Add simple tracker or temporal smoothing.
- Implement `possible_floor_stay` event.
- Add event JSON schema.
- Add severity labels.
- Add terminal event output.

## Deliverables

- Walking around does not trigger event.
- Simulated floor-stay triggers event after threshold.
- Event object includes timestamp, duration, camera, zone, confidence, severity.

---

# Day 2 — SQLite and journal

## Outcome

Events become local memory.

## Tasks

- Create SQLite schema.
- Insert cameras, zones, events, observations, alerts, journal entries.
- Add daily Markdown journal generator.
- Add `medication_routine_likely_observed` event.
- Add routine window config.
- Add manual confirmation status.

## Deliverables

- `caresight.db` created locally.
- Events appear in `events` table.
- Daily journal file generated.
- Medication routine demo works with person + bottle/cup/zone evidence where feasible.

---

# Day 3 — local dashboard

## Outcome

A judge can understand the system visually.

## Tasks

- Build FastAPI/Streamlit dashboard.
- Display live frame or latest annotated frame.
- Show event timeline.
- Show daily journal.
- Show camera health/status.
- Show model/hardware/FPS panel.
- Add manual acknowledge/dismiss buttons.

## Deliverables

- Local web dashboard runs.
- Triggered events appear without restarting app.
- Journal updates are visible.

---

# Day 4 — alert action and README polish

## Outcome

Care event becomes caregiver action.

## Tasks

- Implement one alert channel:
  - macOS notification, Shortcut, local mock text, or console/web alert.
- Create alert templates.
- Add role config for family caregiver and temporary caregiver.
- Create README run instructions.
- Add challenge checklist.
- Add safety/non-medical disclaimer.
- Add architecture diagram.

## Deliverables

- Alert triggers when high-severity event fires.
- README can be followed by someone else.
- Demo narrative is clear.

---

# Day 5 — stretch layer: OBS / FaceTime / Gemma

## Outcome

Add product polish without destabilizing core.

## Priority order

1. OBS scene switching via obs-websocket.
2. OBS Virtual Camera scene for Event View.
3. FaceTime handoff button/link.
4. Apple Shortcut to append journal or send alert.
5. Gemma summary from event JSON.
6. Pet event as expression-range demo.

## Deliverables

- OBS scene switches to relevant event camera/view.
- FaceTime handoff opens or is shown in demo.
- Summary/journal text looks caregiver-friendly.

## Cut line

If OBS or Gemma becomes unreliable, keep them as documented stretch demos and preserve core engine.

---

# Day 6 — demo, recording, cleanup

## Outcome

A complete submission.

## Tasks

- Record 60-second video.
- Record backup longer walkthrough.
- Capture screenshots/GIFs.
- Clean repo.
- Add hardware/model/FPS table.
- Add limitations and future roadmap.
- Add social post text.
- Test clean clone/run instructions.

## Deliverables

- Public repo.
- README complete.
- 60-second demo video.
- Social post.
- Submission checklist checked.

---

# MVP risk register

## Highest risks

- Camera capture instability.
- Over-scoped integrations.
- Event false positives.
- Unclear medication detection.
- macOS automation permissions.
- OBS/FaceTime state issues.

## Mitigations

- One camera first.
- Use staged scenes.
- Use explicit zones and thresholds.
- Use language like “likely observed.”
- Keep manual fallback alert.
- Demo OBS/FaceTime as stretch, not core dependency.

---

# Final demo acceptance test

Before submitting, verify:

- App starts with one command.
- YOLO26 MLX runs locally.
- One event reliably triggers live.
- Event writes to SQLite.
- Journal updates.
- Alert or dashboard action occurs.
- README explains hardware, model variant, and limitations.
- Demo video shows the human problem and the technical solution.
