# Repository Boundaries

## What This Repo Owns

- CareSight governance and agent operating rules.
- Canonical care contracts in `contracts/`.
- TypeScript contract validation in `packages/core/`.
- Shared local quality gates in `tests/`.
- Python runtime boundary in `apps/caresight-hub/`.
- Hackathon, architecture, roadmap, reference, decision, and audit docs.

## TypeScript Governance Boundary

`packages/core/` remains the reusable validation/enforcement layer inherited from the scaffold. It should validate schemas and examples, expose contract helpers, and support repo quality gates.

It should not contain YOLO, OpenCV, camera, SQLite runtime, dashboard, or alert implementation.

## Python Runtime Boundary

`apps/caresight-hub/` owns:

- camera adapters
- YOLO26 MLX runner
- detections, tracking, zones, and temporal event rules
- SQLite storage
- journal generation
- alert adapters
- OBS bridge
- dashboard entrypoint

The runtime consumes contract truth. It does not redefine the safety model.

## Integration Boundaries

Allowed in v1/v2:

- local camera source
- YOLO26 MLX
- SQLite
- local dashboard
- terminal/local/macOS/Shortcut alert
- optional OBS and FaceTime handoff

Out of scope unless explicitly moved:

- Ring/Nest adapters
- cloud raw-video upload
- emergency service integrations
- EHR integrations
- clinical/facility compliance workflows

## Fold-In Rule

Docs from `docs/caresight_hub_docs_pack/` should be routed into the scaffold lanes before they become operational instructions. Root files stay short and act as indexes.
