# Architecture

## System Goal

CareSight Hub turns a local Apple Silicon machine and a camera feed into a bounded care event engine. It observes configured signals, creates local structured records, and routes alerts to authorized humans without claiming medical authority.

## Core Thesis

CareSight should be judged as a chain of care, not a camera viewer:

```text
camera frames
  -> YOLO26 MLX observations
  -> deterministic event policy
  -> local SQLite memory
  -> journal and caregiver alert
  -> human acknowledgement
```

## Architecture Planes

### 1. Contract Plane

Location: `contracts/`

Owns schemas, examples, lifecycle, and fail-closed behavior for care events, camera config, routines, alert policy, and caregiver roles.

### 2. Governance and Enforcement Plane

Location: `packages/core/`

Owns TypeScript validation helpers and quality-gate logic. This plane validates contract truth but does not implement the runtime app.

### 3. Runtime Plane

Location: `apps/caresight-hub/`

Owns the Python/MLX runtime: camera handling, YOLO26 MLX execution, tracking, event engine, SQLite writes, dashboard, alerts, OBS bridge, and FaceTime handoff.

### 4. Presentation Plane

Owns local dashboard views, OBS scene selection, FaceTime handoff controls, and daily journal display. Presentation code must not become canonical truth.

### 5. Evidence and Audit Plane

Owns tests, receipts, event examples, audit notes, and reproducible validation. Claims in docs should point back to this plane or stay explicitly aspirational.

## Runtime Boundary

The Python runtime is downstream of accepted contracts:

```text
contracts/
  -> packages/core/ validation
  -> apps/caresight-hub/ runtime consumption
  -> tests/ and receipts
```

## Fail-Closed Laws

- Missing or invalid contracts block promotion.
- Unsupported actions are blocked by policy.
- Medication administration is never confirmed from vision alone.
- Emergency dispatch is not autonomous.
- Raw video is local by default and cloud upload is opt-in future work only.
