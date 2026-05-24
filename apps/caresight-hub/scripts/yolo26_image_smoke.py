import json
import sys
from pathlib import Path
from urllib.request import urlretrieve


ROOT_DIR = Path(__file__).resolve().parents[1]
YOLO_DIR = ROOT_DIR / "vendor" / "yolo-mlx"
MODEL_PATH = YOLO_DIR / "models" / "yolo26n.npz"
IMAGE_DIR = ROOT_DIR / "images"
IMAGE_PATH = IMAGE_DIR / "bus.jpg"
CONFIG_PATH = ROOT_DIR / "config" / "v0.example.json"
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(YOLO_DIR))

from caresight.runtime.inference import CareSightInferenceHarness  # noqa: E402
from caresight.runtime.inference.adapter import ModelLoadError  # noqa: E402


def main() -> None:
    if not MODEL_PATH.exists():
        raise SystemExit(
            f"Missing model: {MODEL_PATH}\n"
            "Run apps/caresight-hub/scripts/prepare_yolo26n_model.sh first."
        )

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    if not IMAGE_PATH.exists():
        urlretrieve("https://ultralytics.com/images/bus.jpg", IMAGE_PATH)

    harness = CareSightInferenceHarness.from_config_path(CONFIG_PATH)
    try:
        result = harness.run(str(IMAGE_PATH))
    except ModelLoadError as error:
        raise SystemExit(f"fail_closed={error}") from error

    print(json.dumps(result.to_dict(), indent=2))

    model = harness.adapter._runner
    if model is None:
        raise SystemExit("fail_closed=YOLO26 MLX runner did not load")
    results = model.predict(str(IMAGE_PATH), conf=harness.config.model.confidence_threshold)
    output_path = ROOT_DIR / "results" / "bus_result.jpg"
    saved_path = results[0].save(str(output_path))
    print(f"saved={saved_path}")


if __name__ == "__main__":
    main()
