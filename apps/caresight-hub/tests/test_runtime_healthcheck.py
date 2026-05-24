import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from caresight.runtime.healthcheck import healthcheck
from caresight.runtime.model_doctor import check_model_manifest, sha256_path

from importlib import util

ROOT_DIR = Path(__file__).resolve().parents[1]
PREFLIGHT_SCRIPT = ROOT_DIR / "scripts" / "caresight_demo_preflight.py"
preflight_spec = util.spec_from_file_location("caresight_demo_preflight", PREFLIGHT_SCRIPT)
assert preflight_spec is not None
preflight_module = util.module_from_spec(preflight_spec)
assert preflight_spec.loader is not None
preflight_spec.loader.exec_module(preflight_module)


class RuntimeHealthcheckTest(unittest.TestCase):
    def test_healthcheck_reports_ready(self) -> None:
        self.assertEqual(healthcheck(), "caresight-runtime-ready")

    def test_heartbeat_receipt_never_performs_live_actions(self) -> None:
        payload = {
            "mode": "heartbeat",
            "ready": True,
            "checks": [
                {"name": "gemma_endpoint", "ok": False, "required": False, "detail": "not ready"},
                {"name": "contact_allowlist", "ok": True, "required": True, "detail": "present"},
            ],
        }

        receipt = preflight_module.build_preflight_receipt(payload, started_at="2026-05-24T12:00:00Z")

        self.assertEqual(receipt["schema"], "runtime-validation-receipt")
        self.assertEqual(receipt["check_type"], "heartbeat")
        self.assertEqual(receipt["status"], "warn")
        self.assertFalse(receipt["result"]["live_actions_performed"])
        self.assertIn("no_live_send", receipt["safety_boundaries"])
        self.assertIn("no_facetime_call", receipt["safety_boundaries"])
        self.assertIn("no_tts_playback", receipt["safety_boundaries"])

    def test_blocked_runtime_dependency_produces_blocked_receipt(self) -> None:
        payload = {
            "mode": "heartbeat",
            "ready": False,
            "checks": [
                {"name": "contact_allowlist", "ok": False, "required": True, "detail": "missing"},
            ],
        }

        receipt = preflight_module.build_preflight_receipt(payload, started_at="2026-05-24T12:00:00Z")

        self.assertEqual(receipt["status"], "blocked")
        self.assertEqual(receipt["blockers"][0]["code"], "contact_allowlist")

    def test_model_doctor_valid_manifest_passes(self) -> None:
        with TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "model.bin"
            model_path.write_bytes(b"care")
            manifest = _manifest_for(model_path, sha256_path(model_path), model_path.stat().st_size)

            result = check_model_manifest(manifest)

            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["blockers"], [])

    def test_model_doctor_checksum_mismatch_fails(self) -> None:
        with TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "model.bin"
            model_path.write_bytes(b"care")
            manifest = _manifest_for(model_path, "0" * 64, model_path.stat().st_size)

            result = check_model_manifest(manifest)

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["blockers"][0]["code"], "checksum_mismatch")

    def test_model_doctor_missing_manifest_fails(self) -> None:
        result = check_model_manifest({"model_id": "model_incomplete"})

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["blockers"][0]["code"], "missing_manifest_field")


def _manifest_for(path: Path, sha256: str, size: int) -> dict[str, object]:
    return {
        "model_id": "model_test",
        "purpose_lane": "vision",
        "source_url": "https://example.invalid/model",
        "license": "test",
        "local_path": str(path),
        "sha256": sha256,
        "expected_size_bytes": size,
        "runtime": "local_python",
        "allowed_uses": ["local test"],
        "blocked_uses": ["medical_diagnosis"],
        "validation_command": "python --version",
        "last_validated_at": None,
    }


if __name__ == "__main__":
    unittest.main()
