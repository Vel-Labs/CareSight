# Contracts

`contracts/` is the canonical project truth layer.

Anything that defines project meaning, lifecycle state, schema shape, example shape, or fail-closed behavior belongs here before implementation packages consume it.

## Contents

- `lifecycle.md`: lifecycle states and allowed movement.
- `fail-closed-rules.md`: conditions that must block promotion or execution.
- `llm-provider-contract.md`: provider contract and readiness rules for LLM integrations.
- `schemas/`: JSON Schemas for canonical project artifacts.
- `examples/valid/`: examples that must pass contract validation.
- `examples/invalid/`: examples that must fail contract validation.

## Sprint 01 Demo Surface Contracts

- `human-review-packet`: a read-only, SQLite-derived packet for compact human review decisions. It can expose available human actions, but it does not perform review lifecycle changes.
- `blackbox-receipt`: a read-only, SQLite-derived receipt for a selected event's observation, review, journal, handoff, dashboard, and alert provenance. Incomplete receipts must declare blockers instead of synthesizing success.

## Sprint 02 Agent Assist Contracts

- `forbidden-claim-vocabulary`: canonical blocked claim categories and bounded replacement language for agent and TTS outputs.
- `agent-draft`: draft-only caregiver, note, handoff, and audit text derived from SQLite-backed records. Validated drafts must avoid forbidden claims; blocked drafts must preserve block reasons and a safe rewrite.
- `agent-action-request`: staged-only local action intent. The contract requires `stage: staged`, `execution_state: not_executed`, and human approval before any future downstream execution lane exists. iMessage/FaceTime-style handoffs require allowlisted contact IDs and may offer bounded response options such as a text acknowledgement, local screen capture by request, or FaceTime handoff by request.
- `tts-utterance`: validated draft-only utterance text for a neutral system voice. It forbids voice cloning and the same overclaim patterns as agent drafts.

## Phase 1 Live Handoff Contracts

- `media-sharing-policy`: event-scoped approval for images, screenshots, clips, or text excerpts before they leave the local device. Phase 1 permits approved event-scoped snapshot metadata and blocks raw video by default.
- `reply-gated-handoff`: receipt shape for text replies that authorize a bounded follow-up such as FaceTime. FaceTime continuation requires an allowed follow-up action, affirmative reply classification, target verification, and an execution receipt.

## Phase 3 Runtime and Model Governance Contracts

- `runtime-validation-receipt`: machine-readable proof for non-invasive runtime probes and heartbeat checks. Receipts distinguish unit gates from camera, OBS/feed, Gemma, Hermes no-send, TTS-generation, database, disk, and demo-preflight checks. Heartbeats must preserve `no_live_send`, `no_facetime_call`, and `no_tts_playback` boundaries.
- `local-feed-exposure`: explicit policy for local MJPEG/browser preview feeds. Loopback preview remains the default; LAN binding requires operator approval, token protection, an expiration, and privacy-warning acknowledgement.
- `model-manifest`: source, license, checksum, local path, runtime, purpose lane, validation command, allowed uses, and blocked uses for local models.
- `retention-policy`: local retention/export/share policy for SQLite events, snapshots, clips, journal entries, model outputs, and execution attempts.
- `privacy-redaction-receipt`: receipt for text redaction attempts. Privacy filters are PII detection/masking aids only; they are not anonymization, HIPAA compliance, or safety guarantees.

## Phase 4 Care Intelligence Contracts

- `reply-gated-handoff`: FaceTime continuation now uses explicit reply classes: `yes`, `no`, `ambiguous`, `opportunity`, and `timeout`. Only `yes` with the configured phrase can authorize a live handoff.
- `privacy-redaction-receipt`: journal export review records labels, redaction status, and human-review-required boundaries while preserving the canonical local journal text.

## Sprint 03 Appearance Profile Contracts

- `appearance-profile`: non-biometric, same-day local appearance descriptors for care context. The contract requires `identity_boundary: non_biometric_daily_appearance_only`, distinguishes runtime observations from seeded fixtures with `descriptor_source` and `descriptor_status`, permits only bounded role assignments, and forbids biometric identity, face recognition, named-person identification, and cross-day identity claims.

## Ownership

- Contracts may be read by tests, `packages/core/`, docs, future adapters, and future demos.
- Tests must consume these files directly instead of redefining schemas or examples.
- `packages/core/` may enforce contracts, but it must not become the source of truth.
- Adapters, demos, and provider integrations are downstream and out of scope for this baseline.

## Change rule

Any contract change must update:

- relevant valid and invalid examples
- contract validation tests
- current-state or roadmap routing
- `DECISIONS.md` when the change affects architecture or authority
- `CHANGELOG.md`
