import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "v0_floor_stay_live.py"
spec = importlib.util.spec_from_file_location("v0_floor_stay_live", SCRIPT)
assert spec is not None
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class V0FloorStayLiveTest(unittest.TestCase):
    def test_help_does_not_require_live_runtime_imports(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True,
            check=False,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--stop-after-event", result.stdout)
        self.assertIn("--max-seconds", result.stdout)
        self.assertIn("--camera-id", result.stdout)
        self.assertIn("--source-type", result.stdout)

    def test_stop_after_event_when_event_persisted(self) -> None:
        self.assertTrue(
            module.should_stop_loop(
                started_at=10.0,
                now=11.0,
                max_seconds=None,
                event_persisted=True,
                stop_after_event=True,
            )
        )

    def test_max_seconds_stops_loop(self) -> None:
        self.assertTrue(
            module.should_stop_loop(
                started_at=10.0,
                now=20.1,
                max_seconds=10.0,
                event_persisted=False,
                stop_after_event=False,
            )
        )

    def test_continues_when_no_stop_condition_is_met(self) -> None:
        self.assertFalse(
            module.should_stop_loop(
                started_at=10.0,
                now=11.0,
                max_seconds=10.0,
                event_persisted=False,
                stop_after_event=True,
            )
        )


if __name__ == "__main__":
    unittest.main()
