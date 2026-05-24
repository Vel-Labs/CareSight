from __future__ import annotations

import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import secrets


class MjpegPreviewServer:
    def __init__(self, host: str, port: int, token: str | None = None):
        self.host = host
        self.port = port
        self.token = token
        self._latest_jpeg: bytes | None = None
        self._lock = threading.Lock()
        self._server = ThreadingHTTPServer((host, port), self._handler())
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2.0)

    def update(self, jpeg_bytes: bytes) -> None:
        with self._lock:
            self._latest_jpeg = bytes(jpeg_bytes)

    def _handler(self):
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, _format: str, *_args: object) -> None:
                return

            def do_GET(self) -> None:
                if not self._authorized():
                    self.send_error(401)
                    return
                route = self.path.split("?", 1)[0]
                if route in {"/", "/live.html"}:
                    stream_src = "/stream.mjpg"
                    if outer.token is not None and "token=" in self.path:
                        stream_src += "?token=" + self.path.split("token=", 1)[1].split("&", 1)[0]
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(
                        (
                            "<html><body style='margin:0;background:#050708'>"
                            f"<img src='{stream_src}' style='width:100vw;height:100vh;object-fit:contain'/>"
                            "</body></html>"
                        ).encode("utf-8")
                    )
                    return
                if route != "/stream.mjpg":
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
                self.end_headers()
                while True:
                    with outer._lock:
                        frame = outer._latest_jpeg
                    if frame is not None:
                        self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
                    time.sleep(0.1)

            def _authorized(self) -> bool:
                if outer.token is None:
                    return True
                header = self.headers.get("Authorization", "")
                if header.startswith("Bearer ") and secrets.compare_digest(header.removeprefix("Bearer ").strip(), outer.token):
                    return True
                if "token=" in self.path:
                    supplied = self.path.split("token=", 1)[1].split("&", 1)[0]
                    return secrets.compare_digest(supplied, outer.token)
                return False

        return Handler
