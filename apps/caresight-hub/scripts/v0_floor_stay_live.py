import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import re
import sys
import threading
import time
import traceback
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

ROOT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT_DIR.parents[1]
YOLO_DIR = ROOT_DIR / "vendor" / "yolo-mlx"
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(YOLO_DIR))
DEFAULT_CONFIG_PATH = ROOT_DIR / "config" / "v0.local.json"
DEFAULT_MODEL_PATH = ROOT_DIR / "vendor" / "yolo-mlx" / "models" / "yolo26n.npz"
WINDOW_NAME = "CareSight v0 Floor Stay"
DEFAULT_OBS_PREVIEW_PATH = REPO_ROOT / "apps" / "obs-hub" / "config" / "live_preview.jpg"
DEFAULT_ALLOWLIST_PATH = ROOT_DIR / "config" / "hermes" / "allowlisted-contacts.example.json"
DEFAULT_BROWSER_FEED_HOST = "127.0.0.1"
DEFAULT_BROWSER_FEED_PORT = 8766


def parse_args():
    parser = argparse.ArgumentParser(description="Run CareSight v0 possible-floor-stay loop.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="CareSight v0 config JSON.")
    parser.add_argument("--model", default=str(DEFAULT_MODEL_PATH), help="YOLO26 MLX .npz model path.")
    parser.add_argument("--conf", type=float, default=0.25, help="YOLO confidence threshold.")
    parser.add_argument("--camera-id", help="Configured camera_id to select from config.cameras.")
    parser.add_argument(
        "--source-type",
        choices=["webcam", "usb", "continuity_camera", "rtsp"],
        help="Configured source_type to select when it resolves to one camera.",
    )
    parser.add_argument("--no-window", action="store_true", help="Run without an OpenCV preview window.")
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
        default=(
            "CareSight alert. Possible floor stay observed in the Living Room. Needs review. "
            "Would you like to connect to CareSight?"
        ),
        help="Approved live iMessage body.",
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
            "caregiver verification. Please see the image attached, and reply yes to see a live feed."
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
    parser.add_argument("--tts-volume", type=float, default=2.5, help="Playback gain passed to local TTS afplay.")
    parser.add_argument(
        "--tts-after-facetime-delay-seconds",
        type=float,
        default=8.0,
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


class MjpegPreviewServer:
    def __init__(self, *, host: str, port: int):
        self.host = host
        self.port = port
        self._condition = threading.Condition()
        self._jpeg: bytes | None = None
        self._updated_at = ""
        self._server = ThreadingHTTPServer((host, port), self._handler())
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}/live.html"

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
            self._condition.notify_all()

    def _snapshot(self) -> tuple[bytes | None, str]:
        with self._condition:
            return self._jpeg, self._updated_at

    def _wait_for_frame(self, timeout: float = 2.0) -> tuple[bytes | None, str]:
        with self._condition:
            if self._jpeg is None:
                self._condition.wait(timeout)
            return self._jpeg, self._updated_at

    def _handler(self):
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802 - stdlib handler API.
                if self.path in {"/", "/live.html"}:
                    self._write_html()
                    return
                if self.path == "/health":
                    self._write_json({"status": "ready", "frame_available": owner._snapshot()[0] is not None})
                    return
                if self.path == "/snapshot.jpg":
                    self._write_snapshot()
                    return
                if self.path == "/stream.mjpg":
                    self._write_stream()
                    return
                self.send_error(404)

            def log_message(self, _format: str, *_args) -> None:
                return

            def _write_html(self) -> None:
                body = b"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    html, body { width: 100%; height: 100%; margin: 0; overflow: hidden; background: #02060b; }
    img { width: 100vw; height: 100vh; object-fit: contain; background: #02060b; }
  </style>
</head>
<body>
  <img src="/stream.mjpg" alt="" />
</body>
</html>
"""
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
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
                jpeg, updated_at = owner._snapshot()
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
                while True:
                    jpeg, updated_at = owner._wait_for_frame()
                    if jpeg is None:
                        continue
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


def format_floor_stay_debug_line(diagnostic: dict) -> str:
    return "floor_stay_debug " + json.dumps(diagnostic, sort_keys=True)


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def run_post_event_agent_dry_run(
    *,
    store,
    event_id: str,
    gemma_base_url: str,
    gemma_model: str,
    allowed_contact_id: str,
    allowlist_config: str,
) -> dict:
    from caresight.runtime.agent_assist import (
        GemmaLocalProvider,
        build_agent_draft,
        contact_ids,
        load_contact_allowlist,
        run_hermes_dry_run,
        stage_action_request,
    )

    update_obs_overlay(event_id)
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
    live_message: str,
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
    tts_after_facetime_delay_seconds: float,
    post_facetime_hold_seconds: float,
) -> dict:
    from caresight.runtime.agent_assist import execute_facetime_if_yes, execute_live_imessage, wait_for_yes_reply

    receipt = run_post_event_agent_dry_run(
        store=store,
        event_id=event_id,
        gemma_base_url=gemma_base_url,
        gemma_model=gemma_model,
        allowed_contact_id=allowed_contact_id,
        allowlist_config=allowlist_config,
    )
    reply_watch_started_at = time.time()
    live_attempt = execute_live_imessage(
        store,
        request_id=receipt["request_id"],
        message=live_message,
        contact_id=allowed_contact_id,
        allowlist_config=allowlist_config,
        target=live_imessage_target,
        live_approved=live_approved,
    )
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
            event = store.get_event(event_id)
            snapshot_path = event.get("evidence", {}).get("snapshot_path")
            escalation_attempt = execute_live_imessage(
                store,
                request_id=receipt["request_id"],
                message=no_response_escalation_message,
                contact_id=allowed_contact_id,
                allowlist_config=allowlist_config,
                target=live_imessage_target,
                attachment_path=snapshot_path,
                result_name="imessage_no_response_escalation_sent",
                live_approved=live_approved,
            )
            live_receipt["no_response_escalation"] = {
                "attempt_id": escalation_attempt["attempt_id"],
                "result": escalation_attempt["result"],
                "external_action_performed": escalation_attempt["external_action_performed"],
                "attachment_included": bool(snapshot_path),
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
                    live_receipt["facetime_next_step"] = "no yes-like reply observed after escalation timeout"
                    return live_receipt
            else:
                live_receipt["facetime_next_step"] = "no yes-like reply observed before escalation timeout"
                return live_receipt
        else:
            live_receipt["facetime_next_step"] = "no yes-like reply observed before timeout"
            return live_receipt
    if not reply.get("reply_interpreted_as_yes"):
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
    live_receipt["facetime_attempt_id"] = facetime_attempt["attempt_id"]
    live_receipt["facetime_started"] = facetime_attempt["external_action_performed"]
    live_receipt["facetime_result"] = facetime_attempt["result"]
    if facetime_attempt["external_action_performed"] and tts_after_facetime_delay_seconds > 0:
        time.sleep(tts_after_facetime_delay_seconds)
    if play_tts_after_facetime:
        live_receipt["tts_playback"] = play_tts(tts_text, voice=tts_voice, audio_route=tts_audio_route, volume=tts_volume)
    if facetime_attempt["external_action_performed"] and post_facetime_hold_seconds > 0:
        time.sleep(post_facetime_hold_seconds)
        live_receipt["post_facetime_hold_seconds"] = post_facetime_hold_seconds
    return live_receipt


def _resolve_live_target_for_channel(contact_id: str, allowlist_config: str, channel: str) -> str:
    from caresight.runtime.agent_assist.live_handoff import resolve_contact_target

    target, _source = resolve_contact_target(
        contact_id=contact_id,
        channel=channel,
        allowlist_config=allowlist_config,
    )
    return target


def play_tts(text: str, *, voice: str, audio_route: str = "system", volume: float = 2.5) -> dict:
    import subprocess

    tts_command = [
        sys.executable,
        str(ROOT_DIR / "scripts" / "caresight_tts.py"),
        "--voice",
        voice,
        "--text",
        text,
        "--play-volume",
        str(volume),
        "--play",
    ]
    command = tts_command
    if audio_route == "blackhole":
        command = [
            sys.executable,
            str(ROOT_DIR / "scripts" / "caresight_audio_route.py"),
            "run-with-blackhole",
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
        "stdout": result.stdout.strip()[-500:],
        "stderr": result.stderr.strip()[-500:],
    }


def update_obs_overlay(event_id: str) -> None:
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
        site_name="Maple Residence",
        site_mode="Observation Mode",
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
    result,
    config,
    fps_values: deque[float],
    preview_path: Path,
    last_write_at: float,
    preview_fps: float,
) -> float:
    if preview_fps <= 0:
        return last_write_at
    now = time.monotonic()
    if last_write_at and now - last_write_at < 1.0 / preview_fps:
        return last_write_at
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    annotated = draw_frame(cv2, frame, result, config, fps_values)
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


def main() -> None:
    args = parse_args()

    import cv2
    from yolo26mlx import YOLO

    from caresight.events.floor_stay import FloorStayDetector
    from caresight.events.snapshots import attach_local_snapshot
    from caresight.runtime.cameras import camera_source_for_opencv, select_configured_camera
    from caresight.runtime.config import CareSightConfig
    from caresight.storage.sqlite_store import SQLiteStore

    config = select_configured_camera(
        CareSightConfig.load(args.config),
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
    capture_source = camera_source_for_opencv(config.camera)
    if config.camera.source_type == "rtsp":
        cap = cv2.VideoCapture(capture_source)
    else:
        cap = cv2.VideoCapture(capture_source, cv2.CAP_AVFOUNDATION)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.camera.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.camera.height)
    cap.set(cv2.CAP_PROP_FPS, config.camera.fps)
    if not cap.isOpened():
        raise SystemExit(f"Could not open camera {config.camera.source_uri}")

    detector = FloorStayDetector(config)
    fps_values: deque[float] = deque(maxlen=30)
    print(format_started_line(config, database_path))
    mjpeg_server = None
    if args.obs_browser_feed:
        mjpeg_server = MjpegPreviewServer(host=args.obs_browser_feed_host, port=args.obs_browser_feed_port)
        mjpeg_server.start()
        print(
            "obs_browser_feed_started "
            + json.dumps({"url": mjpeg_server.url, "stream_url": f"http://{args.obs_browser_feed_host}:{args.obs_browser_feed_port}/stream.mjpg"}, sort_keys=True)
        )

    if not args.no_window:
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(WINDOW_NAME, config.camera.width, config.camera.height)

    loop_started_at = time.monotonic()
    check_started_at = utc_now()
    frame_count = 0
    persisted_event_count = 0
    obs_preview_path = resolve_runtime_path(args.obs_live_preview_path)
    last_obs_preview_write_at = 0.0
    last_floor_debug_at = 0.0
    try:
        while True:
            started_at = time.perf_counter()
            ok, frame = cap.read()
            if not ok:
                break
            frame_count += 1

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = model.predict(rgb_frame, conf=args.conf)[0]
            height, width = frame.shape[:2]
            event = detector.update(result_to_detections(result, width, height))
            if args.debug_floor_stay and time.monotonic() - last_floor_debug_at >= 1.0:
                print(format_floor_stay_debug_line(detector.diagnostic()))
                last_floor_debug_at = time.monotonic()

            annotated_frame = None
            if args.obs_browser_feed or args.obs_live_preview or not args.no_window:
                annotated_frame = draw_frame(cv2, frame, result, config, fps_values)
            if mjpeg_server is not None and annotated_frame is not None:
                mjpeg_server.update(cv2, annotated_frame)
            if args.obs_live_preview:
                last_obs_preview_write_at = maybe_write_obs_preview(
                    cv2=cv2,
                    frame=frame,
                    result=result,
                    config=config,
                    fps_values=fps_values,
                    preview_path=obs_preview_path,
                    last_write_at=last_obs_preview_write_at,
                    preview_fps=args.obs_live_preview_fps,
                )
            event_persisted = False
            if event is not None:
                snapshot_dir = database_path.parent / "snapshots"
                event = attach_local_snapshot(
                    event=event,
                    snapshot_dir=snapshot_dir,
                    write_snapshot=lambda path: cv2.imwrite(str(path), frame),
                )
                store.insert_event(event)
                print("event_persisted " + json.dumps(event, sort_keys=True))
                event_persisted = True
                persisted_event_count += 1
                if args.auto_agent_live_run:
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
                            tts_after_facetime_delay_seconds=args.tts_after_facetime_delay_seconds,
                            post_facetime_hold_seconds=args.post_facetime_hold_seconds,
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

            if not args.no_window and annotated_frame is not None:
                cv2.imshow(WINDOW_NAME, annotated_frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        if mjpeg_server is not None:
            mjpeg_server.stop()

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
