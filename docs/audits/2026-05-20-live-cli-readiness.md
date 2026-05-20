# Live CLI Readiness Audit

Date: 2026-05-20

## Scope

This audit records live CLI readiness hardening for the v0 floor-stay loop.

## Implemented

- `--help` parses before OpenCV and YOLO26 MLX imports.
- Vendored YOLO path is added to `sys.path` for live runs.
- Tests verify help output includes bounded proof flags.

## Boundary

This does not prove live camera behavior. It makes the operator proof command safer to inspect and run.
