import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "open_demo_terminals.sh"


class DemoTerminalLauncherTest(unittest.TestCase):
    def test_print_mode_lists_two_camera_detector_tabs_with_missing_events(self) -> None:
        result = subprocess.run(
            ["bash", str(SCRIPT), "--print"],
            cwd=ROOT,
            capture_output=True,
            check=False,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Open six terminal tabs", result.stdout)
        self.assertIn("### Terminal 4 - Living Room Detector", result.stdout)
        self.assertIn("### Terminal 5 - Kitchen Detector", result.stdout)
        self.assertIn("### Terminal 6 - CareSight Status Board", result.stdout)
        self.assertIn("--camera-id tapo_living_room", result.stdout)
        self.assertIn("--camera-id tapo_kitchen", result.stdout)
        self.assertEqual(result.stdout.count("--missing-off-camera-events"), 2)
        self.assertIn("cleanup_detector \"tapo_living_room\" \"8766\"", result.stdout)
        self.assertIn("cleanup_detector \"tapo_kitchen\" \"8767\"", result.stdout)
        self.assertIn("Stopping CareSight process on port $port pid $pid", result.stdout)
        self.assertEqual(result.stdout.count("--auto-agent-live-run"), 1)
        self.assertEqual(result.stdout.count("--auto-facetime-on-reply"), 1)
        self.assertIn("--live-approved", result.stdout)
        living_section = result.stdout.split("### Terminal 4 - Living Room Detector", 1)[1].split("### Terminal 5", 1)[0]
        kitchen_section = result.stdout.split("### Terminal 5 - Kitchen Detector", 1)[1].split("### Terminal 6", 1)[0]
        self.assertIn("--auto-agent-live-run", living_section)
        self.assertIn("Starting Living Room detector.", living_section)
        self.assertNotIn("Press Enter to start Living Room detector", living_section)
        self.assertIn("CARESIGHT_AITUM_VERTICAL_MODE=off", living_section)
        self.assertIn('CARESIGHT_OBS_FACETIME_SCENE=""', living_section)
        self.assertIn('CARESIGHT_OBS_FACETIME_VIDEO_MODE=""', living_section)
        self.assertIn("--tts-audio-route blackhole", living_section)
        self.assertNotIn("--auto-agent-live-run", kitchen_section)
        self.assertNotIn("--auto-facetime-on-reply", kitchen_section)
        self.assertIn("Starting Kitchen detector.", kitchen_section)
        self.assertNotIn("Press Enter to start Kitchen detector", kitchen_section)


if __name__ == "__main__":
    unittest.main()
