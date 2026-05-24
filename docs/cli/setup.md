# Setup Commands

Setup commands prepare local dependencies. They do not grant authority to send caregiver messages, open FaceTime, play TTS, confirm events, or claim production readiness.

## Manual Operator

| Command | Purpose | Validation |
| --- | --- | --- |
| `python3 apps/caresight-hub/scripts/caresight_install_all.py` | Install runtime venv, default local models, and OBS. | Rerun `npm run check`, then stack start. |
| `python3 apps/caresight-hub/scripts/caresight_install_model.py gemma-e2b` | Install one ignored local model from Hugging Face. | Gemma: start stack. TTS: generate without `--play`. |
| `python3 apps/caresight-hub/scripts/caresight_install_obs.py` | Install or verify OBS. | `python3 apps/caresight-hub/scripts/caresight_install_obs.py --check-only`. |
| `python3 apps/caresight-hub/scripts/caresight_setup_fixtures.py` | Build local fixture/readiness outputs. | Script exits successfully. |
| `python3 apps/caresight-hub/scripts/caresight_gemma_start.py` | Start the local Gemma MLX OpenAI-compatible endpoint. | Bounded local chat-completions pulse. |
| `python3 apps/caresight-hub/scripts/caresight_gemma_stop.py` | Stop the local Gemma server. | PID file removed or stale PID reported. |
| `python3 apps/caresight-hub/scripts/caresight_hermes_start.py --require-gemma` | Verify vendored Hermes no-send readiness. | Imports Hermes and calls only `send_message(action="list")`; with `--require-gemma`, checks local Gemma. |
| `python3 apps/caresight-hub/scripts/caresight_hermes_stop.py` | Clear local Hermes readiness marker. | Marker removal only. |
| `python3 apps/caresight-hub/scripts/caresight_stack_start.py` | Start Gemma and verify Hermes readiness. | Gemma pulse plus Hermes `--require-gemma`. |
| `python3 apps/caresight-hub/scripts/caresight_stack_stop.py` | Stop local stack processes/markers. | Local stop commands only. |
| `python3 apps/caresight-hub/scripts/caresight_demo_preflight.py` | Check local demo runway: SQLite, contacts, YOLO, OBS, Gemma, BlackHole, env. | Skimmable report or `--json` receipt. |

## Agent-Safe Read

| Command | Purpose | Validation |
| --- | --- | --- |
| `python apps/caresight-hub/scripts/care_console.py model-doctor` | Validate governed local model manifests before model readiness claims. | `test_runtime_healthcheck.py` and `test_care_console.py`. |

`model-doctor --run-validation-command` may become `manual-operator` depending on the manifest command it executes.
