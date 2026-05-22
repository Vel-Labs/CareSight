# Sprint 02 Production Acceptance

Status: not production-accepted.

CareSight Sprint 02 is substantially validated for local, no-send operation:

- Local Gemma E2B runs through `mlx-vlm.server`.
- Case A produced a bounded `provider: gemma_mlx` draft from SQLite-derived context.
- Case A staged an urgent allowlisted action request and Hermes payload.
- Hermes no-send preflight passed with `external_action_performed: false`.
- Case B stayed non-escalating because it was a normal/no-event observation check.
- TTS generated a local WAV from the Gemma Case A message without playback.

Remaining gates before Sprint 02 production acceptance:

- Human approval of the exact Gemma message wording.
- Human-approved local TTS playback and audibility/tone confirmation.
- Privacy-safe OBS/screen scene confirmation.
- Approved Apple contact mapping outside Git.
- One human-approved allowlisted iMessage test, if still in scope.
- One human-approved visual/FaceTime handoff test, if still in scope.

Human feedback recorded on 2026-05-21:

- Gemma wording is approved, with a follow-up request to add time relevance, unresolved-alert cadence, and resolution updates in the alert lifecycle.
- TTS playback functionally works and sounds clean; Dakota voice is approved for the shorter message.
- OBS direction is approved around websocket-created scenes with browser-source overlays, and scenes were created. Dynamic event/recent-activity overlay updates and privacy confirmation remain pending before FaceTime.
- `contact_emergency_primary` is approved for one iMessage test and one FaceTime test, with the real contact identity kept out of Git.
- Live iMessage text is approved, but the send has not been executed.
- A no-send post-event automation path is available through `v0_floor_stay_live.py --auto-agent-dry-run`, wiring event persistence to OBS overlay update, Gemma draft, staged iMessage request, and Hermes dry-run receipt.

No live iMessage, FaceTime call, Apple Notes write, OBS capture, or TTS playback was performed by this receipt.
