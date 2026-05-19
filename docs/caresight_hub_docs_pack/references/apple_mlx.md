# Apple MLX Reference

## Role in CareSight

MLX is the Apple Silicon machine-learning framework used by YOLO26 MLX and optionally Gemma local inference.

## Why it matters

- Efficient local inference on Apple Silicon.
- Unified memory architecture support.
- Makes the product's local-first story credible.

## CareSight implications

- Hardware target should be Apple Silicon, not Intel Mac.
- Benchmark on actual machine.
- Include model/FPS table in README.
- Use lower model variants for broader device accessibility.

## Sources

- [Apple MLX Project](https://opensource.apple.com/projects/mlx/)
- [MLX Docs](https://ml-explore.github.io/mlx/build/html/index.html)
