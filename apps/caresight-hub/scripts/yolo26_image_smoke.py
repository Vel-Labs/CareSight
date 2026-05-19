from pathlib import Path
from urllib.request import urlretrieve

from yolo26mlx import YOLO


ROOT_DIR = Path(__file__).resolve().parents[1]
YOLO_DIR = ROOT_DIR / "vendor" / "yolo-mlx"
MODEL_PATH = YOLO_DIR / "models" / "yolo26n.npz"
IMAGE_DIR = ROOT_DIR / "images"
IMAGE_PATH = IMAGE_DIR / "bus.jpg"


def main() -> None:
    if not MODEL_PATH.exists():
        raise SystemExit(
            f"Missing model: {MODEL_PATH}\n"
            "Run apps/caresight-hub/scripts/prepare_yolo26n_model.sh first."
        )

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    if not IMAGE_PATH.exists():
        urlretrieve("https://ultralytics.com/images/bus.jpg", IMAGE_PATH)

    model = YOLO(str(MODEL_PATH))
    results = model.predict(str(IMAGE_PATH), conf=0.25)
    print(results[0])
    output_path = ROOT_DIR / "results" / "bus_result.jpg"
    saved_path = results[0].save(str(output_path))
    print(f"saved={saved_path}")


if __name__ == "__main__":
    main()
