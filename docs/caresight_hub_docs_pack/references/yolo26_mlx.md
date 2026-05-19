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

## Practical commands to adapt

```bash
python -m mlx_yolo convert --model yolo26n.pt
python -m mlx_yolo predict --model yolo26n.mlpackage --source 0
```

Actual commands may differ by repo version; follow upstream docs.

## Notes

Keep YOLO central to the challenge submission. Gemma/OpenClaw should not replace YOLO as the core AI capability.

## Sources

- [YOLO26 MLX Build Challenge](https://webai.discourse.group/t/the-yolo26-mlx-build-challenge-may-2026/16)
- [YOLO26 MLX Getting Started Guide](https://webai.discourse.group/t/getting-started-guide-yolo26-mlx-build-challenge/20)
- [YOLO26 MLX GitHub Repository](https://github.com/thewebAI/yolo-mlx)
- [webAI YOLO26 MLX Announcement Blog](https://www.webai.com/blog/running-yolo26-natively-on-apple-silicon-with-mlx)
