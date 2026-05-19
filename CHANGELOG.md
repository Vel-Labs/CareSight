# Changelog

## 2026-05-18

- Adopted `Vel-Labs/project-scaffold` as the CareSight Hub repo backbone.
- Personalized root docs, project brief, architecture, boundaries, roadmap, decisions, and agent rules.
- Routed the CareSight docs pack into hackathon, roadmap, architecture, and reference lanes.
- Added CareSight contract schemas and examples for events, cameras, routines, alert policies, and caregiver roles.
- Added a bounded Python runtime skeleton under `apps/caresight-hub/`.
- Added `py:check` to the local quality gate.
- Cloned `thewebAI/yolo-mlx` under the CareSight runtime boundary and added local setup, model-prep, image smoke-test, and webcam smoke-test scripts.
- Recorded the YOLO26 MLX smoke checkpoint audit and routed v0 next work toward eventization and SQLite persistence.
- Implemented v0 floor-stay eventization with file-backed config, zone/dwell logic, SQLite tables, event observation persistence, live runner, and tests.
- Added local still snapshot capture for v0 floor-stay events, recorded in event evidence as local-only snapshot metadata.
- Added v0 review and acknowledgement CLI with event inbox, human-readable summaries, reviewer-gated confirm/dismiss, journal entries, report-only agent handoffs, and lifecycle tests.
- Added `docs/cli/COMMANDS.md` as the durable local CLI registry and updated agent rules for review-flow boundaries.
