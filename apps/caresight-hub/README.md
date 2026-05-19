# CareSight Hub Runtime

This app boundary holds the Python/MLX runtime. The upstream `thewebAI/yolo-mlx` repository is cloned under `vendor/yolo-mlx` so tonight's testing can use the real YOLO26 MLX package while CareSight-specific runtime code remains separate.

## Scope

- YOLO26 MLX runner.
- Camera adapters for webcam, USB, Continuity Camera, and later RTSP.
- Event engine for bounded care observations.
- SQLite storage and migrations.
- Daily journal generation.
- Alert adapters and optional OBS / FaceTime handoff.
- Local dashboard.

## Current Gate

The current Python check is intentionally lightweight while the runtime skeleton is empty:

```bash
npm run py:check
```

When runtime dependencies are added, this should expand to Ruff plus pytest for `apps/caresight-hub/`.

## YOLO26 MLX Local Setup

The upstream checkout is:

```bash
apps/caresight-hub/vendor/yolo-mlx
```

Bootstrap the YOLO26 MLX virtual environment:

```bash
apps/caresight-hub/scripts/setup_yolo26_mlx.sh
```

Download and convert `yolo26n`:

```bash
apps/caresight-hub/scripts/prepare_yolo26n_model.sh
```

Run an image smoke test:

```bash
source apps/caresight-hub/vendor/yolo-mlx/.venv/bin/activate
python apps/caresight-hub/scripts/yolo26_image_smoke.py
```

Run the webcam smoke test:

```bash
source apps/caresight-hub/vendor/yolo-mlx/.venv/bin/activate
python apps/caresight-hub/scripts/yolo26_webcam_smoke.py
```

By default the webcam smoke requests the macOS AVFoundation camera path at `1280x720@30`, sends RGB input to YOLO, and draws boxes directly on the original OpenCV camera frame so the preview keeps the camera's native colors. It also prints the actual settings OpenCV receives. You can override them:

```bash
python apps/caresight-hub/scripts/yolo26_webcam_smoke.py --camera 0 --width 1920 --height 1080 --fps 30
```

If you need to compare against the raw OpenCV color path:

```bash
python apps/caresight-hub/scripts/yolo26_webcam_smoke.py --raw-bgr
```

If you need to compare against the upstream `Results.plot()` renderer:

```bash
python apps/caresight-hub/scripts/yolo26_webcam_smoke.py --renderer plot
```

Press `q` to quit the webcam window. macOS may require camera permission for Terminal or the IDE running Python.

## v0 Floor-Stay Loop

The v0 implementation uses the same YOLO26 MLX model but adds config, zone dwell state, contract-shaped event JSON, and SQLite persistence.

Edit the local test config here:

```bash
apps/caresight-hub/config/v0.local.json
```

Run v0:

```bash
source apps/caresight-hub/vendor/yolo-mlx/.venv/bin/activate
python apps/caresight-hub/scripts/v0_floor_stay_live.py
```

The default test config defines the bottom third of the frame as `floor_zone` and uses an 8-second dwell threshold. Lie or stay low in that zone until the threshold elapses. The terminal prints `event_persisted` with the saved `possible_floor_stay` JSON, and the event is stored in:

```bash
apps/caresight-hub/data/caresight-v0.sqlite3
```

## Upstream Boundary

`vendor/yolo-mlx` is AGPL-3.0-only upstream code. Keep CareSight glue scripts in `apps/caresight-hub/scripts/` and runtime modules in `apps/caresight-hub/caresight/`; do not edit vendored upstream files unless the intent is to carry a patch.
