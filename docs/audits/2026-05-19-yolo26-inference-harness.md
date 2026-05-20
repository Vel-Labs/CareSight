# YOLO26 Inference Harness Audit

Date: 2026-05-19

## Scope

Task T005 added the CareSight-owned YOLO26 MLX inference harness under
`apps/caresight-hub/caresight/runtime/inference/`.

## Implemented Boundary

- Raw `Detection` records preserve model ID, class ID, label, confidence, pixel box, frame size, camera ID, timestamp, and raw index.
- Normalized `Observation` records attach camera metadata, room metadata, normalized box coordinates, and `*_likely_observed` wording.
- `apps/caresight-hub/config/v0.local.json` now carries top-level `room` and `inference` metadata while preserving the existing v0 camera/floor/storage keys.
- The YOLO26 MLX adapter raises fail-closed errors for missing model files, import failures, load failures, and prediction failures.
- Empty YOLO results return empty detections and observations; the harness does not fake detections.

## Validation

Deterministic coverage lives in `apps/caresight-hub/tests/test_inference_harness.py`.
Live image and webcam smoke remain manual/operator checks because they depend on local MLX model availability and camera permissions.
