import argparse
from html import escape as html_escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
import os
import re
import secrets
import sys
import threading
import time
import traceback
from collections import deque
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

ROOT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT_DIR.parents[1]
YOLO_DIR = ROOT_DIR / "vendor" / "yolo-mlx"
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(YOLO_DIR))
DEFAULT_LOCAL_CONFIG_PATH = ROOT_DIR / "config" / "v0.local.json"
DEFAULT_EXAMPLE_CONFIG_PATH = ROOT_DIR / "config" / "v0.example.json"
DEFAULT_CONFIG_PATH = DEFAULT_LOCAL_CONFIG_PATH
DEFAULT_MODEL_PATH = ROOT_DIR / "vendor" / "yolo-mlx" / "models" / "yolo26n.npz"
WINDOW_NAME = "CareSight v0 Floor Stay"
DEFAULT_OBS_PREVIEW_PATH = REPO_ROOT / "apps" / "obs-hub" / "config" / "live_preview.jpg"
DEFAULT_ALLOWLIST_PATH = ROOT_DIR / "config" / "hermes" / "allowlisted-contacts.example.json"
DEFAULT_BROWSER_FEED_HOST = "127.0.0.1"
DEFAULT_BROWSER_FEED_PORT = 8766
DISPLAY_LABELS = {"person", "cat", "dog", "bird"}


def parse_args():
    parser = argparse.ArgumentParser(description="Run CareSight v0 possible-floor-stay loop.")
    parser.add_argument(
        "--config",
        default=None,
        help="CareSight v0 config JSON. Defaults to ignored v0.local.json when present, else tracked v0.example.json.",
    )
    parser.add_argument("--model", default=str(DEFAULT_MODEL_PATH), help="YOLO26 MLX .npz model path.")
    parser.add_argument("--conf", type=float, default=0.25, help="YOLO confidence threshold.")
    parser.add_argument("--camera-id", help="Configured camera_id to select from config.cameras.")
    parser.add_argument(
        "--source-type",
        choices=["webcam", "usb", "continuity_camera", "rtsp"],
        help="Configured source_type to select when it resolves to one camera.",
    )
    parser.add_argument("--no-window", action="store_true", help="Run without an OpenCV preview window.")
    parser.add_argument(
        "--show-window",
        action="store_true",
        help="Force the OpenCV preview window even when --obs-browser-feed is enabled.",
    )
    parser.add_argument("--max-seconds", type=float, help="Stop after this many seconds.")
    parser.add_argument(
        "--stop-after-event",
        action="store_true",
        help="Stop after the first event_persisted line.",
    )
    parser.add_argument(
        "--auto-agent-dry-run",
        action="store_true",
        help=(
            "After each persisted event, update OBS overlay state, create a local Gemma draft, "
            "stage an allowlisted iMessage request, and run Hermes no-send preflight. "
            "No live message or call is sent."
        ),
    )
    parser.add_argument(
        "--obs-live-preview",
        action="store_true",
        help="Write annotated preview frames to apps/obs-hub/config/live_preview.jpg for OBS/browser overlays.",
    )
    parser.add_argument(
        "--obs-browser-feed",
        action="store_true",
        help="Serve an annotated local MJPEG browser feed for OBS at http://127.0.0.1:8766/live.html.",
    )
    parser.add_argument("--obs-browser-feed-host", default=DEFAULT_BROWSER_FEED_HOST)
    parser.add_argument("--obs-browser-feed-port", type=int, default=DEFAULT_BROWSER_FEED_PORT)
    parser.add_argument(
        "--allow-lan-preview",
        action="store_true",
        help="Allow a non-loopback MJPEG preview bind. Requires --preview-token and --ack-lan-preview-risk.",
    )
    parser.add_argument("--preview-token", help="Bearer/query token required for LAN MJPEG preview exposure.")
    parser.add_argument(
        "--ack-lan-preview-risk",
        action="store_true",
        help="Acknowledge that LAN preview can expose event-scoped home video to local-network viewers.",
    )
    parser.add_argument(
        "--obs-live-preview-path",
        default=str(DEFAULT_OBS_PREVIEW_PATH),
        help="Path for annotated OBS live preview JPEG frames.",
    )
    parser.add_argument(
        "--obs-live-preview-fps",
        type=float,
        default=5.0,
        help="Maximum annotated preview write rate.",
    )
    parser.add_argument(
        "--debug-floor-stay",
        action="store_true",
        help="Print one compact floor-stay detector diagnostic line per second.",
    )
    parser.add_argument(
        "--appearance-sampling",
        action="store_true",
        help="Periodically store capped, quality-gated local appearance samples for same-day profile support.",
    )
    parser.add_argument(
        "--appearance-overlay",
        action="store_true",
        help="Draw visual-review clothing descriptor subregions on person detections in preview/OBS frames.",
    )
    parser.add_argument(
        "--missing-off-camera-events",
        action="store_true",
        help="Emit bounded missing_off_camera_extended events when a tracked person is absent for tracking.missing_seconds.",
    )
    parser.add_argument(
        "--camera-read-failure-timeout-seconds",
        type=float,
        default=12.0,
        help="Reconnect RTSP sources for this long after frame-read failures before ending the run.",
    )
    parser.add_argument(
        "--camera-read-retry-delay-seconds",
        type=float,
        default=0.5,
        help="Delay between RTSP frame-read retry attempts.",
    )
    parser.add_argument(
        "--appearance-sample-interval-seconds",
        type=float,
        default=15.0,
        help="Minimum seconds between accepted appearance samples.",
    )
    parser.add_argument(
        "--appearance-max-samples-per-profile",
        type=int,
        default=5,
        help="Retain this many best appearance sample snapshots per profile per day.",
    )
    parser.add_argument(
        "--appearance-min-quality-score",
        type=float,
        default=0.62,
        help="Minimum appearance quality score required before saving a sample snapshot.",
    )
    parser.add_argument(
        "--auto-agent-live-run",
        action="store_true",
        help=(
            "After each persisted event, run the post-event agent chain and send the approved "
            "iMessage to an allowlisted contact. Requires --live-approved and a private contact target."
        ),
    )
    parser.add_argument(
        "--live-approved",
        action="store_true",
        help="Explicit operator approval for live iMessage execution in --auto-agent-live-run.",
    )
    parser.add_argument(
        "--live-imessage-target",
        help="Private iMessage handle. Prefer CARESIGHT_LIVE_IMESSAGE_TARGET for local tests.",
    )
    parser.add_argument(
        "--live-message",
        default=None,
        help="Approved live iMessage body. Defaults to bounded event-specific caregiver wording.",
    )
    parser.add_argument(
        "--auto-facetime-on-reply",
        action="store_true",
        help=(
            "After live iMessage send, watch local Messages for a yes-like reply, then open FaceTime. "
            "Requires local Messages DB access."
        ),
    )
    parser.add_argument("--reply-timeout-seconds", type=float, default=180.0)
    parser.add_argument("--reply-poll-interval-seconds", type=float, default=2.0)
    parser.add_argument(
        "--no-response-escalation-seconds",
        type=float,
        default=90.0,
        help="After this many seconds with no reply, send a bounded follow-up with the local event snapshot. Use 0 to disable.",
    )
    parser.add_argument(
        "--no-response-escalation-message",
        default=(
            "This is CareSight Hub escalation. We have not heard back, but there is an event that requires "
            "caregiver verification. Please see the image attached. To connect, please respond with: "
            "yes connect or yes FaceTime."
        ),
    )
    parser.add_argument(
        "--play-tts-after-facetime",
        action="store_true",
        help="After reply-gated FaceTime opens, play the approved local Dakota TTS utterance.",
    )
    parser.add_argument(
        "--tts-audio-route",
        choices=["system", "blackhole"],
        default="system",
        help="Use system audio as-is, or temporarily route TTS playback through BlackHole 2ch.",
    )
    parser.add_argument(
        "--tts-text",
        default=(
            "This is an automated CareSight message. A possible floor stay was observed in the Living Room. "
            "Please review the live feed. CareSight will keep this handoff open briefly for review."
        ),
    )
    parser.add_argument("--tts-voice", default="dakota")
    parser.add_argument("--tts-volume", type=float, default=6.0, help="Playback gain passed to local TTS afplay.")
    parser.add_argument("--tts-repeat-count", type=int, default=2, help="Number of times to play the TTS handoff message.")
    parser.add_argument(
        "--tts-repeat-delay-seconds",
        type=float,
        default=1.5,
        help="Pause between repeated TTS handoff playback attempts.",
    )
    parser.add_argument(
        "--tts-after-facetime-delay-seconds",
        type=float,
        default=16.0,
        help="Wait this long after FaceTime is requested before playing TTS.",
    )
    parser.add_argument(
        "--post-facetime-hold-seconds",
        type=float,
        default=30.0,
        help="Keep the live command running this long after FaceTime/TTS so the OBS feed remains available.",
    )
    parser.add_argument("--gemma-base-url", default="http://127.0.0.1:8080/v1")
    parser.add_argument(
        "--gemma-model",
        default=str(REPO_ROOT / "apps/caresight-hub/models/reasoning/gemma/gemma-4-e2b-it-4bit"),
    )
    parser.add_argument("--allowed-contact-id", default="contact_emergency_primary")
    parser.add_argument(
        "--allowlist-config",
        default=os.environ.get("CARESIGHT_CONTACT_ALLOWLIST_PATH", str(DEFAULT_ALLOWLIST_PATH)),
    )
    parser.add_argument(
        "--auto-agent-fail-closed",
        action="store_true",
        help="Stop the live loop if the no-send post-event agent pipeline fails.",
    )
    parser.add_argument("--site-name", help="Privacy-safe site label for OBS overlay receipts.")
    parser.add_argument("--site-mode", help="Privacy-safe site mode label for OBS overlay receipts.")
    return parser.parse_args()


def resolve_default_config_path() -> Path:
    if DEFAULT_LOCAL_CONFIG_PATH.exists():
        return DEFAULT_LOCAL_CONFIG_PATH
    return DEFAULT_EXAMPLE_CONFIG_PATH


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


def draw_frame(
    cv2,
    frame,
    result,
    config,
    fps_values: deque[float],
    *,
    appearance_overlay: bool = False,
    rgb_frame=None,
    floor_diagnostic: dict | None = None,
):
    display = frame.copy()
    zone = config.floor_zone
    height, width = display.shape[:2]
    vertices = tuple((int(x * width), int(y * height)) for x, y in zone.normalized_vertices())
    x1 = min(x for x, _y in vertices)
    y1 = min(y for _x, y in vertices)
    x2 = max(x for x, _y in vertices)
    y2 = max(y for _x, y in vertices)
    zone_fill = display.copy()
    if zone.vertices:
        import numpy as np

        polygon = np.array(vertices, dtype=np.int32)
        cv2.fillPoly(zone_fill, [polygon], (35, 125, 55))
        cv2.polylines(display, [polygon], True, (60, 220, 80), 3)
    else:
        cv2.rectangle(zone_fill, (x1, y1), (x2, y2), (35, 125, 55), -1)
        cv2.rectangle(display, (x1, y1), (x2, y2), (60, 220, 80), 2)
    display = cv2.addWeighted(zone_fill, 0.16, display, 0.84, 0)
    cv2.putText(
        display,
        "Calibrated Floor Plane" if zone.vertices else zone.name,
        (x1 + 8, max(y1 - 8, 24)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (60, 220, 80),
        2,
        cv2.LINE_AA,
    )

    posture_by_bbox = _posture_by_bbox(floor_diagnostic)
    active_person = _active_floor_person(floor_diagnostic)
    if result.boxes is not None:
        for box, conf, cls in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls, strict=False):
            cls_id = int(cls)
            name = class_name(result.names, cls_id)
            if not should_draw_detection_label(name):
                continue
            bx1, by1, bx2, by2 = [int(value) for value in box]
            posture = posture_by_bbox.get(
                (
                    round(float(box[0]), 1),
                    round(float(box[1]), 1),
                    round(float(box[2]), 1),
                    round(float(box[3]), 1),
                )
            )
            color = _box_color(posture, name)
            label = _box_label(name, float(conf), posture)
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
            if appearance_overlay and name == "person" and rgb_frame is not None:
                draw_appearance_overlay(cv2, display, rgb_frame, (bx1, by1, bx2, by2))

    avg_fps = sum(fps_values) / len(fps_values) if fps_values else 0.0
    if active_person:
        dwell = float(active_person.get("dwell_seconds", 0.0))
        required = float((floor_diagnostic or {}).get("required_dwell_seconds", config.floor_stay.dwell_seconds))
        posture_label = str(active_person.get("posture_label", "person_detected"))
        cv2.rectangle(display, (12, 48), (440, 104), (18, 24, 34), -1)
        cv2.putText(
            display,
            f"Floor-zone dwell: {dwell:.1f}/{required:.1f}s",
            (24, 72),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (40, 210, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            display,
            f"Posture: {posture_label.replace('_', ' ')}",
            (24, 96),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (230, 235, 240),
            2,
            cv2.LINE_AA,
        )
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


def _posture_by_bbox(diagnostic: dict | None) -> dict[tuple[float, float, float, float], dict]:
    if not diagnostic:
        return {}
    return {
        tuple(person["bbox_xyxy"]): person
        for person in diagnostic.get("people", [])
        if "bbox_xyxy" in person
    }


def should_draw_detection_label(label: str) -> bool:
    return label.strip().lower() in DISPLAY_LABELS


def _active_floor_person(diagnostic: dict | None) -> dict | None:
    if not diagnostic:
        return None
    selected_track_id = diagnostic.get("selected_track_id")
    if selected_track_id is None:
        return None
    for person in diagnostic.get("people", []):
        if person.get("track_id") == selected_track_id:
            return person
    return None


def _box_color(posture: dict | None, name: str) -> tuple[int, int, int]:
    if name != "person":
        return (40, 190, 255)
    if posture and posture.get("floor_stay_eligible"):
        return (40, 90, 255)
    if posture and posture.get("posture_label") == "seated_on_floor_possible":
        return (40, 210, 255)
    return (255, 80, 40)


def _box_label(name: str, confidence: float, posture: dict | None) -> str:
    if name != "person" or not posture:
        return f"{name} {confidence:.2f}"
    posture_label = str(posture.get("posture_label", "person_detected")).replace("_", " ")
    dwell = float(posture.get("dwell_seconds", 0.0))
    if posture.get("floor_stay_eligible"):
        return f"person {confidence:.2f} | {posture_label} | {dwell:.1f}s"
    return f"person {confidence:.2f} | {posture_label}"


def should_run_live_handoff(event: dict) -> bool:
    if event.get("status") != "awaiting_human_confirmation":
        return False
    allowed_actions = set(event.get("allowed_actions") or [])
    if "caregiver_alert" not in allowed_actions:
        return False
    return event.get("event_type") == "possible_floor_stay"


def live_message_for_event(event: dict, override: str | None = None) -> str:
    if override:
        return override
    evidence = event.get("evidence") or {}
    room = evidence.get("room_name") or event.get("room_name") or event.get("camera_id") or "the monitored room"
    return (
        f"CareSight alert. A possible floor-stay event needs review in {room}. "
        "This is not a medical or emergency claim. To connect, please respond with: yes connect or yes FaceTime."
    )


def draw_appearance_overlay(cv2, display, rgb_frame, bbox_xyxy):
    from caresight.runtime.appearance import appearance_region_receipt, descriptor_attributes, extract_appearance_descriptor

    height, width = display.shape[:2]
    descriptor = extract_appearance_descriptor(
        frame=rgb_frame,
        bbox_xyxy=tuple(float(value) for value in bbox_xyxy),
        frame_source="live_rtsp_frame",
        descriptor_source="runtime_observation",
    )
    attributes = descriptor_attributes(descriptor)
    receipt = appearance_region_receipt(
        bbox_xyxy=tuple(float(value) for value in bbox_xyxy),
        frame_width=width,
        frame_height=height,
    )
    colors = {
        "headwear": (168, 85, 247),
        "upper_body_color": (37, 99, 235),
        "lower_body_color": (22, 163, 74),
        "footwear": (220, 38, 38),
    }
    for region in receipt["descriptor_regions"]:
        region_name = str(region["region"])
        bbox = region["bbox_xyxy"]
        if bbox is None:
            continue
        attribute = attributes[region_name]
        label = f"{region_name}: {attribute['value']} {attribute['confidence']:.0%}"
        _draw_labeled_box(cv2, display, tuple(int(round(value)) for value in bbox), colors[region_name], label)
    if descriptor.descriptor_status != "available":
        x1, y1, _x2, y2 = [int(round(value)) for value in bbox_xyxy]
        cv2.putText(
            display,
            f"appearance: {descriptor.descriptor_status}",
            (x1 + 4, min(height - 10, y2 + 22)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (245, 245, 245),
            1,
            cv2.LINE_AA,
        )


def _draw_labeled_box(cv2, image, bbox, color, label):
    x1, y1, x2, y2 = bbox
    cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
    text_width = max(120, len(label) * 7)
    label_top = max(0, y1 - 18)
    cv2.rectangle(image, (x1, label_top), (x1 + text_width, label_top + 18), color, -1)
    cv2.putText(
        image,
        label,
        (x1 + 3, label_top + 13),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.38,
        (17, 24, 39),
        1,
        cv2.LINE_AA,
    )


def open_capture(cv2, config):
    from caresight.runtime.cameras import camera_source_for_opencv

    capture_source = camera_source_for_opencv(config.camera)
    if config.camera.source_type == "rtsp":
        cap = cv2.VideoCapture(capture_source)
    else:
        cap = cv2.VideoCapture(capture_source, cv2.CAP_AVFOUNDATION)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.camera.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.camera.height)
    cap.set(cv2.CAP_PROP_FPS, config.camera.fps)
    return cap


def read_frame_with_reconnect(
    *,
    cv2,
    cap,
    config,
    timeout_seconds: float,
    retry_delay_seconds: float,
):
    ok, frame = cap.read()
    if ok:
        return cap, frame
    if config.camera.source_type != "rtsp" or timeout_seconds <= 0:
        return cap, None

    deadline = time.monotonic() + timeout_seconds
    attempts = 0
    while time.monotonic() < deadline:
        attempts += 1
        cap.release()
        time.sleep(max(retry_delay_seconds, 0.05))
        cap = open_capture(cv2, config)
        if not cap.isOpened():
            continue
        ok, frame = cap.read()
        if ok:
            print(
                "camera_read_recovered "
                + json.dumps({"attempts": attempts, "camera_id": config.camera.camera_id}, sort_keys=True),
                flush=True,
            )
            return cap, frame
    print(
        "camera_read_failed "
        + json.dumps(
            {
                "camera_id": config.camera.camera_id,
                "retry_timeout_seconds": timeout_seconds,
                "source_type": config.camera.source_type,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return cap, None


class MjpegPreviewServer:
    def __init__(self, *, host: str, port: int, token: str | None = None):
        self.host = host
        self.port = port
        self.token = token
        self._condition = threading.Condition()
        self._jpeg: bytes | None = None
        self._updated_at = ""
        self._sequence = 0
        self._server = ThreadingHTTPServer((host, port), self._handler())
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}/live.html"

    def _html_body(self, request_path: str) -> bytes:
        stream_src = "/stream.mjpg"
        if self.token is not None and "token=" in request_path:
            supplied = request_path.split("token=", 1)[1].split("&", 1)[0]
            stream_src = "/stream.mjpg?token=" + supplied
        body = (
            "<!doctype html>\n"
            "<html>\n"
            "<head>\n"
            '  <meta charset="utf-8" />\n'
            "  <style>\n"
            "    html, body { width: 100%; height: 100%; margin: 0; overflow: hidden; background: #02060b; }\n"
            "    img { width: 100vw; height: 100vh; object-fit: contain; background: #02060b; }\n"
            "  </style>\n"
            "</head>\n"
            "<body>\n"
            f'  <img src="{html_escape(stream_src, quote=True)}" alt="" />\n'
            "</body>\n"
            "</html>\n"
        )
        return body.encode("utf-8")

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()

    def update(self, cv2, frame) -> None:
        ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
        if not ok:
            return
        with self._condition:
            self._jpeg = encoded.tobytes()
            self._updated_at = utc_now()
            self._sequence += 1
            self._condition.notify_all()

    def _snapshot(self) -> tuple[bytes | None, str, int]:
        with self._condition:
            return self._jpeg, self._updated_at, self._sequence

    def _wait_for_frame(self, last_sequence: int, timeout: float = 2.0) -> tuple[bytes | None, str, int]:
        with self._condition:
            if self._jpeg is None or self._sequence <= last_sequence:
                self._condition.wait(timeout)
            return self._jpeg, self._updated_at, self._sequence

    def _handler(self):
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802 - stdlib handler API.
                if not self._authorized():
                    self.send_error(401, "Missing or invalid preview token")
                    return
                route = self.path.split("?", 1)[0]
                if route in {"/", "/live.html"}:
                    self._write_html()
                    return
                if route == "/health":
                    jpeg, updated_at, sequence = owner._snapshot()
                    self._write_json(
                        {
                            "status": "ready",
                            "frame_available": jpeg is not None,
                            "sequence": sequence,
                            "updated_at": updated_at,
                        }
                    )
                    return
                if route == "/snapshot.jpg":
                    self._write_snapshot()
                    return
                if route == "/stream.mjpg":
                    self._write_stream()
                    return
                self.send_error(404)

            def log_message(self, _format: str, *_args) -> None:
                return

            def _authorized(self) -> bool:
                if owner.token is None:
                    return True
                header = self.headers.get("Authorization", "")
                if header.startswith("Bearer ") and secrets.compare_digest(header.removeprefix("Bearer ").strip(), owner.token):
                    return True
                token_marker = "token="
                if token_marker in self.path:
                    supplied = self.path.split(token_marker, 1)[1].split("&", 1)[0]
                    return secrets.compare_digest(supplied, owner.token)
                return False

            def _write_html(self) -> None:
                body = owner._html_body(self.path)
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _write_json(self, payload: dict) -> None:
                body = json.dumps(payload, sort_keys=True).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _write_snapshot(self) -> None:
                jpeg, updated_at, _sequence = owner._snapshot()
                if jpeg is None:
                    self.send_error(503, "No frame available yet")
                    return
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-CareSight-Updated-At", updated_at)
                self.send_header("Content-Length", str(len(jpeg)))
                self.end_headers()
                self.wfile.write(jpeg)

            def _write_stream(self) -> None:
                self.send_response(200)
                self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                last_sequence = 0
                while True:
                    jpeg, updated_at, sequence = owner._wait_for_frame(last_sequence)
                    if jpeg is None:
                        continue
                    if sequence <= last_sequence:
                        continue
                    last_sequence = sequence
                    try:
                        self.wfile.write(b"--frame\r\n")
                        self.wfile.write(b"Content-Type: image/jpeg\r\n")
                        self.wfile.write(f"X-CareSight-Updated-At: {updated_at}\r\n".encode("utf-8"))
                        self.wfile.write(f"Content-Length: {len(jpeg)}\r\n\r\n".encode("utf-8"))
                        self.wfile.write(jpeg)
                        self.wfile.write(b"\r\n")
                    except (BrokenPipeError, ConnectionResetError):
                        break

        return Handler


def should_stop_loop(
    *,
    started_at: float,
    now: float,
    max_seconds: float | None,
    event_persisted: bool,
    stop_after_event: bool,
) -> bool:
    if stop_after_event and event_persisted:
        return True
    if max_seconds is not None and now - started_at >= max_seconds:
        return True
    return False


def resolve_runtime_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def preview_bind_scope(host: str) -> str:
    if host in {"localhost", "::1"}:
        return "loopback"
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return "lan"
    return "loopback" if address.is_loopback else "lan"


def validate_preview_exposure(*, host: str, allow_lan: bool, token: str | None, acknowledged: bool) -> dict[str, object]:
    bind_scope = preview_bind_scope(host)
    if bind_scope == "lan":
        if not allow_lan:
            raise SystemExit("Refusing non-loopback MJPEG preview bind without --allow-lan-preview.")
        if not token:
            raise SystemExit("Refusing LAN MJPEG preview without --preview-token.")
        if not acknowledged:
            raise SystemExit("Refusing LAN MJPEG preview without --ack-lan-preview-risk.")
    return {
        "schema": "local-feed-exposure",
        "feed_id": f"feed_{uuid4().hex}",
        "bind_host": host,
        "bind_scope": bind_scope,
        "auth_required": bind_scope == "lan",
        "token_required": bind_scope == "lan",
        "operator_approved": bind_scope == "lan",
        "expires_at": (datetime.now(UTC) + timedelta(hours=4)).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "privacy_warning_acknowledged": bind_scope == "lan",
    }


def format_started_line(config, database_path: Path) -> str:
    return (
        "v0_started "
        f"camera={config.camera.camera_id} room={config.room.name} "
        f"source_type={config.camera.source_type} zone={config.floor_zone.zone_id} "
        f"required_dwell_seconds={config.floor_stay.dwell_seconds} db={database_path}"
    )


def build_no_event_check(
    *,
    started_at: str,
    completed_at: str,
    elapsed_seconds: float,
    frame_count: int,
    config,
) -> dict:
    check_id = f"check_{uuid4().hex}"
    result = {
        "camera_id": config.camera.camera_id,
        "elapsed_seconds": round(elapsed_seconds, 2),
        "frame_count": frame_count,
        "required_dwell_seconds": config.floor_stay.dwell_seconds,
        "status": "no_possible_floor_stay_event",
        "zone_id": config.floor_zone.zone_id,
    }
    return {
        "schema": "observation-check",
        "check_id": check_id,
        "check_type": "normal_presence_no_event",
        "started_at": started_at,
        "completed_at": completed_at,
        "camera_id": config.camera.camera_id,
        "zone_id": config.floor_zone.zone_id,
        "status": "no_event_persisted",
        "frame_count": frame_count,
        "elapsed_seconds": round(elapsed_seconds, 2),
        "required_dwell_seconds": config.floor_stay.dwell_seconds,
        "event_id": None,
        "result": result,
    }


def format_no_event_line(check: dict) -> str:
    payload = {
        "camera_id": check["camera_id"],
        "check_id": check["check_id"],
        "elapsed_seconds": check["elapsed_seconds"],
        "frame_count": check["frame_count"],
        "required_dwell_seconds": check["required_dwell_seconds"],
        "status": "no_possible_floor_stay_event",
        "zone_id": check["zone_id"],
    }
    return "no_event_persisted " + json.dumps(
        payload,
        sort_keys=True,
    )


def format_appearance_sample_line(sample: dict) -> str:
    payload = {
        "appearance_profile_id": sample["appearance_profile_id"],
        "quality_score": sample["quality_score"],
        "sample_id": sample["sample_id"],
        "snapshot_path": sample["snapshot_path"],
        "summary": sample["summary"],
        "track_id": sample["track_id"],
    }
    return "appearance_sample_persisted " + json.dumps(payload, sort_keys=True)


def format_floor_stay_debug_line(diagnostic: dict) -> str:
    return "floor_stay_debug " + json.dumps(diagnostic, sort_keys=True)


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def maybe_capture_appearance_sample(
    *,
    cv2,
    store,
    frame,
    rgb_frame,
    tracked_people,
    config,
    database_path: Path,
    min_quality_score: float,
    max_samples_per_profile: int,
) -> dict | None:
    from caresight.runtime.appearance import (
        AppearanceProfile,
        AppearanceProfileService,
        descriptor_attributes,
        render_appearance_summary,
        score_appearance_sample,
    )

    if not tracked_people:
        return None
    height, width = frame.shape[:2]
    service = AppearanceProfileService()
    candidates = []
    for track in tracked_people:
        detection = track.detection
        if not detection.is_person():
            continue
        descriptor = service.describe_observation(
            bbox_xyxy=detection.bbox_xyxy,
            frame=rgb_frame,
            frame_source="periodic_live_sample",
            descriptor_source="runtime_observation",
        )
        quality = score_appearance_sample(
            descriptor=descriptor,
            bbox_xyxy=detection.bbox_xyxy,
            frame_width=width,
            frame_height=height,
            detection_confidence=detection.confidence,
        )
        if quality.accepted and quality.score >= min_quality_score:
            candidates.append((quality.score, track, descriptor, quality))
    if not candidates:
        return None

    _score, track, descriptor, quality = max(candidates, key=lambda candidate: candidate[0])
    captured_at = utc_now()
    active_date = captured_at[:10]
    profile_id = _appearance_profile_id(active_date, track.track_id)
    sample_id = f"appearance_sample_{uuid4().hex}"
    sample_dir = database_path.parent / "appearance-samples" / active_date / profile_id
    sample_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = sample_dir / f"{sample_id}.jpg"
    cv2.imwrite(str(snapshot_path), frame)
    attributes = descriptor_attributes(descriptor)
    profile = {
        "appearance_profile_id": profile_id,
        "active_date": active_date,
        "created_at": captured_at,
        "updated_at": captured_at,
        "expires_at": (
            datetime.fromisoformat(active_date).replace(tzinfo=UTC) + timedelta(days=1)
        ).replace(hour=4).isoformat().replace("+00:00", "Z"),
        "descriptor_source": descriptor.descriptor_source,
        "created_from": descriptor.descriptor_source,
        "descriptor_status": descriptor.descriptor_status,
        "source_event_id": None,
        "source_observation_id": None,
        "snapshot_path": str(snapshot_path),
        "frame_source": "periodic_live_sample",
        "last_seen_at": captured_at,
        "last_seen_camera_id": config.camera.camera_id,
        "last_seen_room": config.room.name,
        "role_assignment": "unknown_person",
        "assignment_source": "unassigned",
        "assigned_by": None,
        "assigned_at": None,
        "attributes": attributes,
    }
    sample = {
        "sample_id": sample_id,
        "appearance_profile_id": profile_id,
        "active_date": active_date,
        "captured_at": captured_at,
        "camera_id": config.camera.camera_id,
        "room": config.room.name,
        "track_id": track.track_id,
        "source_event_id": None,
        "source_observation_id": None,
        "snapshot_path": str(snapshot_path),
        "frame_source": "periodic_live_sample",
        "descriptor_status": descriptor.descriptor_status,
        "quality_score": quality.score,
        "quality_reasons": quality.reasons,
        "detection_confidence": round(track.detection.confidence, 4),
        "bbox_xyxy": list(track.detection.bbox_xyxy),
        "attributes": attributes,
        "retained_rank": 0,
        "created_at": captured_at,
    }
    store.upsert_appearance_profile(profile)
    store.insert_appearance_profile_sample(sample)
    store.prune_appearance_profile_samples(profile_id, max_samples=max_samples_per_profile)
    render_profile = AppearanceProfile(
        appearance_profile_id=profile_id,
        active_date=active_date,
        expires_at=profile["expires_at"],
        role_assignment="unknown_person",
        assignment_source="unassigned",
        track_id=track.track_id,
        upper_body_color=descriptor.upper_body_color.value,
        lower_body_color=descriptor.lower_body_color.value,
        headwear=descriptor.headwear.value,
        footwear=descriptor.footwear.value,
        last_seen_camera_id=config.camera.camera_id,
        last_seen_room=config.room.name,
        last_seen_at=captured_at,
    )
    return {**sample, "summary": render_appearance_summary(render_profile)}


def _appearance_profile_id(active_date: str, source: str) -> str:
    suffix = "".join(ch if ch.isalnum() else "_" for ch in source.lower()).strip("_")
    return f"appearance_{active_date.replace('-', '_')}_{suffix[:32]}"


def update_last_seen_cache(last_seen_cache: dict, tracked_people, frame, rgb_frame) -> None:
    for track in tracked_people:
        if not track.detection.is_person():
            continue
        last_seen_cache[track.track_id] = {
            "bbox_xyxy": tuple(track.detection.bbox_xyxy),
            "confidence": track.detection.confidence,
            "first_seen_at": track.first_seen_at,
            "frame": frame.copy(),
            "frame_height": track.detection.frame_height,
            "frame_width": track.detection.frame_width,
            "last_seen_at": track.last_seen_at,
            "rgb_frame": rgb_frame.copy(),
        }


def missing_candidates_from_last_seen(last_seen_cache: dict, *, now: float, missing_seconds: float):
    from caresight.runtime.tracking import TrackSnapshot
    from caresight.vision.detections import Detection

    candidates = []
    for track_id, cached in last_seen_cache.items():
        missed_seconds = round(now - float(cached["last_seen_at"]), 2)
        if missed_seconds < missing_seconds:
            continue
        detection = Detection(
            class_name="person",
            confidence=float(cached["confidence"]),
            bbox_xyxy=tuple(float(value) for value in cached["bbox_xyxy"]),
            frame_width=int(cached["frame_width"]),
            frame_height=int(cached["frame_height"]),
        )
        candidates.append(
            TrackSnapshot(
                track_id=track_id,
                detection=detection,
                first_seen_at=float(cached["first_seen_at"]),
                last_seen_at=float(cached["last_seen_at"]),
                missed_seconds=missed_seconds,
            )
        )
    return candidates


def add_last_seen_appearance(event: dict, cached: dict | None) -> dict:
    if cached is None:
        return event
    try:
        from caresight.runtime.appearance import descriptor_attributes, extract_appearance_descriptor

        descriptor = extract_appearance_descriptor(
            frame=cached["rgb_frame"],
            bbox_xyxy=tuple(float(value) for value in cached["bbox_xyxy"]),
            frame_source="missing_last_seen_frame",
            descriptor_source="runtime_observation",
        )
        event["evidence"]["last_seen_appearance"] = {
            "attributes": descriptor_attributes(descriptor),
            "descriptor_status": descriptor.descriptor_status,
            "identity_boundary": "non_biometric_daily_appearance_only",
        }
    except Exception as exc:  # noqa: BLE001 - appearance is advisory, not event authority.
        event["evidence"]["last_seen_appearance"] = {
            "descriptor_status": "unavailable",
            "reason": f"{type(exc).__name__}: {exc}",
        }
    return event


def run_post_event_agent_dry_run(
    *,
    store,
    event_id: str,
    gemma_base_url: str,
    gemma_model: str,
    allowed_contact_id: str,
    allowlist_config: str,
    site_name: str | None = None,
    site_mode: str | None = None,
) -> dict:
    from caresight.runtime.agent_assist import (
        GemmaLocalProvider,
        build_agent_draft,
        contact_ids,
        load_contact_allowlist,
        run_hermes_dry_run,
        stage_action_request,
    )

    update_obs_overlay(event_id, site_name=site_name, site_mode=site_mode)
    draft = build_agent_draft(
        store,
        event_id,
        purpose="alert_draft",
        provider=GemmaLocalProvider(endpoint=gemma_base_url, model=gemma_model),
    )
    allowlist = load_contact_allowlist(allowlist_config)
    request = stage_action_request(
        store,
        event_id=event_id,
        source_draft_id=draft["draft_id"],
        requested_action="send_imessage_draft",
        destination="imessage",
        escalation_level="urgent_handoff",
        recipient_role="emergency_contact",
        allowed_contact_ids=[allowed_contact_id],
        response_options=["request_local_screen_capture", "request_facetime_handoff"],
        contact_allowlist=contact_ids(allowlist),
    )
    attempt = run_hermes_dry_run(store, request=request, draft=draft, vendor_path=ROOT_DIR / "vendor" / "hermes-agent")
    return {
        "event_id": event_id,
        "draft_id": draft["draft_id"],
        "draft_provider": draft["provider"],
        "draft_validation_status": draft["validation_status"],
        "request_id": request["request_id"],
        "attempt_id": attempt["attempt_id"],
        "execution_state": attempt["execution_state"],
        "external_action_performed": attempt["external_action_performed"],
        "obs_overlay_updated": True,
    }


def run_post_event_agent_live_run(
    *,
    store,
    event_id: str,
    gemma_base_url: str,
    gemma_model: str,
    allowed_contact_id: str,
    allowlist_config: str,
    live_message: str | None,
    live_imessage_target: str | None,
    live_approved: bool,
    auto_facetime_on_reply: bool,
    reply_timeout_seconds: float,
    reply_poll_interval_seconds: float,
    no_response_escalation_seconds: float,
    no_response_escalation_message: str,
    play_tts_after_facetime: bool,
    tts_text: str,
    tts_voice: str,
    tts_audio_route: str,
    tts_volume: float,
    tts_repeat_count: int,
    tts_repeat_delay_seconds: float,
    tts_after_facetime_delay_seconds: float,
    post_facetime_hold_seconds: float,
    site_name: str | None = None,
    site_mode: str | None = None,
) -> dict:
    from caresight.runtime.agent_assist import (
        execute_facetime_if_yes,
        execute_live_imessage,
        record_facetime_not_requested,
        wait_for_yes_reply,
    )

    event = store.get_event(event_id)
    approved_live_message = live_message_for_event(event, live_message)
    receipt = run_post_event_agent_dry_run(
        store=store,
        event_id=event_id,
        gemma_base_url=gemma_base_url,
        gemma_model=gemma_model,
        allowed_contact_id=allowed_contact_id,
        allowlist_config=allowlist_config,
        site_name=site_name,
        site_mode=site_mode,
    )
    reply_watch_started_at = time.time()
    live_attempt = execute_live_imessage(
        store,
        request_id=receipt["request_id"],
        message=approved_live_message,
        contact_id=allowed_contact_id,
        allowlist_config=allowlist_config,
        target=live_imessage_target,
        live_approved=live_approved,
    )
    update_obs_overlay(event_id)
    live_receipt = {
        **receipt,
        "live_attempt_id": live_attempt["attempt_id"],
        "live_execution_state": live_attempt["execution_state"],
        "live_result": live_attempt["result"],
        "external_action_performed": live_attempt["external_action_performed"],
        "facetime_started": False,
        "facetime_next_step": "run caresight_live_handoff.py facetime-if-yes with the caregiver reply text",
    }
    if not auto_facetime_on_reply:
        return live_receipt

    reply_target = live_imessage_target
    if not reply_target:
        reply_target = _resolve_live_target_for_channel(allowed_contact_id, allowlist_config, "imessage")
    facetime_target = _resolve_live_target_for_channel(allowed_contact_id, allowlist_config, "facetime")
    first_reply_timeout = reply_timeout_seconds
    if no_response_escalation_seconds > 0:
        first_reply_timeout = min(reply_timeout_seconds, no_response_escalation_seconds)
    reply = wait_for_yes_reply(
        target=reply_target,
        since_unix_seconds=reply_watch_started_at,
        timeout_seconds=first_reply_timeout,
        poll_interval_seconds=reply_poll_interval_seconds,
    )
    live_receipt["reply_watch"] = reply
    if not reply.get("reply_interpreted_as_yes"):
        if no_response_escalation_seconds > 0 and reply.get("status") == "timeout":
            snapshot_path = escalation_attachment_path(event)
            media_policy = build_event_snapshot_media_policy(event_id, snapshot_path) if snapshot_path else None
            escalation_attempt = execute_live_imessage(
                store,
                request_id=receipt["request_id"],
                message=no_response_escalation_message,
                contact_id=allowed_contact_id,
                allowlist_config=allowlist_config,
                target=live_imessage_target,
                attachment_path=snapshot_path,
                media_policy=media_policy,
                result_name="imessage_no_response_escalation_sent",
                live_approved=live_approved,
            )
            update_obs_overlay(event_id)
            live_receipt["no_response_escalation"] = {
                "attempt_id": escalation_attempt["attempt_id"],
                "result": escalation_attempt["result"],
                "external_action_performed": escalation_attempt["external_action_performed"],
                "attachment_included": bool(snapshot_path),
                "attachment_delivery": escalation_attempt.get("payload", {}).get("delivery", {}).get("attachment"),
            }
            remaining_timeout = max(reply_timeout_seconds - first_reply_timeout, 0.0)
            if remaining_timeout > 0:
                second_reply = wait_for_yes_reply(
                    target=reply_target,
                    since_unix_seconds=time.time(),
                    timeout_seconds=remaining_timeout,
                    poll_interval_seconds=reply_poll_interval_seconds,
                )
                live_receipt["reply_watch_after_escalation"] = second_reply
                reply = second_reply
                if reply.get("reply_interpreted_as_yes"):
                    live_receipt["reply_watch"] = reply
                else:
                    no_facetime_attempt = record_facetime_not_requested(
                        store,
                        request_id=receipt["request_id"],
                        reply_watch=reply,
                        contact_id=allowed_contact_id,
                    )
                    live_receipt["facetime_attempt_id"] = no_facetime_attempt["attempt_id"]
                    live_receipt["facetime_result"] = no_facetime_attempt["result"]
                    live_receipt["facetime_next_step"] = "no yes-like reply observed after escalation timeout"
                    return live_receipt
            else:
                no_facetime_attempt = record_facetime_not_requested(
                    store,
                    request_id=receipt["request_id"],
                    reply_watch=reply,
                    contact_id=allowed_contact_id,
                )
                live_receipt["facetime_attempt_id"] = no_facetime_attempt["attempt_id"]
                live_receipt["facetime_result"] = no_facetime_attempt["result"]
                live_receipt["facetime_next_step"] = "no yes-like reply observed before escalation timeout"
                return live_receipt
        else:
            no_facetime_attempt = record_facetime_not_requested(
                store,
                request_id=receipt["request_id"],
                reply_watch=reply,
                contact_id=allowed_contact_id,
            )
            live_receipt["facetime_attempt_id"] = no_facetime_attempt["attempt_id"]
            live_receipt["facetime_result"] = no_facetime_attempt["result"]
            live_receipt["facetime_next_step"] = "no yes-like reply observed before timeout"
            return live_receipt
    if not reply.get("reply_interpreted_as_yes"):
        no_facetime_attempt = record_facetime_not_requested(
            store,
            request_id=receipt["request_id"],
            reply_watch=reply,
            contact_id=allowed_contact_id,
        )
        live_receipt["facetime_attempt_id"] = no_facetime_attempt["attempt_id"]
        live_receipt["facetime_result"] = no_facetime_attempt["result"]
        live_receipt["facetime_next_step"] = "no yes-like reply observed before timeout"
        return live_receipt

    facetime_attempt = execute_facetime_if_yes(
        store,
        request_id=receipt["request_id"],
        reply_text=str(reply.get("reply_text") or ""),
        contact_id=allowed_contact_id,
        allowlist_config=allowlist_config,
        target=facetime_target,
        live_approved=live_approved,
    )
    update_obs_overlay(event_id)
    live_receipt["facetime_attempt_id"] = facetime_attempt["attempt_id"]
    live_receipt["facetime_started"] = facetime_attempt["external_action_performed"]
    live_receipt["facetime_result"] = facetime_attempt["result"]
    if facetime_attempt["external_action_performed"] and tts_after_facetime_delay_seconds > 0:
        time.sleep(tts_after_facetime_delay_seconds)
    if play_tts_after_facetime:
        pending_tts_attempt = record_tts_playback_pending_attempt(
            store,
            request_id=receipt["request_id"],
            contact_id=allowed_contact_id,
            text=tts_text,
            voice=tts_voice,
            audio_route=tts_audio_route,
        )
        playback = play_tts(
            tts_text,
            voice=tts_voice,
            audio_route=tts_audio_route,
            volume=tts_volume,
            repeat_count=tts_repeat_count,
            repeat_delay_seconds=tts_repeat_delay_seconds,
        )
        live_receipt["tts_playback"] = playback
        tts_attempt = record_tts_playback_attempt(
            store,
            request_id=receipt["request_id"],
            contact_id=allowed_contact_id,
            text=tts_text,
            voice=tts_voice,
            audio_route=tts_audio_route,
            playback=playback,
            pending_attempt=pending_tts_attempt,
        )
        update_obs_overlay(event_id)
        live_receipt["tts_attempt_id"] = tts_attempt["attempt_id"]
        live_receipt["tts_result"] = tts_attempt["result"]
    if facetime_attempt["external_action_performed"] and post_facetime_hold_seconds > 0:
        time.sleep(post_facetime_hold_seconds)
        live_receipt["post_facetime_hold_seconds"] = post_facetime_hold_seconds
    return live_receipt


def record_tts_playback_attempt(
    store,
    *,
    request_id: str,
    contact_id: str,
    text: str,
    voice: str,
    audio_route: str,
    playback: dict,
    pending_attempt: dict | None = None,
) -> dict:
    request = store.get_agent_action_request(request_id)
    draft = store.get_agent_draft(request["source_draft_id"])
    ok = playback.get("status") == "played"
    payload = {
        "schema": "care-tts-live-playback",
        "request_id": request_id,
        "event_id": request["event_id"],
        "source_draft_id": draft["draft_id"],
        "approved_contact_id": contact_id,
        "execution_state": "executed" if ok else "failed",
        "live_channel": "tts",
        "live_message_text": text,
        "delivery": {
            "status": playback.get("status"),
            "voice": voice,
            "audio_route": audio_route,
            "volume": playback.get("volume"),
            "repeat_count": playback.get("repeat_count"),
            "repeat_delay_seconds": playback.get("repeat_delay_seconds"),
            "returncode": playback.get("returncode"),
            "stdout_tail": playback.get("stdout"),
            "stderr_tail": playback.get("stderr"),
        },
        "safety_boundaries": [
            "human_review_required",
            "local_tts_only",
            "no_autonomous_dispatch",
            "no_medical_diagnosis",
            "raw_video_stays_local",
        ],
    }
    attempt = {
        "schema": "agent-execution-attempt",
        "attempt_id": pending_attempt["attempt_id"] if pending_attempt else f"attempt_{uuid4().hex}",
        "request_id": request_id,
        "event_id": request["event_id"],
        "created_at": utc_now(),
        "harness": "local_macos_live_handoff",
        "attempt_kind": "live",
        "execution_state": "executed" if ok else "failed",
        "result": "tts_playback_requested" if ok else "tts_playback_failed",
        "error": None if ok else str(playback.get("stderr") or playback.get("stdout") or "tts playback failed")[-500:],
        "external_action_performed": ok,
        "payload": payload,
        "safety_boundaries": payload["safety_boundaries"],
        "provenance": {
            "source": "sqlite_action_request_and_operator_live_approval",
            "source_fields": ["agent_action_requests", "agent_drafts", "agent_execution_attempts"],
        },
    }
    if pending_attempt:
        store.update_agent_execution_attempt(attempt)
    else:
        store.insert_agent_execution_attempt(attempt)
    return attempt


def record_tts_playback_pending_attempt(
    store,
    *,
    request_id: str,
    contact_id: str,
    text: str,
    voice: str,
    audio_route: str,
) -> dict:
    request = store.get_agent_action_request(request_id)
    draft = store.get_agent_draft(request["source_draft_id"])
    payload = {
        "schema": "care-tts-live-playback",
        "request_id": request_id,
        "event_id": request["event_id"],
        "source_draft_id": draft["draft_id"],
        "approved_contact_id": contact_id,
        "execution_state": "pending_execution",
        "live_channel": "tts",
        "live_message_text": text,
        "delivery": {"status": "pending_execution", "voice": voice, "audio_route": audio_route},
        "safety_boundaries": [
            "human_review_required",
            "local_tts_only",
            "no_autonomous_dispatch",
            "no_medical_diagnosis",
            "raw_video_stays_local",
        ],
    }
    attempt = {
        "schema": "agent-execution-attempt",
        "attempt_id": f"attempt_{uuid4().hex}",
        "request_id": request_id,
        "event_id": request["event_id"],
        "created_at": utc_now(),
        "harness": "local_macos_live_handoff",
        "attempt_kind": "live",
        "execution_state": "pending_execution",
        "result": "tts_pending_execution",
        "error": None,
        "external_action_performed": False,
        "payload": payload,
        "safety_boundaries": payload["safety_boundaries"],
        "provenance": {
            "source": "sqlite_action_request_and_operator_live_approval",
            "source_fields": ["agent_action_requests", "agent_drafts", "agent_execution_attempts"],
        },
    }
    store.insert_agent_execution_attempt(attempt)
    return attempt


def escalation_attachment_path(event: dict) -> str | None:
    snapshot_path = event.get("evidence", {}).get("snapshot_path")
    if snapshot_path and Path(snapshot_path).expanduser().exists():
        return str(snapshot_path)
    if DEFAULT_OBS_PREVIEW_PATH.exists():
        return str(DEFAULT_OBS_PREVIEW_PATH)
    return None


def build_event_snapshot_media_policy(event_id: str, snapshot_path: str | None) -> dict | None:
    if not snapshot_path:
        return None
    return {
        "schema": "media-sharing-policy",
        "policy_id": f"media_policy_{event_id.replace('evt_', '')}_snapshot",
        "media_type": "event_scoped_snapshot",
        "scope": "event_scoped",
        "approval_state": "approved",
        "approved_by": "live_approved_operator",
        "approved_at": utc_now(),
        "redaction_required": True,
        "redaction_status": "completed",
        "retention_class": "ephemeral_handoff",
        "blocked_media_types": ["raw_video", "continuous_feed"],
        "provenance": {
            "event_id": event_id,
            "source": "operator_media_approval",
            "source_fields": ["events", "snapshot_path", "agent_execution_attempts"],
        },
    }


def _resolve_live_target_for_channel(contact_id: str, allowlist_config: str, channel: str) -> str:
    from caresight.runtime.agent_assist.live_handoff import resolve_contact_target

    target, _source = resolve_contact_target(
        contact_id=contact_id,
        channel=channel,
        allowlist_config=allowlist_config,
    )
    return target


def play_tts(
    text: str,
    *,
    voice: str,
    audio_route: str = "system",
    volume: float = 6.0,
    repeat_count: int = 1,
    repeat_delay_seconds: float = 1.0,
) -> dict:
    import subprocess

    repeat_count = max(1, int(repeat_count))
    tts_command = [
        sys.executable,
        str(ROOT_DIR / "scripts" / "caresight_tts.py"),
        "--voice",
        voice,
        "--text",
        text,
        "--play-volume",
        str(volume),
        "--play-repeat-count",
        str(repeat_count),
        "--play-repeat-delay-seconds",
        str(repeat_delay_seconds),
        "--play",
    ]
    command = tts_command
    if audio_route == "blackhole":
        command = [
            sys.executable,
            str(ROOT_DIR / "scripts" / "caresight_audio_route.py"),
            "run-with-blackhole",
            "--settle-before-seconds",
            "2.0",
            "--hold-after-seconds",
            "10.0",
            "--",
            *tts_command,
        ]
    result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    return {
        "status": "played" if result.returncode == 0 else "failed",
        "returncode": result.returncode,
        "voice": voice,
        "audio_route": audio_route,
        "volume": volume,
        "repeat_count": repeat_count,
        "repeat_delay_seconds": repeat_delay_seconds,
        "stdout": result.stdout.strip()[-500:],
        "stderr": result.stderr.strip()[-500:],
    }


def update_obs_overlay(event_id: str, *, site_name: str | None = None, site_mode: str | None = None) -> None:
    tool_path = REPO_ROOT / "apps" / "obs-hub" / "tools" / "update_obs_event.py"
    if not tool_path.exists():
        raise FileNotFoundError(tool_path)
    import importlib.util

    spec = importlib.util.spec_from_file_location("caresight_obs_update", tool_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load OBS update tool: {tool_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    db_path = REPO_ROOT / "apps" / "caresight-hub" / "data" / "caresight-v0.sqlite3"
    args = argparse.Namespace(
        db=str(db_path),
        event_id=event_id,
        output=str(REPO_ROOT / "apps" / "obs-hub" / "config" / "current_event.json"),
        js_output=str(REPO_ROOT / "apps" / "obs-hub" / "config" / "current_event.js"),
        site_name=site_name or "CareSight Local Demo",
        site_mode=site_mode or "Observation Mode",
        site_label_source="cli_or_config" if site_name or site_mode else "default_generic",
        recent_limit=4,
        live_preview=str(DEFAULT_OBS_PREVIEW_PATH),
        sample=False,
        dry_run=False,
        watch=False,
        interval_seconds=2.0,
    )
    payload = module.build_payload(args)
    module.write_outputs(
        payload,
        Path(args.output),
        Path(args.js_output),
    )


def maybe_write_obs_preview(
    *,
    cv2,
    frame,
    rgb_frame,
    result,
    config,
    fps_values: deque[float],
    preview_path: Path,
    last_write_at: float,
    preview_fps: float,
    appearance_overlay: bool,
    floor_diagnostic: dict | None,
) -> float:
    if preview_fps <= 0:
        return last_write_at
    now = time.monotonic()
    if last_write_at and now - last_write_at < 1.0 / preview_fps:
        return last_write_at
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    annotated = draw_frame(
        cv2,
        frame,
        result,
        config,
        fps_values,
        appearance_overlay=appearance_overlay,
        rgb_frame=rgb_frame,
        floor_diagnostic=floor_diagnostic,
    )
    cv2.imwrite(str(preview_path), annotated)
    return now


def format_post_event_agent_line(receipt: dict) -> str:
    return "post_event_agent_dry_run " + json.dumps(receipt, sort_keys=True)


def format_post_event_agent_live_line(receipt: dict) -> str:
    return "post_event_agent_live_run " + json.dumps(receipt, sort_keys=True)


def format_post_event_agent_error_line(event_id: str, error: BaseException) -> str:
    payload = {
        "event_id": event_id,
        "error": str(error),
        "error_type": type(error).__name__,
        "external_action_performed": False,
        "status": "post_event_agent_dry_run_failed",
    }
    return "post_event_agent_dry_run_failed " + json.dumps(payload, sort_keys=True)


def format_post_event_agent_live_error_line(event_id: str, error: BaseException) -> str:
    payload = {
        "event_id": event_id,
        "error": str(error),
        "error_type": type(error).__name__,
        "external_action_performed": False,
        "status": "post_event_agent_live_run_failed",
    }
    return "post_event_agent_live_run_failed " + json.dumps(payload, sort_keys=True)


def format_post_event_agent_live_skip_line(event_id: str) -> str:
    payload = {
        "event_id": event_id,
        "external_action_performed": False,
        "reason": "post_event_agent_live_run_already_in_progress",
        "status": "post_event_agent_live_run_skipped",
    }
    return "post_event_agent_live_run_skipped " + json.dumps(payload, sort_keys=True)


def main() -> None:
    args = parse_args()

    import cv2
    from yolo26mlx import YOLO

    from caresight.events.floor_stay import FloorStayDetector
    from caresight.events.missing_off_camera import MissingOffCameraDetector
    from caresight.events.snapshots import attach_local_snapshot
    from caresight.runtime.cameras import select_configured_camera
    from caresight.runtime.config import CareSightConfig
    from caresight.storage.sqlite_store import SQLiteStore

    config_path = Path(args.config) if args.config else resolve_default_config_path()
    config = select_configured_camera(
        CareSightConfig.load(config_path),
        camera_id=args.camera_id,
        source_type=args.source_type,
    )
    model_path = Path(args.model)
    if not model_path.exists():
        raise SystemExit(f"Missing model: {model_path}")

    database_path = resolve_runtime_path(config.storage.database_path)
    store = SQLiteStore(database_path)
    store.initialize()
    store.upsert_config(config)

    model = YOLO(str(model_path))
    cap = open_capture(cv2, config)
    if not cap.isOpened():
        raise SystemExit(f"Could not open camera {config.camera.source_uri}")

    detector = FloorStayDetector(config)
    missing_detector = MissingOffCameraDetector(config)
    fps_values: deque[float] = deque(maxlen=30)
    print(format_started_line(config, database_path))
    mjpeg_server = None
    if args.obs_browser_feed:
        exposure = validate_preview_exposure(
            host=args.obs_browser_feed_host,
            allow_lan=args.allow_lan_preview,
            token=args.preview_token,
            acknowledged=args.ack_lan_preview_risk,
        )
        mjpeg_server = MjpegPreviewServer(
            host=args.obs_browser_feed_host,
            port=args.obs_browser_feed_port,
            token=args.preview_token if exposure["bind_scope"] == "lan" else None,
        )
        mjpeg_server.start()
        stream_path = "/stream.mjpg"
        page_path = "/live.html"
        if exposure["bind_scope"] == "lan":
            stream_path += f"?token={args.preview_token}"
            page_path += f"?token={args.preview_token}"
        print(
            "obs_browser_feed_started "
            + json.dumps(
                {
                    "url": f"http://{args.obs_browser_feed_host}:{args.obs_browser_feed_port}{page_path}",
                    "stream_url": f"http://{args.obs_browser_feed_host}:{args.obs_browser_feed_port}{stream_path}",
                    "exposure": exposure,
                },
                sort_keys=True,
            )
        )

    use_preview_window = args.show_window or (not args.no_window and not args.obs_browser_feed)

    if use_preview_window:
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(WINDOW_NAME, config.camera.width, config.camera.height)

    loop_started_at = time.monotonic()
    check_started_at = utc_now()
    frame_count = 0
    persisted_event_count = 0
    obs_preview_path = resolve_runtime_path(args.obs_live_preview_path)
    last_obs_preview_write_at = 0.0
    last_floor_debug_at = 0.0
    post_event_threads: list[threading.Thread] = []
    post_event_live_lock = threading.Lock()
    post_event_live_running = False
    last_appearance_sample_at = 0.0
    last_concern_severity = None
    last_seen_cache = {}

    def run_post_event_live_in_background(event_id: str) -> bool:
        nonlocal post_event_live_running
        if args.auto_agent_fail_closed:
            return False
        with post_event_live_lock:
            if post_event_live_running:
                print(format_post_event_agent_live_skip_line(event_id), flush=True)
                return True
            post_event_live_running = True

        def worker() -> None:
            nonlocal post_event_live_running
            worker_store = SQLiteStore(database_path)
            try:
                receipt = run_post_event_agent_live_run(
                    store=worker_store,
                    event_id=event_id,
                    gemma_base_url=args.gemma_base_url,
                    gemma_model=args.gemma_model,
                    allowed_contact_id=args.allowed_contact_id,
                    allowlist_config=args.allowlist_config,
                    live_message=args.live_message,
                    live_imessage_target=args.live_imessage_target,
                    live_approved=args.live_approved,
                    auto_facetime_on_reply=args.auto_facetime_on_reply,
                    reply_timeout_seconds=args.reply_timeout_seconds,
                    reply_poll_interval_seconds=args.reply_poll_interval_seconds,
                    no_response_escalation_seconds=args.no_response_escalation_seconds,
                    no_response_escalation_message=args.no_response_escalation_message,
                    play_tts_after_facetime=args.play_tts_after_facetime,
                    tts_text=args.tts_text,
                    tts_voice=args.tts_voice,
                    tts_audio_route=args.tts_audio_route,
                    tts_volume=args.tts_volume,
                    tts_repeat_count=args.tts_repeat_count,
                    tts_repeat_delay_seconds=args.tts_repeat_delay_seconds,
                    tts_after_facetime_delay_seconds=args.tts_after_facetime_delay_seconds,
                    post_facetime_hold_seconds=args.post_facetime_hold_seconds,
                    site_name=args.site_name or config.site.name,
                    site_mode=args.site_mode or config.site.mode,
                )
                print(format_post_event_agent_live_line(receipt), flush=True)
            except Exception as exc:  # noqa: BLE001 - terminal receipt must include failure.
                print(format_post_event_agent_live_error_line(event_id, exc), file=sys.stderr, flush=True)
                traceback.print_exc()
            finally:
                with post_event_live_lock:
                    post_event_live_running = False

        thread = threading.Thread(target=worker, name=f"care-agent-live-{event_id[:12]}", daemon=False)
        thread.start()
        post_event_threads.append(thread)
        return True

    try:
        while True:
            started_at = time.perf_counter()
            cap, frame = read_frame_with_reconnect(
                cv2=cv2,
                cap=cap,
                config=config,
                timeout_seconds=args.camera_read_failure_timeout_seconds,
                retry_delay_seconds=args.camera_read_retry_delay_seconds,
            )
            if frame is None:
                break
            frame_count += 1

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = model.predict(rgb_frame, conf=args.conf)[0]
            height, width = frame.shape[:2]
            detections = result_to_detections(result, width, height)
            now_epoch = datetime.now(tz=UTC).timestamp()
            event = detector.update(detections, now=now_epoch)
            tracked_people = detector.tracked_people()
            update_last_seen_cache(last_seen_cache, tracked_people, frame, rgb_frame)
            if event is None and args.missing_off_camera_events:
                missing_candidates = missing_candidates_from_last_seen(
                    last_seen_cache,
                    now=now_epoch,
                    missing_seconds=config.tracking.missing_seconds,
                )
                event = missing_detector.update(
                    missing_candidates,
                    now=now_epoch,
                    recent_concern_severity=last_concern_severity,
                )
                if event is not None:
                    event = add_last_seen_appearance(event, last_seen_cache.get(event["evidence"]["track_id"]))
            if (
                args.appearance_sampling
                and time.monotonic() - last_appearance_sample_at >= args.appearance_sample_interval_seconds
            ):
                sample = maybe_capture_appearance_sample(
                    cv2=cv2,
                    store=store,
                    frame=frame,
                    rgb_frame=rgb_frame,
                    tracked_people=tracked_people,
                    config=config,
                    database_path=database_path,
                    min_quality_score=args.appearance_min_quality_score,
                    max_samples_per_profile=args.appearance_max_samples_per_profile,
                )
                if sample is not None:
                    last_appearance_sample_at = time.monotonic()
                    print(format_appearance_sample_line(sample))
            if args.debug_floor_stay and time.monotonic() - last_floor_debug_at >= 1.0:
                print(format_floor_stay_debug_line(detector.diagnostic()))
                last_floor_debug_at = time.monotonic()

            annotated_frame = None
            floor_diagnostic = detector.diagnostic()
            if args.obs_browser_feed or args.obs_live_preview or use_preview_window:
                annotated_frame = draw_frame(
                    cv2,
                    frame,
                    result,
                    config,
                    fps_values,
                    appearance_overlay=args.appearance_overlay,
                    rgb_frame=rgb_frame,
                    floor_diagnostic=floor_diagnostic,
                )
            if mjpeg_server is not None and annotated_frame is not None:
                mjpeg_server.update(cv2, annotated_frame)
            if args.obs_live_preview:
                last_obs_preview_write_at = maybe_write_obs_preview(
                    cv2=cv2,
                    frame=frame,
                    rgb_frame=rgb_frame,
                    result=result,
                    config=config,
                    fps_values=fps_values,
                    preview_path=obs_preview_path,
                    last_write_at=last_obs_preview_write_at,
                    preview_fps=args.obs_live_preview_fps,
                    appearance_overlay=args.appearance_overlay,
                    floor_diagnostic=floor_diagnostic,
                )
            event_persisted = False
            if event is not None:
                snapshot_dir = database_path.parent / "snapshots"
                snapshot_frame = frame
                if event["event_type"] == "missing_off_camera_extended":
                    cached = last_seen_cache.get(event["evidence"]["track_id"])
                    if cached is not None:
                        snapshot_frame = cached["frame"]
                event = attach_local_snapshot(
                    event=event,
                    snapshot_dir=snapshot_dir,
                    write_snapshot=lambda path: cv2.imwrite(str(path), snapshot_frame),
                )
                store.insert_event(event)
                print("event_persisted " + json.dumps(event, sort_keys=True))
                event_persisted = True
                persisted_event_count += 1
                last_concern_severity = event.get("severity")
                if args.auto_agent_live_run and should_run_live_handoff(event):
                    if not run_post_event_live_in_background(event["event_id"]):
                        try:
                            receipt = run_post_event_agent_live_run(
                                store=store,
                                event_id=event["event_id"],
                                gemma_base_url=args.gemma_base_url,
                                gemma_model=args.gemma_model,
                                allowed_contact_id=args.allowed_contact_id,
                                allowlist_config=args.allowlist_config,
                                live_message=args.live_message,
                                live_imessage_target=args.live_imessage_target,
                                live_approved=args.live_approved,
                                auto_facetime_on_reply=args.auto_facetime_on_reply,
                                reply_timeout_seconds=args.reply_timeout_seconds,
                                reply_poll_interval_seconds=args.reply_poll_interval_seconds,
                                no_response_escalation_seconds=args.no_response_escalation_seconds,
                                no_response_escalation_message=args.no_response_escalation_message,
                                play_tts_after_facetime=args.play_tts_after_facetime,
                                tts_text=args.tts_text,
                                tts_voice=args.tts_voice,
                                tts_audio_route=args.tts_audio_route,
                                tts_volume=args.tts_volume,
                                tts_repeat_count=args.tts_repeat_count,
                                tts_repeat_delay_seconds=args.tts_repeat_delay_seconds,
                                tts_after_facetime_delay_seconds=args.tts_after_facetime_delay_seconds,
                                post_facetime_hold_seconds=args.post_facetime_hold_seconds,
                                site_name=args.site_name or config.site.name,
                                site_mode=args.site_mode or config.site.mode,
                            )
                            print(format_post_event_agent_live_line(receipt))
                        except Exception as exc:  # noqa: BLE001 - terminal receipt must include failure.
                            print(format_post_event_agent_live_error_line(event["event_id"], exc), file=sys.stderr)
                            traceback.print_exc()
                            if args.auto_agent_fail_closed:
                                raise
                elif args.auto_agent_dry_run:
                    try:
                        receipt = run_post_event_agent_dry_run(
                            store=store,
                            event_id=event["event_id"],
                            gemma_base_url=args.gemma_base_url,
                            gemma_model=args.gemma_model,
                            allowed_contact_id=args.allowed_contact_id,
                            allowlist_config=args.allowlist_config,
                            site_name=args.site_name or config.site.name,
                            site_mode=args.site_mode or config.site.mode,
                        )
                        print(format_post_event_agent_line(receipt))
                    except Exception as exc:  # noqa: BLE001 - terminal receipt must include failure.
                        print(format_post_event_agent_error_line(event["event_id"], exc), file=sys.stderr)
                        traceback.print_exc()
                        if args.auto_agent_fail_closed:
                            raise

            elapsed = max(time.perf_counter() - started_at, 0.0001)
            fps_values.append(1.0 / elapsed)

            if should_stop_loop(
                started_at=loop_started_at,
                now=time.monotonic(),
                max_seconds=args.max_seconds,
                event_persisted=event_persisted,
                stop_after_event=args.stop_after_event,
            ):
                break

            if use_preview_window and annotated_frame is not None:
                cv2.imshow(WINDOW_NAME, annotated_frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        if mjpeg_server is not None:
            mjpeg_server.stop()
        for thread in post_event_threads:
            if thread.is_alive():
                thread.join()

    elapsed_seconds = time.monotonic() - loop_started_at
    if frame_count > 0 and persisted_event_count == 0:
        check = build_no_event_check(
            started_at=check_started_at,
            completed_at=utc_now(),
            elapsed_seconds=elapsed_seconds,
            frame_count=frame_count,
            config=config,
        )
        store.insert_observation_check(check)
        print(format_no_event_line(check))

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
