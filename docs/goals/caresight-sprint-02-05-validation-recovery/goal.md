# CareSight Sprint 02-05 Validation Recovery

## Original Request

Recover from the prior premature completion claim for the Sprint 04/05 plus 02/03/04/05 audit tranche. Build a new GoalBuddy board that captures the user's corrections, expands the remaining plan, and drives real validation/resolution work instead of another shallow audit.

## Interpreted Outcome

CareSight has a corrected, evidence-heavy recovery run that:

- audits the prior Sprint 02/03/04/05 work honestly;
- expands Sprint 03 appearance validation across visibility, distance, occlusion, body coverage, and difficulty;
- deepens Sprint 04 tracking reliability with complexity-graded deterministic tests, not just live-camera handwaving;
- proves or precisely blocks Sprint 05 camera support end to end with explicit local camera assumptions, documented credential/config attempts, redacted probe receipts, and narrative output;
- researches and tests concrete Sprint 02 FaceTime/OBS/TTS resolution options rather than only restating known blockers;
- updates docs, CLI docs, changelog, and audit receipts with the corrected status and remaining gates;
- ends only when a final Judge receipt proves the owner outcome against the corrected target.

## Input Shape

Recovery plus audit of an existing, incomplete GoalBuddy run.

## Non-Negotiable Constraints

- Do not call CareSight a medical device.
- Do not claim HIPAA compliance.
- Do not implement or imply autonomous emergency dispatch.
- Do not confirm medication administration from vision alone.
- Keep `possible_floor_stay`, `likely observed`, or `possible event` language unless authorized human confirmation exists.
- Keep YOLO26 MLX as the vision lane.
- Keep Gemma/OpenClaw/Hermes as summary or orchestration only.
- Preserve the bounded loop: observation, policy, human confirmation, journal, audit.
- Preserve local-first privacy defaults and redaction.
- Do not scan networks or attempt access to cameras that are not explicitly owner-authorized.
- Do not commit downloaded third-party media, credentials, raw camera footage, private contact handles, or private snapshots.
- Do not engage live FaceTime/iMessage/TTS playback without explicit operator approval in the run.

## Corrected User Notes To Preserve

- Sprint 04 gap is not merely live-camera validation. The system needs complexity-graded deterministic testing for each target, including varying difficulty levels, visibility, occlusion, tracking churn, distance, posture, and confidence behavior.
- Sprint 05 camera support should be tested end to end where locally possible. Research default/local setup assumptions for the camera class, prove deterministic config/probe/frame/narrative behavior, and document every improvement attempt and remaining blocker.
- Sprint 02 FaceTime/OBS/TTS was not a process issue. It had known resolution/output issues for virtual camera feed and TTS audio into FaceTime. The run must investigate known issues, test alternatives, and document concrete options, not only audit blockers.
- Sprint 03 still-image validation needs many real runs across full body, partial body, obscured/occluded images, varying distance, quality, and visibility. Receipts should include confidence, difficulty, what made each case hard, and whether the descriptor was accurate, limited, or unsafe.
- Docs/changelog/CLI need a real, inspectable output that reflects the corrected plan and evidence, not just a quiet update.
- Final audit must not call the tranche complete unless the corrected intended target is actually met or each remaining gap is backed by research, attempted resolution, and a precise blocker.

## Goal Oracle

The final Judge receipt must say `full_outcome_complete: true` only if all of the following are true:

1. Sprint 03 has a source-backed, varied still-image validation matrix and run receipt covering full-body, partial-body, occluded, cropped, near/mid/far, footwear-visible, headwear-visible, low-quality, and multi-person/crowded cases.
2. Sprint 03 run receipts include actual command outputs or machine-readable result summaries, confidence/descriptor status, difficulty labels, failure modes, and source/license records, while committing no third-party media.
3. Sprint 04 has complexity-graded deterministic tests and/or simulation receipts for same-track dwell, track churn, occlusion grace, dedupe, distance/box-scale, prone/low posture ambiguity, missing-off-camera escalation, and false-positive/non-event cases.
4. Sprint 05 has end-to-end config/probe/frame/narrative evidence using committed examples and any operator-authorized local camera config available; any Tapo/default credential research is source-backed and redacted, and no unauthorized access is attempted.
5. Sprint 02 has concrete FaceTime/OBS/TTS resolution research and attempted local alternatives or tests, including virtual-camera feed failure modes, OBS/Aitum/MJPEG/browser-source options, BlackHole/TTS routing, FaceTime audio/video caveats, and a recommended next test ladder.
6. `docs/cli/COMMANDS.md`, `docs/roadmaps/CURRENT_STATE_AND_NEXT.md`, `CHANGELOG.md`, and audit docs reflect the corrected status and do not overclaim production readiness.
7. Fresh verification passes, including `npm run check` and any targeted commands selected by Judge.

## Likely Misfire

Repeating the previous mistake: producing a status audit, a source list, or a docs update and then claiming completion without actual complexity-graded validation, resolution attempts, or source-backed blocker analysis.

## Enough For This Tranche

This tranche is enough only when the corrected evidence exists in repo-native files and the final audit maps every user correction to artifacts, commands, results, and remaining blockers. Planning alone is not enough.

## Starter Command

```bash
/goal Follow docs/goals/caresight-sprint-02-05-validation-recovery/goal.md.
```
