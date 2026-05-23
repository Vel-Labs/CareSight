#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
DEFAULT_DB_PATH = ROOT_DIR / "data" / "caresight-v0.sqlite3"
DEFAULT_ALLOWLIST_PATH = ROOT_DIR / "config" / "hermes" / "allowlisted-contacts.example.json"


def parse_args() -> argparse.Namespace:
    from caresight.runtime.agent_assist import DEFAULT_LIVE_MESSAGE

    parser = argparse.ArgumentParser(description="Execute explicit CareSight local live handoff actions.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="CareSight SQLite database.")
    parser.add_argument(
        "--allowlist-config",
        default=os.environ.get("CARESIGHT_CONTACT_ALLOWLIST_PATH", str(DEFAULT_ALLOWLIST_PATH)),
        help="Redacted public or ignored private contact allowlist JSON.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    send_parser = subparsers.add_parser("send-imessage", help="Send the approved CareSight iMessage.")
    send_parser.add_argument("request_id")
    send_parser.add_argument("--contact-id", default="contact_emergency_primary")
    send_parser.add_argument("--target", help="Private iMessage handle. Prefer CARESIGHT_LIVE_IMESSAGE_TARGET.")
    send_parser.add_argument("--message", default=DEFAULT_LIVE_MESSAGE)
    send_parser.add_argument("--live-approved", action="store_true")
    send_parser.add_argument("--dry-run", action="store_true")

    face_parser = subparsers.add_parser(
        "facetime-if-yes",
        help="Open FaceTime only if the provided reply text is yes-like.",
    )
    face_parser.add_argument("request_id")
    face_parser.add_argument("--reply-text", required=True)
    face_parser.add_argument("--contact-id", default="contact_emergency_primary")
    face_parser.add_argument("--target", help="Private FaceTime handle. Prefer CARESIGHT_LIVE_FACETIME_TARGET.")
    face_parser.add_argument("--live-approved", action="store_true")
    face_parser.add_argument("--dry-run", action="store_true")

    demo_parser = subparsers.add_parser(
        "wait-reply-facetime-tts",
        help="Wait for a yes-like iMessage reply, open FaceTime, then play approved Dakota TTS.",
    )
    demo_parser.add_argument("request_id")
    demo_parser.add_argument("--contact-id", default="contact_emergency_primary")
    demo_parser.add_argument("--target", help="Private Messages/FaceTime handle. Prefer CARESIGHT_LIVE_CONTACT_TARGET.")
    demo_parser.add_argument("--since-unix-seconds", type=float, required=True)
    demo_parser.add_argument("--timeout-seconds", type=float, default=180.0)
    demo_parser.add_argument("--poll-interval-seconds", type=float, default=2.0)
    demo_parser.add_argument(
        "--tts-text",
        default=(
            "This is an automated CareSight message. A possible floor stay was observed in the Living Room. "
            "Please review the live feed. CareSight will keep this handoff open briefly for review."
        ),
    )
    demo_parser.add_argument("--tts-voice", default="dakota")
    demo_parser.add_argument("--tts-audio-route", choices=["system", "blackhole"], default="system")
    demo_parser.add_argument("--tts-volume", type=float, default=6.0)
    demo_parser.add_argument("--tts-repeat-count", type=int, default=2)
    demo_parser.add_argument("--tts-repeat-delay-seconds", type=float, default=1.5)
    demo_parser.add_argument("--tts-after-facetime-delay-seconds", type=float, default=16.0)
    demo_parser.add_argument("--post-facetime-hold-seconds", type=float, default=30.0)
    demo_parser.add_argument("--live-approved", action="store_true")
    demo_parser.add_argument("--dry-run", action="store_true")

    reply_parser = subparsers.add_parser("interpret-reply", help="Classify whether reply text is yes-like.")
    reply_parser.add_argument("--reply-text", required=True)
    return parser.parse_args()


def main() -> None:
    from caresight.runtime.agent_assist import (
        execute_facetime_if_yes,
        execute_live_imessage,
        is_yes_like_reply,
        wait_for_yes_reply,
    )
    from caresight.storage.sqlite_store import SQLiteStore

    args = parse_args()
    if args.command == "interpret-reply":
        print(json.dumps({"reply_interpreted_as_yes": is_yes_like_reply(args.reply_text)}, sort_keys=True))
        return

    store = SQLiteStore(args.db)
    store.initialize()
    if args.command == "send-imessage":
        attempt = execute_live_imessage(
            store,
            request_id=args.request_id,
            message=args.message,
            contact_id=args.contact_id,
            allowlist_config=args.allowlist_config,
            target=args.target,
            live_approved=args.live_approved,
            dry_run=args.dry_run,
        )
        print(json.dumps(attempt, indent=2, sort_keys=True))
        return

    if args.command == "facetime-if-yes":
        attempt = execute_facetime_if_yes(
            store,
            request_id=args.request_id,
            reply_text=args.reply_text,
            contact_id=args.contact_id,
            allowlist_config=args.allowlist_config,
            target=args.target,
            live_approved=args.live_approved,
            dry_run=args.dry_run,
        )
        print(json.dumps(attempt, indent=2, sort_keys=True))
        return

    if args.command == "wait-reply-facetime-tts":
        target = args.target or os.environ.get("CARESIGHT_LIVE_FACETIME_TARGET") or os.environ.get(
            "CARESIGHT_LIVE_CONTACT_TARGET"
        )
        if not target:
            raise SystemExit(
                "missing live target; set CARESIGHT_LIVE_FACETIME_TARGET or pass --target for this local test"
            )
        reply = wait_for_yes_reply(
            target=target,
            since_unix_seconds=args.since_unix_seconds,
            timeout_seconds=args.timeout_seconds,
            poll_interval_seconds=args.poll_interval_seconds,
        )
        print("reply_watch " + json.dumps(reply, sort_keys=True), flush=True)
        if not reply.get("reply_interpreted_as_yes"):
            return
        attempt = execute_facetime_if_yes(
            store,
            request_id=args.request_id,
            reply_text=str(reply.get("reply_text") or ""),
            contact_id=args.contact_id,
            allowlist_config=args.allowlist_config,
            target=target,
            live_approved=args.live_approved,
            dry_run=args.dry_run,
        )
        print("facetime_handoff " + json.dumps(attempt, sort_keys=True), flush=True)
        if args.dry_run:
            return
        if args.tts_after_facetime_delay_seconds > 0:
            __import__("time").sleep(args.tts_after_facetime_delay_seconds)
        tts_command = [
            sys.executable,
            str(ROOT_DIR / "scripts" / "caresight_tts.py"),
            "--voice",
            args.tts_voice,
            "--text",
            args.tts_text,
            "--play-volume",
            str(args.tts_volume),
            "--play-repeat-count",
            str(max(1, args.tts_repeat_count)),
            "--play-repeat-delay-seconds",
            str(args.tts_repeat_delay_seconds),
            "--play",
        ]
        if args.tts_audio_route == "blackhole":
            tts_command = [
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
        result = __import__("subprocess").run(tts_command, cwd=ROOT_DIR.parents[1], text=True)
        if result.returncode != 0:
            raise SystemExit(result.returncode)
        if args.post_facetime_hold_seconds > 0:
            print(
                "post_facetime_hold "
                + json.dumps({"seconds": args.post_facetime_hold_seconds, "status": "holding"}, sort_keys=True),
                flush=True,
            )
            __import__("time").sleep(args.post_facetime_hold_seconds)
        return


if __name__ == "__main__":
    main()
