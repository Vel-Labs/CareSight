# Security, Privacy, and Compliance Notes

## Product stance

CareSight Hub should be privacy-first and local-first.

Default promise:

- raw video stays local
- event metadata is stored locally
- alerts share summaries by default
- snapshots/clips are opt-in
- access is role-based
- the cared-for person does not need to operate the system

---

# Non-medical-device framing

The MVP should not claim:

- medical diagnosis
- confirmed fall detection
- confirmed medication ingestion
- emergency dispatch
- replacement for Life Alert or clinical monitoring
- HIPAA compliance

Use language such as:

- possible floor-stay event
- medication routine likely observed
- caregiver awareness
- event documentation
- human confirmation required
- supplemental safety layer

---

# HIPAA / facility path

For home/family MVP, HIPAA may not apply depending on deployment and entities involved. For clinical/facility deployment, formal legal/compliance review is required.

Future facility versions need:

- access control
- audit logs
- encryption
- retention policy
- deletion/export workflows
- breach/security procedures
- business associate considerations where applicable
- staff training and operational controls

---

# Privacy boundaries

## Camera placement

Recommended:

- living room
- kitchen
- front door
- hallway
- medication station
- pet area

Avoid or block by default:

- bathrooms
- private bedrooms unless explicitly configured and legally/ethically appropriate

## Video retention

Recommended MVP:

- no raw video storage by default
- event metadata only
- optional latest snapshot disabled by default or manually approved

## LLM privacy

The local LLM should receive structured event JSON, not continuous raw video.

---

# Role-based access

Access should be scoped by:

- person/subject
- camera
- event type
- time window
- severity
- role

Example:

```text
Pet sitter can confirm pet events this weekend.
Pet sitter cannot see elder medication notes or living-room safety events.
```

---

# Agent safety

If using Gemma/OpenClaw:

- Treat inbound messages as untrusted.
- Use an allow-list of actions.
- Validate JSON output.
- Log all tool actions.
- Keep command execution sandboxed.
- Do not let the agent call arbitrary shell scripts.
- Do not let the agent change camera/permission settings without authorization.

---

# Alert safety

Avoid fully autonomous emergency actions in MVP.

Recommended escalation:

```text
event observed
  → caregiver alert
  → caregiver acknowledgement
  → secondary caregiver if no acknowledgement
  → optional FaceTime handoff
```

If future versions support emergency-service integrations, they require legal, safety, reliability, and regulatory review.

---

# Voice/TTS and memory support

Generic TTS or pre-recorded consent-based messages are safest.

Avoid unconsented voice cloning.

Safer prompt:

> CareSight detected a possible safety event. Your caregiver has been notified.

If familiar voice prompts are ever added:

- require explicit consent from voice owner
- label generated/pre-recorded voice use
- log use in audit trail
- include disabling controls

---

# OBS and live view security

- Protect OBS WebSocket with a password.
- Bind control to localhost.
- Do not expose OBS WebSocket publicly.
- Keep live view behind access controls.
- Prefer event pages with expiring links for future remote access.

---

# Camera API security

For Ring/Nest/Home Assistant/RTSP:

- store credentials securely
- never commit tokens to GitHub
- rotate tokens during demo if exposed
- separate local demo credentials from personal accounts
- document API limitations honestly

---

# README safety text

Recommended wording:

> CareSight Hub is a prototype caregiver awareness system. It is not a medical device, fall detector certification system, alarm service, or emergency dispatch product. It creates local care observations that authorized humans can acknowledge, confirm, or dismiss.
