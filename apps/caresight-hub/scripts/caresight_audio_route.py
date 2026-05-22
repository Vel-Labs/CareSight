#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from typing import Any


BLACKHOLE_DEVICE = "BlackHole 2ch"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check and temporarily route CareSight demo audio.")
    subparsers = parser.add_subparsers(dest="action", required=True)
    subparsers.add_parser("check", help="Check BlackHole and switchaudio-osx availability.")
    subparsers.add_parser("install-plan", help="Print install commands for optional audio routing tools.")
    route_parser = subparsers.add_parser("run-with-blackhole", help="Run a command with system input/output set to BlackHole.")
    route_parser.add_argument(
        "--hold-after-seconds",
        type=float,
        default=1.5,
        help="Keep BlackHole selected briefly after playback before restoring devices.",
    )
    route_parser.add_argument("route_command", nargs=argparse.REMAINDER)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.action == "check":
        print(json.dumps(audio_route_status(), indent=2, sort_keys=True))
        return 0
    if args.action == "install-plan":
        print(
            "\n".join(
                [
                    "brew install steipete/tap/imsg",
                    "brew install switchaudio-osx",
                    "brew install --cask blackhole-2ch",
                    "# Reboot after BlackHole install, then re-run:",
                    "python3 apps/caresight-hub/scripts/caresight_audio_route.py check",
                ]
            )
        )
        return 0
    if args.action == "run-with-blackhole":
        if not args.route_command:
            print("audio_route_failed missing command", file=sys.stderr)
            return 2
        command = args.route_command[1:] if args.route_command[0] == "--" else args.route_command
        return run_with_blackhole(command, hold_after_seconds=args.hold_after_seconds)
    return 2


def audio_route_status() -> dict[str, Any]:
    switchaudio = shutil.which("SwitchAudioSource")
    devices = list_audio_devices() if switchaudio else {"input": [], "output": [], "system": []}
    return {
        "schema": "caresight-audio-route-status",
        "switchaudio_available": switchaudio is not None,
        "switchaudio_path": switchaudio,
        "blackhole_device": BLACKHOLE_DEVICE,
        "blackhole_input_available": BLACKHOLE_DEVICE in devices["input"],
        "blackhole_output_available": BLACKHOLE_DEVICE in devices["output"],
        "current_input": current_device("input") if switchaudio else None,
        "current_output": current_device("output") if switchaudio else None,
        "current_system": current_device("system") if switchaudio else None,
        "devices": devices,
        "install_commands": [
            "brew install steipete/tap/imsg",
            "brew install switchaudio-osx",
            "brew install --cask blackhole-2ch",
        ],
        "notes": [
            "BlackHole install requires a reboot before the audio device appears.",
            "This script can temporarily switch default input/output during TTS playback, then restore them.",
        ],
    }


def run_with_blackhole(command: list[str], *, hold_after_seconds: float = 1.5) -> int:
    status = audio_route_status()
    if not status["switchaudio_available"]:
        print("audio_route_failed switchaudio_missing; run install-plan", file=sys.stderr)
        return 2
    if not status["blackhole_input_available"] or not status["blackhole_output_available"]:
        print("audio_route_failed blackhole_2ch_missing_or_needs_reboot", file=sys.stderr)
        return 2

    previous_input = status["current_input"]
    previous_output = status["current_output"]
    try:
        set_device("input", BLACKHOLE_DEVICE)
        set_device("output", BLACKHOLE_DEVICE)
        returncode = subprocess.run(command, check=False).returncode
        if hold_after_seconds > 0:
            __import__("time").sleep(hold_after_seconds)
        return returncode
    finally:
        if previous_input:
            set_device("input", previous_input)
        if previous_output:
            set_device("output", previous_output)


def list_audio_devices() -> dict[str, list[str]]:
    return {
        "input": _switchaudio_lines(["-a", "-t", "input"]),
        "output": _switchaudio_lines(["-a", "-t", "output"]),
        "system": _switchaudio_lines(["-a", "-t", "system"]),
    }


def current_device(kind: str) -> str:
    return _switchaudio_text(["-c", "-t", kind])


def set_device(kind: str, name: str) -> None:
    subprocess.run(["SwitchAudioSource", "-t", kind, "-s", name], check=True)


def _switchaudio_lines(args: list[str]) -> list[str]:
    text = _switchaudio_text(args)
    return [line.strip() for line in text.splitlines() if line.strip()]


def _switchaudio_text(args: list[str]) -> str:
    result = subprocess.run(["SwitchAudioSource", *args], capture_output=True, check=False, text=True)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


if __name__ == "__main__":
    raise SystemExit(main())
