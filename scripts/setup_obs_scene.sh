#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OBS_APP_DIR="$ROOT_DIR/apps/obs-hub"
VENV_DIR="$ROOT_DIR/.venv-obs"
LOCAL_DEMO_ENV="$ROOT_DIR/apps/caresight-hub/config/live-demo.local"

if [[ -f "$LOCAL_DEMO_ENV" ]]; then
  # shellcheck source=/dev/null
  source "$LOCAL_DEMO_ENV"
fi

HOST="${OBS_WEBSOCKET_HOST:-127.0.0.1}"
PORT="${OBS_WEBSOCKET_PORT:-4455}"
WIDTH="${CARESIGHT_OBS_CANVAS_WIDTH:-1920}"
HEIGHT="${CARESIGHT_OBS_CANVAS_HEIGHT:-1080}"
SAMPLE_IMAGE="${CARESIGHT_OBS_SAMPLE_IMAGE:-$OBS_APP_DIR/assets/sample-living-room.jpg}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required for OBS scene setup." >&2
  exit 2
fi

mkdir -p "$OBS_APP_DIR/config" "$OBS_APP_DIR/overlays" "$OBS_APP_DIR/tools" "$OBS_APP_DIR/assets"

if [[ ! -f "$OBS_APP_DIR/config/cameras.json" ]]; then
  cat > "$OBS_APP_DIR/config/cameras.json" <<JSON
{
  "canvas": {
    "width": $WIDTH,
    "height": $HEIGHT
  },
  "cameras": [
    {
      "id": "C1",
      "zone": "Living Room",
      "scene": "CareSight Camera - Living Room",
      "source_name": "CareSight Feed - Living Room",
      "source_type": "image",
      "image_path": "$SAMPLE_IMAGE"
    },
    {
      "id": "C2",
      "zone": "Kitchen",
      "scene": "CareSight Camera - Kitchen",
      "source_name": "CareSight Feed - Kitchen",
      "source_type": "placeholder"
    },
    {
      "id": "C3",
      "zone": "Hallway",
      "scene": "CareSight Camera - Hallway",
      "source_name": "CareSight Feed - Hallway",
      "source_type": "placeholder"
    },
    {
      "id": "C4",
      "zone": "Bedroom",
      "scene": "CareSight Camera - Bedroom",
      "source_name": "CareSight Feed - Bedroom",
      "source_type": "placeholder"
    }
  ]
}
JSON
fi

if [[ ! -f "$OBS_APP_DIR/config/sample_event.json" ]]; then
  echo "Missing $OBS_APP_DIR/config/sample_event.json. Restore the tracked OBS Hub files before setup." >&2
  exit 2
fi

for required in \
  "$OBS_APP_DIR/overlays/camera-feed.html" \
  "$OBS_APP_DIR/overlays/dashboard.html" \
  "$OBS_APP_DIR/overlays/escalation.html" \
  "$OBS_APP_DIR/overlays/obs-overlay.css" \
  "$OBS_APP_DIR/overlays/obs-overlay.js" \
  "$OBS_APP_DIR/tools/setup_obs_scenes.py"; do
  if [[ ! -f "$required" ]]; then
    echo "Missing required OBS Hub file: $required" >&2
    exit 2
  fi
done

if [[ ! -d "$VENV_DIR" ]]; then
  python3 -m venv "$VENV_DIR"
fi

# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip >/dev/null
python -m pip install obsws-python >/dev/null

python "$OBS_APP_DIR/tools/setup_obs_scenes.py" --host "$HOST" --port "$PORT" "$@"
