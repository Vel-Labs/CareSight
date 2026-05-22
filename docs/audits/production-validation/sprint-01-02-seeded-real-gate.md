# Sprint 01/02 Seeded-Real A/B Gate

Status: local no-send A/B gate passed; live-action gate still pending.

Case A, concerning path:

- Sprint 01 human-readable review packet and blackbox receipt exist.
- Sprint 02 real Gemma draft exists: `docs/audits/production-validation/sprint-02/case-a-gemma-draft.json`.
- Urgent staged handoff exists: `docs/audits/production-validation/sprint-02/case-a-gemma-urgent-action-request.json`.
- Hermes no-send receipt exists: `docs/audits/production-validation/sprint-02/case-a-gemma-hermes-dry-run.json`.

Case B, normal/no-event path:

- No possible floor-stay event was persisted.
- A normal/no-event observation check was persisted as continuity proof.
- No Gemma alert, urgent action request, or Hermes invocation was created for the normal/no-event case.

Decision:

The seeded-real A/B proof is sufficient to proceed to human review of wording, contact mapping, TTS playback, OBS/visual privacy, and live-action approvals. It is not approval to send iMessage, start FaceTime, play audio, or capture/share a visual feed.

2026-05-21 human feedback advanced the gate:

- Gemma wording approved with requested time relevance and alert lifecycle follow-up/resolution additions.
- TTS playback functionally works and Dakota voice is approved with the shorter alert wording.
- OBS visual handoff direction approved as websocket-managed scenes plus browser-source overlays; scenes were created, but dynamic overlay updates and privacy confirmation remain pending.
- `contact_emergency_primary` approved for iMessage and FaceTime testing, with the real contact identity kept outside Git.
- iMessage test text is approved, but no live send has been executed yet.
