---
name: live-demo-validation-recovery
description: Validate or recover the CareSight live demo chain across local detector, camera feeds, OBS/browser overlay, caregiver handoff staging, FaceTime, TTS, receipts, and status-board truth without overstating proof.
license: Complete terms in LICENSE.txt
---

# Live Demo Validation Recovery

Use this skill when CareSight work touches live floor-stay validation, local
camera proof, OBS/browser-source presentation, caregiver handoff staging,
FaceTime/TTS demo behavior, or demo-terminal/status-board readiness.

## Read First

- `AGENTS.md`
- `docs/agents/AGENT_BOUNDARIES.md`
- `docs/roadmaps/CURRENT_STATE_AND_NEXT.md`
- `docs/goals/caresight-sprint-01-02-production-validation/goal.md`
- `docs/goals/caresight-sprint-04-05-camera-obs-recon/goal.md`
- `docs/cli/COMMANDS.md`
- `docs/operations/local_model_operations.md`

## Core Boundary

CareSight is a local-first caregiver-awareness demo with human review. Do not
frame it as medical diagnosis, autonomous emergency dispatch, or production
fall detection. Separate these proof states:

- deterministic implementation;
- dry-run receipt;
- local seeded-real receipt;
- live camera first-frame proof;
- OBS/browser-source visual proof;
- staged iMessage/handoff request;
- human-approved live send/call;
- FaceTime/TTS observation;
- production validation.

## Workflow

1. Establish the target lane: detector, camera, OBS/feed, handoff, FaceTime, TTS,
   status board, docs, or sprint-readiness reporting.
2. Run or inspect the local preflight before live claims. Name blockers instead
   of substituting adjacent evidence.
3. Keep outbound actions staged unless the human explicitly approves live send,
   call, write, or publish behavior for the current task.
4. For camera work, use ignored local config and the vendored YOLO/MLX Python
   environment when OpenCV dependencies are needed.
5. For floor-stay behavior, inspect event receipts and debug output before
   blaming operator placement. Track dwell, floor-zone, posture evidence, and
   track/candidate continuity separately.
6. For OBS work, prefer file-backed browser overlays and local MJPEG/feed health
   checks over brittle runtime source mutation. Treat OBS/system permission
   blockers separately from CareSight code failures.
7. For caregiver-facing review, produce Markdown for humans and JSON for
   machine/audit receipts. Do not hand raw JSON to a reviewer as the only
   human-readable surface.
8. Update audit notes, changelog, roadmap/current-state, and GoalBuddy state
   only for proof that actually exists.

## Common Local Commands

Use the repo root unless a command says otherwise.

```bash
npm run check
node scripts/check-goal-state.mjs docs/goals/caresight-sprint-01-02-production-validation
node scripts/check-goal-state.mjs docs/goals/caresight-sprint-04-05-camera-obs-recon
./scripts/open_demo_terminals.sh --print
```

Use the vendored interpreter for camera and YOLO/OpenCV paths when needed:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/caresight_camera_probe.py --help
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --help
```

## Evidence Checklist

- command, cwd, and interpreter recorded;
- source camera/feed named without exposing secrets;
- first-frame or no-event receipt path named when relevant;
- event ID, review ID, request ID, or status file path named when relevant;
- OBS scene/feed status described as observed, not assumed;
- FaceTime/TTS actions marked staged, human-approved, observed, or skipped;
- human-review and no-emergency/no-medical boundaries preserved.

## Stop Conditions

Stop and report before:

- accessing credentials or unignored private camera config;
- initiating live iMessage, FaceTime, or other outbound communication without
  current explicit approval;
- changing sprint completion state without proof-linked receipts;
- treating a system permission, OBS setup, or local model runtime blocker as a
  code bug without evidence.

## Completion Criteria

The final report names files changed, commands run, validation results, skipped
checks, proof level reached, remaining operator-owned inputs, and any blockers
that prevent stronger claims.
