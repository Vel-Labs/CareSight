# Sprint 02 No-Call Runtime Audit

Date: 2026-05-23

Scope: no-call/no-send Sprint 02 runtime status check for FaceTime x OBS virtual camera, TTS, Hermes/iMessage dry-run boundaries, and execution-attempt surfaces.

## Commands And Results

```bash
python3 apps/caresight-hub/scripts/caresight_demo_preflight.py --json
```

Result: `ready=true`.

Notable ready checks:

- SQLite database present.
- Contact allowlist present.
- Local demo env present.
- YOLO runtime Python and `yolo26n.npz` present.
- Gemma model and endpoint present/reachable.
- Holler TTS model present.
- OBS scene tool dry-run passed.
- OBS password present.
- BlackHole/SwitchAudioSource present.

Notable non-ready optional checks:

- `obs_mjpeg_feed=false`: detector was not currently serving `--obs-browser-feed`.
- Aitum Vertical Canvas plugin not reachable; plain OBS fallback remains available.

```bash
python3 apps/caresight-hub/scripts/caresight_audio_route.py check
```

Result: BlackHole 2ch input/output and `SwitchAudioSource` are available. Current input/output remained MacBook Pro microphone/speakers.

```bash
apps/obs-hub/tools/check_obs_live_feed.py
```

Result: blocked.

```text
BLOCKED detector_mjpeg_health: not reachable: URLError: connection refused
BLOCKED obs_websocket: not reachable: ConnectionRefusedError: connection refused
```

This is an environment/runtime-state blocker: the detector feed was not running and OBS websocket was not reachable. It is not evidence of a CareSight event-policy defect.

```bash
python3 apps/caresight-hub/scripts/caresight_tts.py \
  --voice dakota \
  --text "CareSight alert. Possible floor stay observed in the Living Room. Needs review."
```

Result: local WAV generated at `apps/caresight-hub/data/tts/caresight_tts_000.wav`; `played=false`.

```bash
python3 apps/caresight-hub/scripts/care_console.py list-execution-attempts --help
python3 apps/caresight-hub/scripts/caresight_live_handoff.py --help
```

Result: both help commands rendered; no action subcommand was executed.

## Status Matrix

| Gate | Status | Evidence |
| --- | --- | --- |
| Gemma endpoint | ready in this audit | `caresight_demo_preflight.py --json` reported endpoint ready |
| Hermes/iMessage dry-run surface | inspectable | CLI/help and prior execution-attempt surfaces exist; no live send performed |
| OBS live feed | blocked | detector MJPEG server and OBS websocket were not reachable |
| FaceTime visual handoff | not run | no-call overnight boundary preserved |
| TTS generation | ready for generated audio | Dakota WAV generated locally with `played=false` |
| TTS playback/audibility | human-validation pending | playback intentionally not run |
| Execution-attempt logging | inspectable | `care_console.py list-execution-attempts --help` rendered |

## Boundary

This audit did not send iMessage, open FaceTime, play TTS audio, confirm or dismiss events, mutate OBS scenes, trigger dispatch, or claim production readiness.

## Next Operator Step

Start the detector with `--obs-browser-feed`, confirm OBS is open with websocket enabled, then rerun `apps/obs-hub/tools/check_obs_live_feed.py`. TTS playback and FaceTime visual validation remain explicit human-validation steps.
