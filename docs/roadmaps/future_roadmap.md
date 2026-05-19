# CareSight Hub — Future Roadmap

This document captures the roadmap beyond the hackathon MVP.

The hackathon build is intentionally bounded:

```text
YOLO26 MLX local perception
+ SQLite local memory
+ daily care journal
+ caregiver alert
+ optional OBS / FaceTime handoff
```

Future versions expand that into a fuller local-first care platform.

---

## Guiding principle

CareSight should become a **set-and-forget care appliance**.

The person at the home should not need to:

- press a button
- remember a workflow
- open an app
- answer a prompt
- understand the base unit
- operate a phone during a care event

The system should quietly observe configured care-relevant signals, store structured local memory, and involve the right human only when needed.

---

# 1. Product roadmap

## v3 — Home pilot

Goal:

```text
Turn the hackathon demo into a reliable home base unit.
```

Capabilities:

- multi-camera support
- RTSP camera input
- camera health checks
- reconnect logic
- local retention settings
- local dashboard authentication
- care routines configuration
- caregiver acknowledgement workflow
- alert escalation if no acknowledgement
- privacy mode / quiet hours
- launchd-based auto-start on macOS
- dedicated Mac user profile for the appliance

Key product question:

> Can this run for a week in a real home without manual intervention?

---

## v4 — Care circle

Goal:

```text
Make delegated care the core product experience.
```

Capabilities:

- family caregiver role
- nurse / care worker role
- temporary caregiver role
- pet sitter role
- role-based event visibility
- time-limited access
- subject-specific access
- acknowledgement and confirmation workflows
- shared daily journal
- caregiver comment thread
- false-positive correction
- missed-routine alerts

Example:

```text
A pet sitter can confirm feeding events for the dog this weekend,
but cannot view medication notes for the person living in the home.
```

---

## v5 — Appliance setup and onboarding

Goal:

```text
Make the system installable by a non-technical family member or installer.
```

Capabilities:

- setup wizard
- camera discovery
- room/zone labeling
- routine templates
- caregiver invite flow
- test alert button
- event simulation mode
- permissions walkthrough
- privacy explanation
- local backup/export
- restore from backup
- appliance health page

Installation target:

```text
Mac mini + local cameras + CareSight app
```

---

## v6 — Remote caregiver portal

Goal:

```text
Give caregivers a secure way to view only the events they are allowed to see.
```

Capabilities:

- event timeline
- live event page
- acknowledgement buttons
- journal view
- note/comment workflow
- limited snapshot/event clip review
- no default raw-video cloud upload
- device health alerts
- caregiver notification preferences

Important design rule:

```text
Remote access should expose care events first, not continuous surveillance by default.
```

---

# 2. Enterprise roadmap

## Enterprise wedge

The enterprise value is not “camera monitoring.”

It is:

```text
privacy-preserving local event documentation
+ role-based acknowledgement
+ facility operations visibility
+ audit-ready care workflows
```

Potential markets:

- assisted living facilities
- memory care facilities
- small nursing homes
- in-home care agencies
- pet care businesses
- independent living communities
- clinics with non-diagnostic safety monitoring
- workplace safety / occupancy pilots

---

## v7 — Small facility pilot

Capabilities:

- multi-room support
- multiple residents/subjects
- staff role permissions
- shift handoff summaries
- escalation by staff group
- audit exports
- local facility dashboard
- event retention rules
- facility-wide device health
- incident review workflow

Example workflows:

```text
resident floor-stay event
→ staff alert
→ staff acknowledgement
→ family summary if configured
→ shift handoff note
```

```text
care routine likely observed
→ nurse confirmation
→ daily care journal
→ audit entry
```

---

## v8 — Fleet and admin controls

Capabilities:

- multi-site management
- device enrollment
- update management
- camera inventory
- policy templates
- per-site retention rules
- staff directory sync
- admin audit logs
- uptime monitoring
- incident exports
- on-prem deployment option

Enterprise expectations:

- clear data ownership
- encryption at rest
- audit trail
- access revocation
- administrator controls
- supportable installation
- model performance reporting

---

# 3. Care home / nursing home roadmap

## Chain of care, not chain of custody

The product should use the phrase **chain of care**.

Recommended model:

```text
Observed by system
→ summarized by local agent
→ acknowledged by staff
→ confirmed or corrected by authorized human
→ recorded in audit log
```

Avoid:

```text
System proves medication was taken.
```

Prefer:

```text
Medication routine likely observed and confirmed by authorized caregiver.
```

---

## Plan-of-care support

Capabilities:

- configured care routines
- morning/evening medication windows
- meal/hydration observations
- mobility observations
- room safety observations
- missed-routine escalation
- staff confirmation
- daily/shift summary
- family-visible summary subset
- exception reporting

Example:

```text
8:00–9:00 AM medication window
No likely routine observed by 9:15 AM
→ low-priority staff alert
→ staff confirms administered manually
→ journal records manual confirmation
```

---

## Memory care use cases

Potential capabilities:

- exit/doorway alerts
- unusual nighttime activity
- prolonged inactivity
- room-presence check
- calm local TTS prompt
- caregiver summary of interaction
- escalation if no response or repeated events

Safety note:

TTS prompts should be calm, clear, and non-deceptive. Familiar voice or cloned voice features should require explicit consent and careful safeguards.

---

## Facility safety use cases

Potential capabilities:

- blocked walkway detection
- fall-risk area observations
- door left open
- visitor/package event
- staff response time tracking
- non-identifying occupancy counts
- camera health failure alerts

---

# 4. Quality-of-life roadmap

CareSight should not only handle severe events. It should make ordinary care easier.

## Family home

Capabilities:

- package arrival
- kitchen/stove presence
- door activity
- water bottle / hydration station visible
- phone/wallet/backpack last-seen memory
- trash/recycling reminders
- routine movement check
- “no activity by expected time” check-in

## Pet care

Capabilities:

- pet food area activity
- pet left/entered room
- dog near door
- temporary pet sitter access
- feeding confirmation
- water bowl activity
- pet sitter daily summary

## Accessibility

Capabilities:

- object finder
- room object inventory
- last-seen memory
- spoken guidance
- low-vision dashboard mode
- simple caregiver summaries

## Household coordination

Capabilities:

- shared notes
- delegated tasks
- routine checklists
- “who acknowledged this?” tracking
- daily digest
- weekly trend summaries

---

# 5. HIPAA, privacy, security, and compliance roadmap

Note: the correct spelling is **HIPAA**.

The hackathon version should not claim HIPAA compliance. It should say:

```text
CareSight is a local-first prototype. Clinical/facility deployment would require formal privacy, security, regulatory, and legal review.
```

HHS describes the HIPAA Privacy Rule as establishing national standards for protecting medical records and other individually identifiable health information. HHS describes the HIPAA Security Rule as establishing national security standards for certain health information maintained or transmitted electronically by regulated entities.

References:

- HHS HIPAA Privacy Rule: https://www.hhs.gov/hipaa/for-professionals/privacy/index.html
- HHS Summary of the HIPAA Privacy Rule: https://www.hhs.gov/hipaa/for-professionals/privacy/laws-regulations/index.html
- HHS Summary of the HIPAA Security Rule: https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html
- HHS HIPAA for Professionals: https://www.hhs.gov/hipaa/for-professionals/index.html

---

## Compliance questions to resolve before clinical/facility use

- Is the deployment acting as or serving a covered entity?
- Would the vendor be a business associate?
- Is protected health information being created, stored, or transmitted?
- What data is stored locally?
- What data leaves the home/facility?
- Who can access event records?
- What is the retention policy?
- How are access revocations handled?
- How are audit logs protected?
- What happens after a breach or device loss?
- Are any features medical-device-like?
- Is emergency dispatch involved?
- Are state privacy laws implicated?

---

## Security roadmap

Capabilities:

- encrypted local database
- secure key storage
- local user authentication
- caregiver authentication
- role-based access control
- audit log for every access/change
- retention policy controls
- device lock / tamper detection
- backup encryption
- signed software updates
- least-privilege service accounts
- secure remote access model
- vulnerability disclosure policy
- incident response playbook

---

## Privacy roadmap

Capabilities:

- raw video disabled for sharing by default
- event summaries before live video
- no face recognition by default
- no bedroom cameras by default, or strong privacy controls
- bathroom camera prohibition
- visible installation consent workflow
- subject/caregiver consent records
- per-room privacy settings
- local-only mode
- event-only retention
- optional snapshot redaction
- caregiver access expiration
- data export and deletion flows

---

## Regulatory safety posture

CareSight should not claim:

- medical diagnosis
- certified fall detection
- emergency replacement
- guaranteed medication administration proof
- autonomous emergency response
- HIPAA compliance without formal review

CareSight can claim:

- local event observation
- caregiver notification
- daily care journaling
- structured event records
- human acknowledgement and confirmation
- privacy-first design intent

---

# 6. Camera and integration roadmap

## Local-first camera sources

Priority order:

1. USB webcam
2. Mac camera
3. iPhone Continuity Camera
4. RTSP stream
5. ONVIF discovery
6. Home Assistant camera entity
7. vendor cloud adapters

## RTSP / ONVIF

Future capabilities:

- camera discovery
- credential storage
- stream health checks
- reconnect logic
- camera grouping by room
- zone calibration UI
- FPS/resolution tuning

## Home Assistant

Potential value:

- use existing home camera entities
- use smart home events as context
- door/motion sensors as secondary signals
- trigger automations from CareSight events

## Ring / Nest / Google Home

Treat as optional adapters, not the core product.

Positioning:

```text
CareSight can process a user-authorized stream or event from these ecosystems when available,
but the local-first product should not depend on consumer cloud camera APIs.
```

---

# 7. OBS, FaceTime, and live-view roadmap

## OBS role

OBS should be the human presentation layer, not the main inference source.

```text
CareSight analyzes raw feeds.
OBS displays the right event scene to caregivers.
```

Capabilities:

- event scene switching
- overlay summary updates
- virtual camera output
- local event recording if allowed
- caregiver-safe scene composition
- idle/privacy scene
- multi-camera mosaic

## FaceTime role

FaceTime should be a familiar handoff channel.

Capabilities:

- caregiver call button
- FaceTime URL handoff
- OBS Virtual Camera selected as video source
- fallback to event page or text alert

Important limitation:

FaceTime handoff is not emergency dispatch and should not be the only escalation mechanism.

---

# 8. Agent and language-model roadmap

## Local Gemma role

Gemma should summarize and format structured events.

Good tasks:

- caregiver-friendly summary
- daily journal wording
- weekly digest
- missed-routine explanation
- alert template selection
- natural-language search over event history
- transcript summary after an interaction

Avoid:

- raw-video reasoning as the primary perception layer
- autonomous medical judgment
- arbitrary tool execution
- unbounded shell access
- unsupervised emergency escalation

## OpenClaw / tool orchestration role

Potential capabilities:

- event-driven hooks
- iMessage or messaging channels
- scripted local actions
- note creation
- daily summary delivery
- caregiver command parsing

Safety boundary:

```text
The agent receives structured event JSON and can call only approved tools.
The deterministic policy engine decides what actions are allowed.
```

---

# 9. Model and performance roadmap

## Model variants

Future benchmarking should compare:

- `yolo26n` for low-latency real-time use
- `yolo26s` for balanced accuracy
- larger variants only if hardware allows
- segmentation variants for paths/shelf/room geometry

## Optimization features

- adaptive frame rate
- frame skipping
- tracking between inference frames
- event-triggered high-resolution inference
- camera-specific model settings
- low-power mode
- offline benchmark script
- per-device model recommendation

## Custom model roadmap

Potential fine-tune classes:

- pill bottle
- walker
- cane
- wheelchair
- remote control
- keys
- medication organizer
- pet bowl
- package
- stove/oven context
- safety equipment

Validation requirement:

Custom models need precision/recall evaluation before being trusted for alerts.

---

# 10. Data, memory, and analytics roadmap

## Local memory

SQLite remains the local source of truth.

Future data features:

- full-text search
- JSON event payloads
- event replay
- false-positive labels
- caregiver corrections
- weekly trend summaries
- routine adherence metrics
- camera reliability metrics
- export/import
- encrypted backup

## Analytics

Useful analytics:

- missed medication windows
- acknowledgement time
- recurring anomaly patterns
- camera downtime
- event frequency by room
- pet feeding regularity
- nighttime activity changes
- routine consistency

Avoid overreach:

```text
Do not turn ordinary care analytics into diagnosis claims.
```

---

# 11. Commercial roadmap

## Phase 1 — open-source showcase

Goal:

```text
Win attention by shipping a polished local-first care demo.
```

Audience:

- hackathon judges
- Apple/MLX builders
- WebAI/YOLO26 community
- edge AI companies
- home automation builders

## Phase 2 — family/home beta

Goal:

```text
Test reliability and usefulness in real homes.
```

Potential offer:

```text
CareSight app
+ Mac mini setup guide
+ recommended camera list
+ local-only install
```

## Phase 3 — installer / agency partnership

Goal:

```text
Make setup available through caregivers, home automation installers, or in-home care agencies.
```

## Phase 4 — facility pilot

Goal:

```text
Run structured pilots with assisted living or home-care providers under appropriate legal/privacy review.
```

## Phase 5 — appliance bundle

Goal:

```text
Sell or certify a preconfigured base unit.
```

Potential package:

```text
Mac mini or equivalent edge device
+ preconfigured CareSight
+ camera kit
+ installation wizard
+ support plan
```

---

# 12. Research and validation roadmap

Before high-stakes deployments, validate:

- false positive rate
- false negative rate
- alert fatigue
- caregiver response behavior
- resident privacy expectations
- room/camera placement
- medication routine ambiguity
- fall/floor-stay ambiguity
- pet event accuracy
- network reliability
- hardware reliability
- usability by non-technical caregivers

Suggested evaluation design:

```text
controlled staged events
→ real-home shadow mode
→ caregiver feedback
→ threshold tuning
→ limited alert mode
→ expanded pilot
```

---

# 13. Long-term product vision

CareSight becomes:

```text
a local-first care operating layer for homes and small care environments
```

Not a surveillance product. Not a medical diagnosis system. Not a cloud camera clone.

The best long-term promise is:

> **CareSight gives a place its own memory, so caregivers can act sooner and document care better without requiring the person being cared for to operate anything.**
