import argparse
import json
import re
import sys
import time
from collections import deque
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
DEFAULT_CONFIG_PATH = ROOT_DIR / "config" / "v0.local.json"
DEFAULT_MODEL_PATH = ROOT_DIR / "vendor" / "yolo-mlx" / "models" / "yolo26n.npz"
WINDOW_NAME = "CareSight v0 Floor Stay"


def parse_args():
    parser = argparse.ArgumentParser(description="Run CareSight v0 possible-floor-stay loop.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="CareSight v0 config JSON.")
    parser.add_argument("--model", default=str(DEFAULT_MODEL_PATH), help="YOLO26 MLX .npz model path.")
    parser.add_argument("--conf", type=float, default=0.25, help="YOLO confidence threshold.")
    parser.add_argument("--no-window", action="store_true", help="Run without an OpenCV preview window.")
    return parser.parse_args()


def class_name(names, cls_id: int) -> str:
    from caresight.vision.coco import coco_name

    fallback = coco_name(cls_id)
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


def result_to_detections(result, frame_width: int, frame_height: int):
    from caresight.vision.detections import Detection

    if result.boxes is None:
        return []

    detections = []
    for box, conf, cls in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls, strict=False):
        cls_id = int(cls)
        detections.append(
            Detection(
                class_name=class_name(result.names, cls_id),
                confidence=float(conf),
                bbox_xyxy=tuple(float(value) for value in box),
                frame_width=frame_width,
                frame_height=frame_height,
            )
        )
    return detections


def draw_frame(cv2, frame, result, config, fps_values: deque[float]):
    display = frame.copy()
    zone = config.floor_zone
    height, width = display.shape[:2]
    x1 = int(zone.x_min * width)
    y1 = int(zone.y_min * height)
    x2 = int(zone.x_max * width)
    y2 = int(zone.y_max * height)
    cv2.rectangle(display, (x1, y1), (x2, y2), (60, 220, 80), 2)
    cv2.putText(
        display,
        zone.name,
        (x1 + 8, max(y1 - 8, 24)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (60, 220, 80),
        2,
        cv2.LINE_AA,
    )

    if result.boxes is not None:
        for box, conf, cls in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls, strict=False):
            cls_id = int(cls)
            name = class_name(result.names, cls_id)
            bx1, by1, bx2, by2 = [int(value) for value in box]
            color = (255, 80, 40) if name == "person" else (40, 190, 255)
            label = f"{name} {float(conf):.2f}"
            cv2.rectangle(display, (bx1, by1), (bx2, by2), color, 2)
            cv2.putText(
                display,
                label,
                (bx1 + 4, max(by1 - 8, 18)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2,
                cv2.LINE_AA,
            )

    avg_fps = sum(fps_values) / len(fps_values) if fps_values else 0.0
    cv2.putText(
        display,
        f"v0 floor stay | dwell={config.floor_stay.dwell_seconds:.1f}s | {avg_fps:.1f} FPS | q to quit",
        (16, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return display


def main() -> None:
    import cv2
    from yolo26mlx import YOLO

    from caresight.events.floor_stay import FloorStayDetector
    from caresight.events.snapshots import attach_local_snapshot
    from caresight.runtime.config import CareSightConfig
    from caresight.storage.sqlite_store import SQLiteStore

    args = parse_args()
    config = CareSightConfig.load(args.config)
    model_path = Path(args.model)
    if not model_path.exists():
        raise SystemExit(f"Missing model: {model_path}")

    store = SQLiteStore(config.storage.database_path)
    store.initialize()
    store.upsert_config(config)

    model = YOLO(str(model_path))
    cap = cv2.VideoCapture(int(config.camera.source_uri), cv2.CAP_AVFOUNDATION)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.camera.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.camera.height)
    cap.set(cv2.CAP_PROP_FPS, config.camera.fps)
    if not cap.isOpened():
        raise SystemExit(f"Could not open camera {config.camera.source_uri}")

    detector = FloorStayDetector(config)
    fps_values: deque[float] = deque(maxlen=30)
    print(
        "v0_started "
        f"camera={config.camera.camera_id} zone={config.floor_zone.zone_id} "
        f"dwell_seconds={config.floor_stay.dwell_seconds} db={config.storage.database_path}"
    )

    if not args.no_window:
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(WINDOW_NAME, config.camera.width, config.camera.height)

    while True:
        started_at = time.perf_counter()
        ok, frame = cap.read()
        if not ok:
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = model.predict(rgb_frame, conf=args.conf)[0]
        height, width = frame.shape[:2]
        event = detector.update(result_to_detections(result, width, height))
        if event is not None:
            snapshot_dir = Path(config.storage.database_path).parent / "snapshots"
            event = attach_local_snapshot(
                event=event,
                snapshot_dir=snapshot_dir,
                write_snapshot=lambda path: cv2.imwrite(str(path), frame),
            )
            store.insert_event(event)
            print("event_persisted " + json.dumps(event, sort_keys=True))

        elapsed = max(time.perf_counter() - started_at, 0.0001)
        fps_values.append(1.0 / elapsed)

        if not args.no_window:
            cv2.imshow(WINDOW_NAME, draw_frame(cv2, frame, result, config, fps_values))
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
