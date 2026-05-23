# Sprint 02 FaceTime / OBS / TTS Resolution Ladder

Date: 2026-05-23

Scope: source-backed resolution research plus no-call/no-send local checks for the Sprint 02 handoff lane. This receipt does not send iMessage, open FaceTime, mutate OBS scenes, or play TTS.

## Sources

- OBS Virtual Camera troubleshooting: `https://obsproject.com/kb/virtual-camera-troubleshooting`
- OBS Virtual Camera guide: `https://obsproject.com/kb/virtual-camera-guide`
- Apple FaceTime camera/microphone selection: `https://support.apple.com/en-ae/guide/facetime/fctm26739220/mac`
- Apple FaceTime troubleshooting: `https://support.apple.com/en-gb/102203`
- Apple FaceTime audio options: `https://support.apple.com/en-gw/guide/facetime/fctme7c07113/mac`
- BlackHole audio loopback: `https://github.com/ExistentialAudio/BlackHole`

## Findings

- OBS virtual camera should be treated as a scene/source output selector, not a guaranteed FaceTime layout path. Pin a known OBS scene/source before testing.
- OBS notes macOS 13+ plus OBS 30+ virtual-camera behavior; older OBS virtual-camera components can be incompatible with newer macOS versions.
- Apple documents camera and microphone selection inside FaceTime's Video menu. Validate device selection before blaming CareSight runtime code.
- Apple troubleshooting recommends verifying camera/microphone selection and testing the camera in another app. Use a local app or OBS preview first.
- BlackHole is an app-to-app audio loopback path. For TTS into FaceTime, the sending output and FaceTime input both need to point at the loopback device.

## No-Call Checks Run

```bash
python3 apps/caresight-hub/scripts/caresight_demo_preflight.py --json
```

Result summary:

- `ready=true`
- local contact allowlist present
- YOLO runtime/model present
- Gemma and TTS model paths present
- OBS scene tool dry-run passed
- `obs_mjpeg_feed=false`: detector must be started with `--obs-browser-feed`
- Aitum Vertical Canvas optional plugin not reachable
- `blackhole_switcher=true`
- Gemma endpoint check was sandbox-blocked in this run; do not treat it as a fresh endpoint proof

```bash
apps/obs-hub/tools/check_obs_live_feed.py
```

Result after rerun with loopback permission:

```text
ready=false
BLOCKED detector_mjpeg_health: connection refused
BLOCKED obs_websocket: connection refused
```

Interpretation: detector MJPEG server and OBS websocket were not running/reachable. This is a setup/runtime-state blocker, not evidence that the CareSight event or draft pipeline is broken.

```bash
python3 apps/caresight-hub/scripts/caresight_audio_route.py check
```

Result summary:

- `switchaudio_available=true`
- `blackhole_input_available=false`
- `blackhole_output_available=false`
- install notes still require BlackHole device availability and reboot if newly installed

```bash
python3 apps/caresight-hub/scripts/caresight_tts.py --voice dakota --text 'CareSight alert. Possible floor stay observed in the Living Room. Needs review.'
```

First sandbox run failed with Metal unavailable. Rerun with local Metal access succeeded:

```text
tts_generated ... voice=dakota played=false ... audio_path=apps/caresight-hub/data/tts/caresight_tts_000.wav
```

```bash
python3 apps/caresight-hub/scripts/caresight_live_handoff.py --help
```

Result: command help rendered; no subcommand executed.

## Recommended Test Ladder

1. Start the detector with `--obs-browser-feed` and confirm `http://127.0.0.1:8766/live.html` renders locally.
2. Start OBS with websocket enabled and rerun `apps/obs-hub/tools/check_obs_live_feed.py`.
3. Keep OBS as the visual operator/review surface by default. Only test OBS Virtual Camera into FaceTime after explicit operator approval.
4. If FaceTime visual output stretches, mirrors, or drops the OBS feed, keep the stable boundary: FaceTime is the reply-gated audio/TTS call, while OBS is the local visual proof surface.
5. Install/confirm BlackHole 2ch appears as both input and output. Run `caresight_audio_route.py check` again before any playback.
6. Generate Dakota TTS with `played=false`, then play only after the wording and audibility test are explicitly approved.

## Boundary

No live iMessage, FaceTime call, TTS playback, OBS scene mutation, emergency dispatch, medical claim, event confirmation, event dismissal, raw-video upload, or contact-handle commit occurred.
