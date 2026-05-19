# YOLO26 MLX Smoke Checkpoint

Date: 2026-05-18

## Scope

This audit records the first functional CareSight Hub YOLO26 MLX smoke checkpoint.

The goal was not v0 event persistence yet. The goal was to prove that the repo can run local on-device YOLO26 MLX inference from the CareSight runtime boundary and use that as a reliable starting point for v0 implementation.

## Verified Setup

- Upstream repo cloned at `apps/caresight-hub/vendor/yolo-mlx`.
- Upstream checkout: `39dd0b38f5183490337cdc84bd3e90ec6af74d15`.
- Local YOLO26 MLX virtual environment created at `apps/caresight-hub/vendor/yolo-mlx/.venv`.
- `yolo26n.pt` converted to MLX-native `yolo26n.npz`.
- Converted model path: `apps/caresight-hub/vendor/yolo-mlx/models/yolo26n.npz`.

## Commands

```bash
apps/caresight-hub/scripts/setup_yolo26_mlx.sh
apps/caresight-hub/scripts/prepare_yolo26n_model.sh
source apps/caresight-hub/vendor/yolo-mlx/.venv/bin/activate
python apps/caresight-hub/scripts/yolo26_image_smoke.py
python apps/caresight-hub/scripts/yolo26_webcam_smoke.py
```

## Observed Results

- Image smoke test loaded `yolo26n.npz`.
- Image smoke test detected 5 boxes on the sample bus image.
- Annotated image saved to `apps/caresight-hub/results/bus_result.jpg`.
- Webcam smoke test opened the Mac camera successfully.
- Live detections were rapid and usable.
- Camera settings/FPS overlay displayed correctly.
- OpenCV renderer preserved much better native camera color than the upstream plot renderer.
- Labels now resolve through a COCO fallback map instead of showing placeholder `class#` labels.

## Known Notes

- OpenCV requested `1280x720@30`; the Mac camera returned `1280x720@15.0` in the observed run.
- The live smoke is a functional inference test, not the v0 event loop.
- Generated model, venv, image, and result artifacts are intentionally excluded from scaffold file-tree validation.

## Validation

```bash
npm run check
```

Result: passed.

## Next Resolution Layer

The next implementation layer is v0 eventization:

```text
YOLO26 MLX detections
  -> person/couch-aware observations
  -> configured zones
  -> dwell-time state
  -> possible_floor_stay event JSON
  -> SQLite event row
  -> inspectable terminal output
```

Success means the system can create one contract-shaped `possible_floor_stay` event from live local detections and persist it locally.
