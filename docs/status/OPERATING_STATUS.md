# Operating Status

This page is the short status layer for operators and future agents. It separates deterministic proof, local runtime probes, and remaining human/live gates.

## Current Feature Status

| Area | Status | Notes |
| --- | --- | --- |
| Contracts and examples | Implemented and covered by the contract corpus. | Includes live-handoff, media policy, runtime validation, model manifest, feed exposure, retention, and privacy-redaction contracts. |
| Python runtime loop | Implemented for the current hackathon path. | `possible_floor_stay`, review lifecycle, SQLite blackbox rows, OBS feed, no-event receipts, and post-event no-send/live-gated chains exist. |
| Review and audit surfaces | Implemented. | Dashboard, review packet, blackbox receipt, escalation receipt, journal, and audit commands read from SQLite. |
| Agent assistance | Staged and bounded. | Drafting, action requests, Hermes payloads, and dry-run attempts are local and no-send unless a separate human-approved live path is used. |
| Camera and OBS runtime | Partially validated locally. | Unit checks cover parsing/redaction; live camera, OBS websocket/feed, and scene privacy remain operator/runtime gates. |
| Live caregiver handoff | Implemented behind human gates, not unattended. | iMessage, FaceTime, reply watching, and TTS playback require approved contact targets and explicit human approval. |
| Production readiness | Not claimed. | Remaining runtime gates below must be closed before stronger readiness language. |

## Tests Completed

Latest plan-known full deterministic gate: `npm run check` passed on 2026-05-24 after Phase 4 resolution notes.

The deterministic gate covers:

- scaffold/file-tree validation
- contract schema and example validation
- TypeScript focused and full tests
- TypeScript typecheck
- Python unit tests under `apps/caresight-hub/tests`

Phase 5 validation should rerun at least:

```bash
npm run validate:scaffold
npm run validate:contracts
npm run test:focused
npm test
npm run typecheck
npm run py:check
npm run check
```

## Remaining Work

The following are runtime or operator-owned checks, not unit-test substitutes:

- camera probes against ignored local configs
- detector MJPEG feed and OBS browser-source verification
- OBS websocket scene/privacy confirmation
- Gemma endpoint readiness on the target machine
- Hermes no-send dry run from a real staged request
- iMessage dry run and one human-approved live send
- FaceTime setup and approved reply-gated handoff
- TTS generation and separate human-approved playback
- periodic heartbeat receipts
- multi-camera event-loop proof before production-operation claims

## Safe Command Classes

Use [`docs/cli/COMMANDS.md`](../cli/COMMANDS.md) for the command index.

- `agent-safe-read`: safe for agents to run unattended when local prerequisites exist.
- `manual-operator`: requires a human/operator because it uses hardware, windows, local services, downloads, or long-running loops.
- `human-review-required`: requires explicit human approval because it changes lifecycle state or performs live handoff behavior.

## Heartbeat

Heartbeat command:

```bash
python3 apps/caresight-hub/scripts/caresight_demo_preflight.py --heartbeat --json
```

Heartbeat receipts must preserve these boundaries:

- no live message send
- no FaceTime call
- no TTS playback
- no autonomous emergency dispatch
- no medical or HIPAA compliance claim

## Feed Exposure

Local MJPEG feeds are loopback-only by default. LAN exposure requires:

```bash
--allow-lan-preview --preview-token <token> --ack-lan-preview-risk
```

The startup receipt must include the `local-feed-exposure` policy shape.
