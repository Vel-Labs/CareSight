import argparse
import re
import sys
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
YOLO_DIR = ROOT_DIR / "vendor" / "yolo-mlx"
MODEL_PATH = YOLO_DIR / "models" / "yolo26n.npz"
CONFIG_PATH = ROOT_DIR / "config" / "v0.example.json"
WINDOW_NAME = "CareSight YOLO26 MLX"
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(YOLO_DIR))

from caresight.runtime.inference import CareSightInferenceHarness  # noqa: E402
from caresight.runtime.inference.adapter import ModelLoadError  # noqa: E402

COCO_NAMES = [
    "person",
    "bicycle",
    "car",
    "motorcycle",
    "airplane",
    "bus",
    "train",
    "truck",
    "boat",
    "traffic light",
    "fire hydrant",
    "stop sign",
    "parking meter",
    "bench",
    "bird",
    "cat",
    "dog",
    "horse",
    "sheep",
    "cow",
    "elephant",
    "bear",
    "zebra",
    "giraffe",
    "backpack",
    "umbrella",
    "handbag",
    "tie",
    "suitcase",
    "frisbee",
    "skis",
    "snowboard",
    "sports ball",
    "kite",
    "baseball bat",
    "baseball glove",
    "skateboard",
    "surfboard",
    "tennis racket",
    "bottle",
    "wine glass",
    "cup",
    "fork",
    "knife",
    "spoon",
    "bowl",
    "banana",
    "apple",
    "sandwich",
    "orange",
    "broccoli",
    "carrot",
    "hot dog",
    "pizza",
    "donut",
    "cake",
    "chair",
    "couch",
    "potted plant",
    "bed",
    "dining table",
    "toilet",
    "tv",
    "laptop",
    "mouse",
    "remote",
    "keyboard",
    "cell phone",
    "microwave",
    "oven",
    "toaster",
    "sink",
    "refrigerator",
    "book",
    "clock",
    "vase",
    "scissors",
    "teddy bear",
    "hair drier",
    "toothbrush",
]


@dataclass(frozen=True)
class CameraSettings:
    camera: int
    width: int
    height: int
    fps: int
    conf: float
    renderer: str
    raw_bgr: bool


def parse_args() -> CameraSettings:
    parser = argparse.ArgumentParser(description="Run a CareSight YOLO26 MLX webcam smoke test.")
    parser.add_argument("--camera", type=int, default=0, help="OpenCV camera index.")
    parser.add_argument("--width", type=int, default=1280, help="Requested capture width.")
    parser.add_argument("--height", type=int, default=720, help="Requested capture height.")
    parser.add_argument("--fps", type=int, default=30, help="Requested capture FPS.")
    parser.add_argument("--conf", type=float, default=0.25, help="YOLO confidence threshold.")
    parser.add_argument(
        "--renderer",
        choices=["opencv", "plot"],
        default="opencv",
        help="Draw boxes with OpenCV on the original camera frame, or use upstream Results.plot().",
    )
    parser.add_argument(
        "--raw-bgr",
        action="store_true",
        help="Debug mode: skip RGB/BGR correction and show the raw OpenCV color path.",
    )
    args = parser.parse_args()
    return CameraSettings(
        camera=args.camera,
        width=args.width,
        height=args.height,
        fps=args.fps,
        conf=args.conf,
        renderer=args.renderer,
        raw_bgr=args.raw_bgr,
    )


def open_camera(settings: CameraSettings, cv2_module) -> Any:
    cv2 = cv2_module
    cap = cv2.VideoCapture(settings.camera, cv2.CAP_AVFOUNDATION)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.height)
    cap.set(cv2.CAP_PROP_FPS, settings.fps)
    return cap


def print_actual_settings(cap: Any, settings: CameraSettings, cv2_module) -> None:
    cv2 = cv2_module
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = cap.get(cv2.CAP_PROP_FPS)
    print(
        "camera="
        f"{settings.camera} requested={settings.width}x{settings.height}@{settings.fps} "
        f"actual={actual_width}x{actual_height}@{actual_fps:.1f} conf={settings.conf} "
        f"renderer={settings.renderer} color={'raw-bgr' if settings.raw_bgr else 'rgb-input'}"
    )


def draw_status(frame, fps_values: deque[float], settings: CameraSettings, cv2_module):
    cv2 = cv2_module
    if not fps_values:
        return frame

    avg_fps = sum(fps_values) / len(fps_values)
    cv2.putText(
        frame,
        f"CareSight YOLO26 MLX | {avg_fps:.1f} FPS | q to quit",
        (16, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        f"camera {settings.camera} | requested {settings.width}x{settings.height}@{settings.fps}",
        (16, 62),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    return frame


def class_name(names, cls_id: int) -> str:
    fallback = COCO_NAMES[cls_id] if 0 <= cls_id < len(COCO_NAMES) else f"class{cls_id}"
    if isinstance(names, dict):
        name = names.get(cls_id, names.get(str(cls_id)))
        if name and not is_placeholder_name(str(name)):
            return str(name)
    if isinstance(names, list | tuple) and 0 <= cls_id < len(names):
        name = str(names[cls_id])
        if not is_placeholder_name(name):
            return name
    return fallback


def is_placeholder_name(name: str) -> bool:
    return re.fullmatch(r"(?i)class[_ -]?\d+", name.strip()) is not None


def draw_boxes_on_camera_frame(frame, result, cv2_module):
    cv2 = cv2_module
    display = frame.copy()
    if result.boxes is None or len(result.boxes) == 0:
        return display

    for box, conf, cls in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls, strict=False):
        x1, y1, x2, y2 = [int(v) for v in box]
        cls_id = int(cls)
        label = f"{class_name(result.names, cls_id)} {float(conf):.2f}"
        color = (255, 80, 40) if cls_id == 0 else (40, 190, 255)

        cv2.rectangle(display, (x1, y1), (x2, y2), color, 2)
        text_size, baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        text_w, text_h = text_size
        label_y = max(y1, text_h + baseline + 4)
        cv2.rectangle(
            display,
            (x1, label_y - text_h - baseline - 4),
            (x1 + text_w + 6, label_y + baseline),
            color,
            -1,
        )
        cv2.putText(
            display,
            label,
            (x1 + 3, label_y - 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

    return display


def main() -> None:
    import cv2
    settings = parse_args()
    if not MODEL_PATH.exists():
        raise SystemExit(
            f"Missing model: {MODEL_PATH}\n"
            "Run apps/caresight-hub/scripts/prepare_yolo26n_model.sh first."
        )

    harness = CareSightInferenceHarness.from_config_path(CONFIG_PATH)
    try:
        harness.adapter.load()
    except ModelLoadError as error:
        raise SystemExit(f"fail_closed={error}") from error

    cap = open_camera(settings, cv2)
    if not cap.isOpened():
        raise SystemExit(
            f"Could not open camera {settings.camera}. "
            "Check macOS camera permission for Terminal or your IDE."
        )

    print_actual_settings(cap, settings, cv2)
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, settings.width, settings.height)
    fps_values: deque[float] = deque(maxlen=30)

    while True:
        started_at = time.perf_counter()
        ok, frame = cap.read()
        if not ok:
            break

        model_input = frame if settings.raw_bgr else cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = harness.adapter._runner.predict(model_input, conf=settings.conf)
        if settings.renderer == "plot":
            annotated = results[0].plot()
            display_frame = (
                annotated if settings.raw_bgr else cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR)
            )
        else:
            display_frame = draw_boxes_on_camera_frame(frame, results[0], cv2)
        elapsed = max(time.perf_counter() - started_at, 0.0001)
        fps_values.append(1.0 / elapsed)

        cv2.imshow(WINDOW_NAME, draw_status(display_frame, fps_values, settings, cv2))
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
