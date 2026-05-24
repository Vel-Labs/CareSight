# Validation Commands

Validation is layered. Unit and contract gates prove deterministic code behavior. Runtime probes prove local machine dependencies. Human-approved live paths remain separate gates.

## Deterministic Gates

```bash
npm run validate:scaffold
npm run validate:contracts
npm run test:focused
npm test
npm run typecheck
npm run py:check
npm run check
```

## Agent-Safe Read

| Command | Purpose | Validation |
| --- | --- | --- |
| `python3 apps/caresight-hub/scripts/live_proof_audit.py readiness --camera-authorization not_checked` | Report local live-proof readiness and camera-authorization blockers. | `test_live_proof_audit.py`. |
| `python3 apps/caresight-hub/scripts/live_proof_audit.py bundle <event_id>` | Emit a read-only audit bundle for a fresh operator-supplied event ID. | `test_live_proof_audit.py`. |

## Manual Operator

| Command | Purpose | Boundary |
| --- | --- | --- |
| `python3 apps/caresight-hub/scripts/caresight_demo_preflight.py --heartbeat --json` | Emit a non-invasive `runtime-validation-receipt`. | No camera open, no live send, no FaceTime call, no TTS playback. |
| `apps/obs-hub/tools/check_obs_live_feed.py` | Verify the detector MJPEG server and OBS browser/live-feed sources. | Run after starting `v0_floor_stay_live.py --obs-browser-feed`. |

## Policy Checks

Agent policy is enforced by runtime helpers rather than a standalone CLI command. `test_agent_policy.py` verifies allowed actions require purpose/provenance and forbidden actions fail deterministically.

## Docs Link Check

There is no dedicated package script for markdown link checking yet. Phase 5 validates docs reachability through scaffold file-tree validation plus targeted grep/spot checks for the new CLI category links.
