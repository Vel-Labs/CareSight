# Hackathon State and Cleanup Plan

Date: 2026-05-23

Scope: compare CareSight hackathon goals with the current project state, define the stable cut point, and identify cleanup candidates without moving or deleting files.

## Stable Cut Point

The current stable cut point is:

```text
owner-authorized local Tapo RTSP feeds
  -> YOLO26 MLX live detector processes
  -> calibrated floor-plane overlay and floor-zone scoring
  -> local SQLite event/audit path
  -> OBS browser-source presentation
  -> human-review bounded handoff surfaces
```

This is the right hackathon cut because it proves the local-first care loop with visible live feeds while preserving the project boundary: possible events, local evidence, and human review. It should not expand into true metric depth, medical certainty, autonomous dispatch, or cloud camera integrations before the demo story is stable.

## Hackathon Goal Check

| Goal | Current state | Status | Next needed |
| --- | --- | --- | --- |
| On-device YOLO26 MLX inference | YOLO26 MLX is running from the local venv against live Tapo RTSP feeds. | Demo-ready for current machine | Keep startup command and model path documented. |
| Meaningful care event | `possible_floor_stay` is implemented with same-track dwell, occlusion grace, dedupe evidence, and calibrated floor-plane support. | Implemented; live event proof still needs final operator receipt after the latest calibration | Run one bounded operator proof using the current Tapo setup and save the resulting receipt. |
| Local structured memory | SQLite event, observation, review, journal, draft, action, and appearance paths exist. | Implemented | Keep SQLite as canonical; avoid dashboard or OBS becoming truth. |
| Human-readable care journal | Review packet, blackbox receipt, dashboard, and journal paths exist. | Implemented | Create a single judge-facing demo script that references one current event ID. |
| Caregiver alert | Gemma draft, action-request staging, Hermes no-send, iMessage/FaceTime/TTS ladders exist. | Staged; not fully production-validated | Use one approved demo route: no-send or one explicitly approved live handoff, not both. |
| Set-and-forget resident experience | OBS plus detached detector launcher reduces operator work; camera setup still needs local config and manual launch. | Partially implemented | Add launchd/app auto-start later; not needed for hackathon cut. |
| Two v1 care events | `possible_floor_stay`, medication, and hydration likely-observed policies exist in code/docs. | Implemented in deterministic path; demo emphasis should remain floor-stay unless routine proof is refreshed | Decide whether routine event is in the live demo or documented as implemented support. |
| Multi-camera support | Living Room and Kitchen Tapo feeds run as separate detector processes on ports 8766 and 8767. | Implemented for current demo architecture | Future: single ingest/restream worker after adoption signal. |

## What Should Stay In The Hackathon Demo

- Local Tapo camera feeds, not cloud camera accounts.
- YOLO26 MLX as the vision lane.
- Calibrated floor-plane polygons as the current low-risk depth approximation.
- `possible_floor_stay` wording, not fall detection or medical emergency wording.
- OBS as the visible reviewer surface.
- SQLite receipts and Markdown review artifacts as the proof layer.
- Human approval before any live iMessage, FaceTime, or TTS action.

## What Should Move To Future Layers

- True depth perception from depth/stereo hardware or monocular-depth models.
- A single restream/ingest worker to reduce camera connections and avoid one YOLO process per feed.
- WebRTC/MSE low-latency live view outside OBS.
- MQTT integration.
- Event-scoped recording clips with retention controls.
- Camera setup wizard and room/zone calibration UI.
- launchd auto-start and appliance health page.
- Remote caregiver portal and role-based sharing.

## Directory Sprawl Findings

Tracked file counts from the current Git index:

| Area | Count | Readability issue |
| --- | ---: | --- |
| `docs/` | 216 | The useful story is buried under audit history, sprint packs, imported docs, and generated GoalBuddy boards. |
| `docs/audits/` | 87 | Strong evidence trail, but too noisy for judge/operator entry. |
| `docs/caresight_hub_docs_pack/` | 35 | Useful source pack, but it duplicates routed docs and should be treated as imported reference material. |
| `docs/goals/` | 12 tracked files plus generated board assets | Helpful for agent history, poor for public navigation. |
| `apps/caresight-hub/scripts/` | 30 | Many operator commands are real; needs a small "run these three" entrypoint. |
| `apps/caresight-hub/tests/` | 21 | Acceptable, but test names should map to sprint surfaces in docs. |

Ignored local runtime sprawl also exists:

- `apps/caresight-hub/.venv/`
- `apps/caresight-hub/data/`
- `apps/caresight-hub/config/*.local.json`
- `apps/caresight-hub/config/live-demo.local`

These should remain ignored because they contain local environment state, camera credentials, runtime data, and generated artifacts. The cleanup task is to make them visibly routed, not to commit them.

## Cleanup Scope

No files should be moved until this plan is approved. Recommended cleanup order:

1. Create a short judge/operator landing page.
   - Candidate path: `docs/hackathon/current-demo-status.md`
   - It should name the current demo command, OBS URLs, safety boundaries, and proof receipts.

2. Split docs into three visible lanes.
   - Active: README, getting started, commands, architecture, current state, demo status.
   - Evidence: audits and production-validation receipts.
   - Reference/archive: imported docs pack, old GoalBuddy runs, retry receipts, source notes.

3. Add archive indexes before moving anything.
   - Candidate path: `docs/archive-candidates/2026-05-23-cleanup-review.md`
   - Include old retry receipts, completed GoalBuddy boards, imported docs pack, and superseded sprint plans as review candidates only.

4. Reduce operator command surface.
   - Keep `caresight_detector_start.py --appearance-overlay --stop-existing` as the live feed start path.
   - Keep `docs/cli/COMMANDS.md` as complete registry.
   - Add a small "Demo Runbook" that only shows the commands needed for the current demo.

5. Preserve auditability.
   - Do not delete old receipts.
   - If old receipts move later, keep a redirect/index entry.
   - Regenerate `docs/FILE_TREE.md` after any approved move.

## Recommended Next Work

1. Run one current calibrated-floor-plane live proof and save a redacted audit receipt.
2. Create `docs/hackathon/current-demo-status.md` as the human-facing entrypoint.
3. Create an archive-candidate review file; do not move files yet.
4. Decide whether the hackathon demo includes medication/hydration likely-observed live proof or keeps it as implemented-but-not-primary.
5. After the demo story is stable, consider future perception layers: monocular depth, stereo/depth hardware, pose estimation, and true segmentation. These should remain future work until the current floor-plane cut proves useful.
