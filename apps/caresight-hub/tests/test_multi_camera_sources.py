import unittest
import importlib.util
import json
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from pathlib import Path

from caresight.runtime.cameras import camera_source_for_opencv
from caresight.runtime.cameras.multi_camera import (
    CameraHealth,
    MultiCameraFrameManager,
    UnsupportedCameraSource,
)
from caresight.runtime.config import CameraConfig, CareSightConfig


class MultiCameraSourcesTest(unittest.TestCase):
    def test_supported_explicit_camera_sources_validate(self) -> None:
        for source_type, source_uri, expected in [
            ("webcam", 0, 0),
            ("usb", "1", 1),
            ("continuity_camera", 2, 2),
            ("rtsp", "rtsp://192.0.2.55/stream1", "rtsp://192.0.2.55/stream1"),
        ]:
            camera = CameraConfig(
                camera_id=f"{source_type}_camera",
                name=f"{source_type} camera",
                source_type=source_type,
                source_uri=source_uri,
                width=1280,
                height=720,
                fps=15,
                room_id="test_room",
                room_label="Test Room",
                privacy={
                    "raw_video_storage": "local_only",
                    "cloud_upload_default": False,
                },
            )

            self.assertEqual(camera.privacy.raw_video_storage, "local_only")
            self.assertFalse(camera.privacy.cloud_upload_default)
            self.assertEqual(camera_source_for_opencv(camera), expected)

    def test_rejects_cloud_provider_discovery_and_credential_bearing_sources(self) -> None:
        blocked = [
            ("ring", "rtsp://192.0.2.10/stream1"),
            ("nest", "rtsp://192.0.2.10/stream1"),
            ("arlo", "rtsp://192.0.2.10/stream1"),
            ("wyze_cloud", "rtsp://192.0.2.10/stream1"),
            ("home_assistant_cloud", "rtsp://192.0.2.10/stream1"),
            ("onvif_discovery", "rtsp://192.0.2.10/stream1"),
            ("lan_scan", "rtsp://192.0.2.10/stream1"),
            ("rtsp", "rtsp://user:secret@192.0.2.10/stream1"),
        ]

        for source_type, source_uri in blocked:
            with self.subTest(source_type=source_type):
                with self.assertRaises(ValueError):
                    CameraConfig(
                        camera_id=f"{source_type}_camera",
                        name=f"{source_type} camera",
                        source_type=source_type,
                        source_uri=source_uri,
                        width=1280,
                        height=720,
                        fps=15,
                    )

    def test_allows_credential_bearing_rtsp_only_when_local_flag_is_explicit(self) -> None:
        camera = CameraConfig(
            camera_id="tapo_living_room",
            name="Tapo Living Room",
            source_type="rtsp",
            source_uri="rtsp://user:secret@10.0.0.20:554/stream1",
            width=1920,
            height=1080,
            fps=15,
            room_id="living_room",
            room_label="Living Room",
            allow_embedded_credentials=True,
            privacy={
                "raw_video_storage": "local_only",
                "cloud_upload_default": False,
            },
        )

        self.assertEqual(camera_source_for_opencv(camera), "rtsp://user:secret@10.0.0.20:554/stream1")

    def test_round_robin_manager_returns_camera_metadata_and_health(self) -> None:
        config = CareSightConfig.from_dict(
            {
                **CareSightConfig.default().to_dict(),
                "cameras": [
                    {
                        **CareSightConfig.default().camera.__dict__,
                        "camera_id": "living_room",
                        "room_id": "living_room",
                        "room_label": "Living Room",
                    },
                    {
                        **CareSightConfig.default().camera.__dict__,
                        "camera_id": "kitchen",
                        "source_uri": 1,
                        "room_id": "kitchen",
                        "room_label": "Kitchen",
                    },
                ],
            }
        )
        manager = MultiCameraFrameManager(
            config.cameras,
            opener=lambda camera: StaticSource(camera.camera_id),
            now=lambda: "2026-05-23T08:00:00Z",
        )

        first = manager.read_next()
        second = manager.read_next()

        self.assertEqual(first.camera_id, "living_room")
        self.assertEqual(first.room_id, "living_room")
        self.assertEqual(second.camera_id, "kitchen")
        self.assertEqual(second.room_label, "Kitchen")
        self.assertEqual(manager.health()["living_room"].status, "ok")

    def test_failed_source_creates_health_blocker_not_frame(self) -> None:
        camera = CareSightConfig.default().camera
        manager = MultiCameraFrameManager(
            (camera,),
            opener=lambda _camera: FailingSource(),
            now=lambda: "2026-05-23T08:00:00Z",
        )

        frame = manager.read_next()
        health = manager.health()[camera.camera_id]

        self.assertIsNone(frame)
        self.assertIsInstance(health, CameraHealth)
        self.assertEqual(health.status, "open_failure")
        self.assertEqual(health.blocker, "camera_source_unavailable")

    def test_unsupported_source_type_is_health_blocker(self) -> None:
        camera = object.__new__(CameraConfig)
        object.__setattr__(camera, "camera_id", "bad")
        object.__setattr__(camera, "name", "Bad Camera")
        object.__setattr__(camera, "source_type", "ring")
        object.__setattr__(camera, "source_uri", "cloud")
        object.__setattr__(camera, "width", 1280)
        object.__setattr__(camera, "height", 720)
        object.__setattr__(camera, "fps", 15)
        object.__setattr__(camera, "room_id", "bad_room")
        object.__setattr__(camera, "room_label", "Bad Room")
        object.__setattr__(camera, "privacy", None)

        with self.assertRaises(UnsupportedCameraSource):
            MultiCameraFrameManager((camera,))

    def test_camera_probe_dry_run_redacts_rtsp_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "camera.local.json"
            config_path.write_text(
                json.dumps(
                    {
                        "camera": {
                            "camera_id": "tapo_living_room",
                            "name": "Tapo Living Room",
                            "source_type": "rtsp",
                            "source_uri": "rtsp://care:secret@192.0.2.55:554/stream1",
                            "width": 1280,
                            "height": 720,
                            "fps": 15,
                            "room_id": "living_room",
                            "room_label": "Living Room",
                        }
                    }
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "apps/caresight-hub/scripts/caresight_camera_probe.py",
                    "--config",
                    str(config_path),
                    "--dry-run",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)
            probe = payload["result"]

            self.assertEqual(payload["schema"], "runtime-validation-receipt")
            self.assertEqual(probe["camera_id"], "tapo_living_room")
            self.assertEqual(probe["redacted_uri"], "rtsp://***:***@192.0.2.55:554/stream1")
            self.assertNotIn("secret", result.stdout)
            self.assertEqual(probe["stream_opened"], "not_attempted")

    def test_camera_probe_reports_missing_cv2_next_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "camera.local.json"
            config_path.write_text(
                json.dumps(
                    {
                        "camera": {
                            "camera_id": "tapo_living_room",
                            "source_type": "rtsp",
                            "source_uri": "rtsp://care:secret@192.0.2.55:554/stream1",
                            "room_id": "living_room",
                            "room_label": "Living Room",
                        }
                    }
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "apps/caresight-hub/scripts/caresight_camera_probe.py",
                    "--config",
                    str(config_path),
                    "--timeout-seconds",
                    "0.01",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)
            probe = payload["result"]

            if probe["blocker"] == "missing_cv2":
                self.assertIn("vendor/yolo-mlx/.venv/bin/python", probe["next_command"])
                self.assertNotIn("secret", result.stdout)

    def test_camera_view_reports_missing_cv2_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "camera.local.json"
            config_path.write_text(
                json.dumps(
                    {
                        "camera": {
                            "camera_id": "tapo_living_room",
                            "source_type": "rtsp",
                            "source_uri": "rtsp://care:secret@192.0.2.55:554/stream1",
                        }
                    }
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "apps/caresight-hub/scripts/caresight_camera_view.py",
                    "--config",
                    str(config_path),
                    "--max-seconds",
                    "0.01",
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                self.assertIn("vendor/yolo-mlx/.venv/bin/python", result.stderr)
                self.assertNotIn("secret", result.stderr)

    def test_camera_discovery_writes_owner_specified_rtsp_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "tapo.local.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "apps/caresight-hub/scripts/caresight_camera_discover.py",
                    "--host",
                    "192.0.2.55",
                    "--camera-id",
                    "tapo_living_room",
                    "--name",
                    "Tapo Living Room",
                    "--room-id",
                    "living_room",
                    "--room-label",
                    "Living Room",
                    "--skip-reachability",
                    "--write-config",
                    str(config_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)
            written = json.loads(config_path.read_text(encoding="utf-8"))

            self.assertEqual(payload["schema"], "camera-discovery-receipt")
            self.assertFalse(payload["network_scan_performed"])
            self.assertEqual(payload["redacted_uri"], "rtsp://***:***@192.0.2.55:554/stream1")
            self.assertEqual(payload["candidate_kind"], "not_attempted")
            self.assertEqual(written["camera"]["camera_id"], "tapo_living_room")
            self.assertEqual(written["camera"]["source_type"], "rtsp")
            self.assertIn("replace-with-camera-password", written["camera"]["source_uri"])
            self.assertEqual(written["notes"]["rtsp_port_reachable"], "not_attempted")
            self.assertEqual(written["notes"]["candidate_kind"], "not_attempted")

    def test_camera_discovery_classifies_owner_host_service_only(self) -> None:
        module = load_script_module("caresight_camera_discover")
        self.assertEqual(
            module._candidate_kind(rtsp_reachable=False, onvif_reachable=False, open_ports=[443]),
            "service_only",
        )
        self.assertEqual(
            module._candidate_kind(rtsp_reachable=True, onvif_reachable=False, open_ports=[554]),
            "rtsp_ready",
        )

    def test_camera_discovery_requires_explicit_allow_for_lan_scan(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "apps/caresight-hub/scripts/caresight_camera_discover.py",
                "--subnet",
                "192.0.2.0/30",
            ],
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--allow-lan-scan", result.stderr)

    def test_camera_discovery_lan_scan_reports_progress_and_completes(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "apps/caresight-hub/scripts/caresight_camera_discover.py",
                "--subnet",
                "192.0.2.0/30",
                "--allow-lan-scan",
                "--scan-timeout-seconds",
                "0.01",
                "--progress-every",
                "1",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(result.stdout)
        self.assertEqual(payload["mode"], "owner_authorized_lan_scan")
        self.assertEqual(payload["hosts_checked"], 2)
        self.assertTrue(payload["network_scan_performed"])
        self.assertIn("scan_progress", result.stderr)

    def test_camera_discovery_collects_hosts_with_any_camera_candidate_port(self) -> None:
        module = load_script_module("caresight_camera_discover")
        original_scan_host = module._scan_host
        try:
            module._scan_host = lambda hostname, ports, timeout: (
                hostname,
                {"80": True} if hostname == "192.0.2.1" else {},
            )
            payload = module._scan_subnet(
                SimpleNamespace(
                    subnet="192.0.2.0/30",
                    max_hosts=8,
                    scan_workers=2,
                    rtsp_port=554,
                    onvif_port=2020,
                    discovery_ports=[554, 8554, 2020, 80],
                    scan_timeout_seconds=0.01,
                    progress_every=0,
                    include_arp=False,
                )
            )
        finally:
            module._scan_host = original_scan_host

        self.assertEqual(payload["candidate_count"], 1)
        self.assertEqual(payload["candidates"][0]["host"], "192.0.2.1")
        self.assertEqual(payload["candidates"][0]["open_ports"], [80])

    def test_camera_discovery_surfaces_unclassified_arp_hosts(self) -> None:
        module = load_script_module("caresight_camera_discover")
        original_scan_host = module._scan_host
        original_arp_hosts = module._arp_hosts
        original_local_ipv4_addresses = module._local_ipv4_addresses
        try:
            module._scan_host = lambda hostname, ports, timeout: (hostname, {})
            module._arp_hosts = lambda: [{"host": "192.0.2.1", "mac": "00:11:22:33:44:55"}]
            module._local_ipv4_addresses = lambda: {"192.0.2.2"}
            payload = module._scan_subnet(
                SimpleNamespace(
                    subnet="192.0.2.0/30",
                    max_hosts=8,
                    scan_workers=2,
                    rtsp_port=554,
                    onvif_port=2020,
                    discovery_ports=[554, 8554, 2020, 80],
                    scan_timeout_seconds=0.01,
                    progress_every=0,
                    include_arp=True,
                )
            )
        finally:
            module._scan_host = original_scan_host
            module._arp_hosts = original_arp_hosts
            module._local_ipv4_addresses = original_local_ipv4_addresses

        self.assertEqual(payload["candidate_count"], 0)
        self.assertEqual(payload["unclassified_arp_hosts"][0]["host"], "192.0.2.1")
        self.assertIn("--host 192.0.2.1", payload["unclassified_arp_hosts"][0]["suggested_next_command"])


class StaticSource:
    def __init__(self, frame):
        self.frame = frame

    def read(self):
        return True, self.frame

    def release(self):
        return None


class FailingSource:
    def read(self):
        return False, None

    def release(self):
        return None


def load_script_module(name: str):
    path = Path("apps/caresight-hub/scripts") / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    unittest.main()
