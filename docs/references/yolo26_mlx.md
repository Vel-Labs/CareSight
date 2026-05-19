# YOLO26 MLX Reference

## Role in CareSight

YOLO26 MLX is the core perception engine. It should provide object/person/pet detections, optional tracking, and possibly segmentation for care-relevant event logic.

## Key implementation notes

- Run locally on Apple Silicon.
- Start with `yolo26n` for real-time webcam demos.
- Try `yolo26s` if accuracy needs improvement and FPS remains acceptable.
- Use tracking for dwell time and persistent event logic.
- Use segmentation only if masks/path occupancy are important.

## CareSight use cases

- possible floor-stay event
- medication station routine evidence
- pet food area activity
- package/front-door activity
- person/room occupancy
- camera zone entry/exit

## Local CareSight Checkout

The upstream repo is cloned at:

```text
apps/caresight-hub/vendor/yolo-mlx
```

Current pinned checkout at adoption time:

```text
39dd0b38f5183490337cdc84bd3e90ec6af74d15
0.3.1: dataset auto-download lands at ./datasets/
```

CareSight wrapper scripts live outside the vendored repo:

```text
apps/caresight-hub/scripts/setup_yolo26_mlx.sh
apps/caresight-hub/scripts/prepare_yolo26n_model.sh
apps/caresight-hub/scripts/yolo26_image_smoke.py
apps/caresight-hub/scripts/yolo26_webcam_smoke.py
```

## Practical commands

```bash
apps/caresight-hub/scripts/setup_yolo26_mlx.sh
apps/caresight-hub/scripts/prepare_yolo26n_model.sh
source apps/caresight-hub/vendor/yolo-mlx/.venv/bin/activate
python apps/caresight-hub/scripts/yolo26_image_smoke.py
python apps/caresight-hub/scripts/yolo26_webcam_smoke.py
```

Upstream package commands from the current checkout:

```bash
yolo26 converters convert models/yolo26n.pt -o models/yolo26n.npz --verify
```

## Notes

Keep YOLO central to the challenge submission. Gemma/OpenClaw should not replace YOLO as the core AI capability.

## Sources

- [YOLO26 MLX Build Challenge](https://webai.discourse.group/t/the-yolo26-mlx-build-challenge-may-2026/16)
- [YOLO26 MLX Getting Started Guide](https://webai.discourse.group/t/getting-started-guide-yolo26-mlx-build-challenge/20)
- [YOLO26 MLX GitHub Repository](https://github.com/thewebAI/yolo-mlx)
- [webAI YOLO26 MLX Announcement Blog](https://www.webai.com/blog/running-yolo26-natively-on-apple-silicon-with-mlx)
