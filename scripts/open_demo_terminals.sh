#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATUS_DIR="$ROOT_DIR/apps/caresight-hub/data/runtime/demo-status"
MODE="${1:---tabs}"

case "$MODE" in
  --terminal|--tabs|--windows|--print|--help) ;;
  *)
    echo "Usage: $0 [--tabs|--windows|--print]" >&2
    exit 2
    ;;
esac

if [[ "$MODE" == "--help" ]]; then
  cat <<'EOF'
Usage:
  ./scripts/open_demo_terminals.sh --tabs      # open named macOS Terminal tabs
  ./scripts/open_demo_terminals.sh --windows   # open named macOS Terminal windows
  ./scripts/open_demo_terminals.sh --print     # print tab names and commands for VS Code/manual tabs

The default uses Terminal tabs to keep the demo surface compact. If macOS UI
automation focus blocks tab creation, use --windows or --print.
EOF
  exit 0
fi

mkdir -p "$STATUS_DIR"
rm -f "$STATUS_DIR"/*.status
printf "loading\n" > "$STATUS_DIR/stack.status"
printf "loading\n" > "$STATUS_DIR/overlay.status"
printf "loading\n" > "$STATUS_DIR/check.status"
printf "loading\n" > "$STATUS_DIR/living.status"
printf "loading\n" > "$STATUS_DIR/kitchen.status"

terminal_command() {
  local title="$1"
  local command_body="$2"
  cat <<EOF
cd "$ROOT_DIR"
printf '\\033]0;%s\\007' "$title"
printf '\\033]1;%s\\007' "$title"
source apps/caresight-hub/config/live-demo.local 2>/dev/null || true
clear
echo "== $title =="
$command_body
EOF
}

detector_cleanup_snippet() {
  local camera_id="$1"
  local port="$2"
  cat <<EOF
cleanup_detector() {
  local camera_id="$1"
  local port="$2"
  local pid_path="apps/caresight-hub/data/runtime/\${camera_id}_detector.pid"
  if [[ -f "\$pid_path" ]]; then
    local pid
    pid="\$(tr -d '[:space:]' < "\$pid_path" || true)"
    if [[ "\$pid" =~ ^[0-9]+$ ]] && kill -0 "\$pid" 2>/dev/null; then
      echo "Stopping previous \$camera_id detector pid \$pid"
      kill "\$pid" 2>/dev/null || true
      sleep 1
      if kill -0 "\$pid" 2>/dev/null; then
        echo "Previous \$camera_id detector still running; forcing stop"
        kill -9 "\$pid" 2>/dev/null || true
      fi
    fi
    rm -f "\$pid_path"
  fi
  while IFS= read -r pid; do
    [[ -z "\$pid" ]] && continue
    local command
    command="\$(ps -p "\$pid" -o command= 2>/dev/null || true)"
    if [[ "\$command" == *"v0_floor_stay_live.py"* ]]; then
      echo "Stopping CareSight process on port \$port pid \$pid"
      kill "\$pid" 2>/dev/null || true
      sleep 1
      if kill -0 "\$pid" 2>/dev/null; then
        echo "CareSight process on port \$port still running; forcing stop"
        kill -9 "\$pid" 2>/dev/null || true
      fi
    else
      echo "Port \$port is in use by a non-CareSight process pid \$pid; refusing to kill it."
      return 1
    fi
  done < <(lsof -tiTCP:"\$port" -sTCP:LISTEN 2>/dev/null || true)
}
cleanup_detector "$camera_id" "$port"
EOF
}

stack_cmd="$(terminal_command "CareSight Stack" 'echo loading > apps/caresight-hub/data/runtime/demo-status/stack.status
if python3 apps/caresight-hub/scripts/caresight_stack_start.py; then
  echo ready > apps/caresight-hub/data/runtime/demo-status/stack.status
else
  echo failed > apps/caresight-hub/data/runtime/demo-status/stack.status
fi
echo
echo "Stack command finished. Leave this tab open for logs."')"

overlay_cmd="$(terminal_command "OBS Overlay Watch" 'echo loading > apps/caresight-hub/data/runtime/demo-status/overlay.status
echo ready > apps/caresight-hub/data/runtime/demo-status/overlay.status
./scripts/update_obs_overlay.sh --watch')"

check_cmd="$(terminal_command "OBS Feed Check" 'echo waiting > apps/caresight-hub/data/runtime/demo-status/check.status
echo "Waiting for the live detector feed before marking this check blocked..."
for attempt in 1 2 3 4 5 6 7 8 9 10; do
  if apps/obs-hub/tools/check_obs_live_feed.py; then
    echo ready > apps/caresight-hub/data/runtime/demo-status/check.status
    break
  fi
  if [[ "$attempt" -lt 10 ]]; then
    echo waiting > apps/caresight-hub/data/runtime/demo-status/check.status
    echo "OBS/feed check waiting ($attempt/10). Start Terminal 4 and Terminal 5 when ready."
    sleep 2
  else
    echo blocked > apps/caresight-hub/data/runtime/demo-status/check.status
  fi
done
echo
echo "Rerun check with: apps/obs-hub/tools/check_obs_live_feed.py"
exec "$SHELL" -l')"

living_cleanup="$(detector_cleanup_snippet "tapo_living_room" "8766")"
living_body="$(cat <<EOF
echo "This tab starts the Living Room detector feed for OBS."
echo "It runs floor-stay, posture indicators, and missing-off-camera events for tapo_living_room."
echo "FaceTime handoff preserves the current OBS camera/scene selection."
echo
echo waiting > apps/caresight-hub/data/runtime/demo-status/living.status
echo "Starting Living Room detector."
$living_cleanup
trap 'echo stopped > apps/caresight-hub/data/runtime/demo-status/living.status' EXIT
echo running > apps/caresight-hub/data/runtime/demo-status/living.status
export CARESIGHT_AITUM_VERTICAL_MODE=off
export CARESIGHT_OBS_FACETIME_SCENE=""
export CARESIGHT_OBS_FACETIME_VIDEO_MODE=""
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python \
  apps/caresight-hub/scripts/v0_floor_stay_live.py \
  --config apps/caresight-hub/config/tapo-runtime.local.json \
  --camera-id tapo_living_room \
  --max-seconds 600 \
  --obs-browser-feed \
  --obs-browser-feed-port 8766 \
  --appearance-overlay \
  --missing-off-camera-events \
  --debug-floor-stay \
  --auto-agent-live-run \
  --live-approved \
  --auto-facetime-on-reply \
  --reply-timeout-seconds 120 \
  --no-response-escalation-seconds 90 \
  --play-tts-after-facetime \
  --tts-audio-route blackhole \
  --tts-volume 6.0 \
  --tts-repeat-count 2 \
  --tts-repeat-delay-seconds 1.5 \
  --tts-after-facetime-delay-seconds 16 \
  --post-facetime-hold-seconds 30 \
  --no-window
EOF
)"
living_cmd="$(terminal_command "Living Room Detector" "$living_body")"

kitchen_cleanup="$(detector_cleanup_snippet "tapo_kitchen" "8767")"
kitchen_body="$(cat <<EOF
echo "This tab starts the Kitchen detector feed for OBS."
echo "It runs floor-stay, posture indicators, and missing-off-camera events for tapo_kitchen."
echo
echo waiting > apps/caresight-hub/data/runtime/demo-status/kitchen.status
echo "Starting Kitchen detector."
$kitchen_cleanup
trap 'echo stopped > apps/caresight-hub/data/runtime/demo-status/kitchen.status' EXIT
echo running > apps/caresight-hub/data/runtime/demo-status/kitchen.status
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python \
  apps/caresight-hub/scripts/v0_floor_stay_live.py \
  --config apps/caresight-hub/config/tapo-runtime.local.json \
  --camera-id tapo_kitchen \
  --max-seconds 600 \
  --obs-browser-feed \
  --obs-browser-feed-port 8767 \
  --appearance-overlay \
  --missing-off-camera-events \
  --debug-floor-stay \
  --no-window
EOF
)"
kitchen_cmd="$(terminal_command "Kitchen Detector" "$kitchen_body")"

status_cmd="$(terminal_command "CareSight Status Board" './scripts/demo_status_dashboard.sh')"

export STACK_CMD="$stack_cmd"
export OVERLAY_CMD="$overlay_cmd"
export CHECK_CMD="$check_cmd"
export LIVING_CMD="$living_cmd"
export KITCHEN_CMD="$kitchen_cmd"
export STATUS_CMD="$status_cmd"

if [[ "$MODE" == "--print" ]]; then
  cat <<EOF
Open six terminal tabs and paste one block into each.

### Terminal 1 - CareSight Stack
$stack_cmd

### Terminal 2 - OBS Overlay Watch
$overlay_cmd

### Terminal 3 - OBS/Feed Check
$check_cmd

### Terminal 4 - Living Room Detector
$living_cmd

### Terminal 5 - Kitchen Detector
$kitchen_cmd

### Terminal 6 - CareSight Status Board
$status_cmd
EOF
  exit 0
fi

if [[ "$MODE" == "--terminal" || "$MODE" == "--windows" ]]; then
  osascript <<OSA
on runCommandInNewWindow(commandText)
  tell application "Terminal"
    activate
    do script commandText
  end tell
end runCommandInNewWindow

runCommandInNewWindow($(python3 -c 'import json, os; print(json.dumps(os.environ["STACK_CMD"]))'))
delay 1
runCommandInNewWindow($(python3 -c 'import json, os; print(json.dumps(os.environ["OVERLAY_CMD"]))'))
delay 1
runCommandInNewWindow($(python3 -c 'import json, os; print(json.dumps(os.environ["CHECK_CMD"]))'))
delay 1
runCommandInNewWindow($(python3 -c 'import json, os; print(json.dumps(os.environ["LIVING_CMD"]))'))
delay 1
runCommandInNewWindow($(python3 -c 'import json, os; print(json.dumps(os.environ["KITCHEN_CMD"]))'))
delay 1
runCommandInNewWindow($(python3 -c 'import json, os; print(json.dumps(os.environ["STATUS_CMD"]))'))
OSA
  exit 0
fi

osascript <<OSA
on runCommandInNewTab(commandText)
  tell application "Terminal" to activate
  tell application "System Events"
    tell process "Terminal"
      keystroke "t" using command down
      delay 0.2
    end tell
  end tell
  tell application "Terminal"
    do script commandText in selected tab of front window
  end tell
end runCommandInNewTab

tell application "Terminal"
  activate
  if not (exists window 1) then
    do script ""
  end if
end tell

tell application "Terminal"
  do script $(python3 -c 'import json, os; print(json.dumps(os.environ["STACK_CMD"]))') in selected tab of front window
end tell
delay 1
runCommandInNewTab($(python3 -c 'import json, os; print(json.dumps(os.environ["OVERLAY_CMD"]))'))
delay 1
runCommandInNewTab($(python3 -c 'import json, os; print(json.dumps(os.environ["CHECK_CMD"]))'))
delay 1
runCommandInNewTab($(python3 -c 'import json, os; print(json.dumps(os.environ["LIVING_CMD"]))'))
delay 1
runCommandInNewTab($(python3 -c 'import json, os; print(json.dumps(os.environ["KITCHEN_CMD"]))'))
delay 1
runCommandInNewTab($(python3 -c 'import json, os; print(json.dumps(os.environ["STATUS_CMD"]))'))
OSA
