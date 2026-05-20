# Bounded Live Proof Controls Audit

Date: 2026-05-20

## Scope

This audit records bounded live-run controls for the v0 floor-stay loop.

## Implemented

- Added `--max-seconds`.
- Added `--stop-after-event`.
- Added deterministic loop-control tests.
- Documented the bounded audit command.

## Operator Command

```bash
python3 apps/caresight-hub/scripts/v0_floor_stay_live.py --no-window --stop-after-event --max-seconds 120
```

## Boundary

The command still requires a real camera, real model output, and operator/human review. It does not synthesize detections, confirm events, dismiss events, dispatch, or diagnose.
