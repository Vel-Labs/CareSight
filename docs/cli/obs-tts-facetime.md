# OBS, TTS, and FaceTime Commands

These commands operate presentation and handoff surfaces. OBS and local TTS generation are operator-owned. Live iMessage, FaceTime, reply-watching, and TTS playback require explicit human approval.

## Agent-Safe Read

| Command | Purpose | Validation |
| --- | --- | --- |
| `./scripts/update_obs_overlay.sh --event-id <event_id>` | Refresh local OBS overlay state from SQLite for one event. | `./scripts/update_obs_overlay.sh --sample --dry-run` and unsafe wording rejection. |

## Manual Operator

| Command | Purpose | Boundary |
| --- | --- | --- |
| `python3 apps/caresight-hub/scripts/caresight_contacts_config.py --display-label "Primary emergency contact" --imessage <private-imessage-handle>` | Create ignored local contact allowlist config. | Stores private handles only in ignored local config. |
| `python3 apps/caresight-hub/scripts/caresight_audio_route.py check` | Check optional `imsg`, BlackHole, and SwitchAudioSource readiness. | Does not change audio devices. |
| `python3 apps/caresight-hub/scripts/caresight_tts.py --voice dakota --text "CareSight alert. Possible floor stay observed in the Living Room. Needs review."` | Generate local Holler TTS audio without playback. | Playback is not part of default validation. |
| `./scripts/setup_obs_scene.sh --dry-run` | Create or inspect local CareSight OBS scenes. | Live OBS setup requires operator scene/privacy confirmation. |
| `./scripts/install_obs_vertical_canvas.sh` | Download optional Aitum Vertical Canvas installer into ignored vendor storage. | Install/restart OBS manually. |
| `apps/obs-hub/tools/aitum_vertical.py status` | Inspect Aitum vertical canvas state. | No message/call/playback action. |
| `apps/obs-hub/tools/aitum_vertical.py switch --scene "CareSight Hub - FaceTime Mobile Vertical" --start-virtual-camera` | Switch vertical canvas and start Aitum virtual camera. | Operator-approved FaceTime handoff path only. |
| `apps/obs-hub/tools/normalize_aitum_vertical_scene.py` | Reset Aitum FaceTime scene geometry. | No live caregiver action. |
| `./scripts/update_obs_overlay.sh --watch` | Continuously refresh OBS overlay state from SQLite. | Reads SQLite and writes local overlay state only. |
| `./scripts/open_demo_terminals.sh --terminal` | Open the named demo terminal set. | Pauses before the live detector terminal executes the caregiver flow. |

## Human Review Required

| Command | Purpose | Gate |
| --- | --- | --- |
| `python3 apps/caresight-hub/scripts/caresight_live_handoff.py send-imessage <request_id> --live-approved` | Send an approved iMessage to an allowlisted private target. | Contact target must match the allowlist; pending receipt is written before execution. |
| `python3 apps/caresight-hub/scripts/caresight_live_handoff.py facetime-if-yes <request_id> --reply-text "yes connect" --live-approved` | Open FaceTime only after an explicit yes-like reply. | Reply must classify as `yes` and match the required phrase. |
| `python3 apps/caresight-hub/scripts/caresight_live_handoff.py wait-reply-facetime-tts <request_id> --since-unix-seconds <timestamp> --live-approved --tts-audio-route blackhole` | Watch local Messages, open FaceTime on yes, and play approved TTS. | Human-approved live handoff path. |
| `python3 apps/caresight-hub/scripts/caresight_tts.py --text <approved_text> --play --play-volume 6.0 --play-repeat-count 2` | Play approved local TTS audio. | Explicit human approval required. |
| `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --obs-browser-feed --auto-agent-live-run --live-approved --auto-facetime-on-reply --play-tts-after-facetime` | Run the live post-event caregiver chain for possible floor-stay events. | Approved message, allowlisted target, reply gate, FaceTime, and TTS gate. |

## Stable Demo Boundary

OBS remains the local visual review surface. FaceTime is reply-gated and can be audio/TTS-only if virtual-camera output is distorted or unreliable. The system does not autonomously dispatch help or diagnose a condition.
