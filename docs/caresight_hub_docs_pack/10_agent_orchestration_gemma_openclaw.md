# Agent Orchestration: Gemma and OpenClaw

## Core boundary

YOLO26 MLX is the vision engine. Gemma/OpenClaw are not the vision engine.

```text
YOLO26 MLX:
  What is visible? Where? For how long?

Rules engine:
  Is this a configured care event? How severe?

Gemma/OpenClaw:
  How should this be summarized and routed through approved tools?
```

---

# What the local LLM should do

Good uses:

- caregiver-friendly summary
- daily journal wording
- alert template selection
- prior event summary
- answer simple caregiver questions from the local event log
- parse caregiver reply such as “mark this confirmed”
- recommend action from an allow-list

Bad uses:

- raw emergency authority
- unbounded shell execution
- deciding medical truth
- watching raw video continuously
- inventing evidence
- autonomous 911 dispatch

---

# Event-driven wake hook

The LLM should sleep until a meaningful event occurs.

```text
YOLO frame loop
  → event detector threshold crossed
  → event inserted into SQLite
  → local agent receives event JSON
  → summary/action recommendation produced
  → approved action adapter executes
```

This keeps compute and privacy under control.

---

# Structured event input

```json
{
  "event_id": "evt_20260518_102204",
  "event_type": "possible_floor_stay",
  "room": "Living Room",
  "camera": "living_room_cam",
  "duration_seconds": 31,
  "confidence_label": "high",
  "severity": "high",
  "evidence": {
    "objects": ["person"],
    "zone": "floor_zone",
    "movement": "low",
    "raw_video_uploaded": false
  },
  "allowed_actions": [
    "create_journal_entry",
    "notify_primary_caregiver",
    "switch_obs_event_view",
    "offer_facetime"
  ]
}
```

---

# Structured agent output

```json
{
  "caregiver_summary": "Possible floor-stay event in Living Room. The person has been low in the floor zone for 31 seconds. Raw video remains local.",
  "journal_entry": "10:22 AM — Possible floor-stay event observed in Living Room. Awaiting caregiver acknowledgement.",
  "recommended_action": "notify_primary_caregiver",
  "requires_human_confirmation": true,
  "do_not_claim": ["fall confirmed", "injury detected", "medicine taken"]
}
```

---

# Gemma via MLX

Gemma can run locally through MLX tooling. For this project, prefer a smaller model variant first and expose it through a local endpoint if needed.

## Example conceptual flow

```text
CareSight event JSON
  → local Gemma endpoint
  → JSON summary output
  → policy guard validates allowed action
  → action adapter runs
```

## Prompt guardrail

```text
You are CareSight's local event summarizer. You may only summarize evidence present in the JSON. Do not diagnose injury, confirm medication ingestion, or recommend emergency dispatch. Choose recommended_action only from allowed_actions.
```

---

# OpenClaw role

OpenClaw can be a gateway/tool orchestration layer for channels and local hooks.

Potential uses:

- iMessage channel experiments
- event-driven hooks
- multi-channel caregiver alerts
- local assistant workflows
- memory/history interaction

## Security boundary

Treat inbound messages as untrusted. Do not expose arbitrary host tools to care workflows. Route all tool calls through a narrow allow-list.

---

# Policy guard

Before executing any agent-recommended action:

1. Validate JSON schema.
2. Verify action is in `allowed_actions`.
3. Verify role permissions.
4. Verify severity threshold.
5. Log decision to audit log.
6. Execute action adapter.

## Example policy rule

```python
if action not in event.allowed_actions:
    reject("action_not_allowed")

if action == "offer_facetime" and event.severity not in ["high", "urgent"]:
    reject("severity_too_low")
```

---

# Voice/TTS roadmap

## MVP

Use generic TTS or pre-recorded messages.

Example:

> CareSight detected a possible safety event. A caregiver has been notified.

## Future

Consent-based familiar voice prompts may be useful, but avoid unconsented voice cloning. Always log when synthetic voice or pre-recorded voice is used.

---

# Recommended MVP implementation

For v1, skip OpenClaw unless already comfortable with it.

For v2 stretch:

- Add a Gemma summarizer function that takes event JSON and returns summary JSON.
- Add OpenClaw as documented future adapter or limited hook demo.
- Keep core action execution inside CareSight's own policy guard.
