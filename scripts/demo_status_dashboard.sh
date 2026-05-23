#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATUS_DIR="$ROOT_DIR/apps/caresight-hub/data/runtime/demo-status"
EVENT_STATE="$ROOT_DIR/apps/obs-hub/config/current_event.json"

mkdir -p "$STATUS_DIR"

status_icon() {
  case "$1" in
    ready|running|online) printf "Ready ✅" ;;
    blocked|failed) printf "Blocked ⚠️" ;;
    waiting) printf "Waiting ⏸" ;;
    *) printf "Loading ↻" ;;
  esac
}

read_status() {
  local name="$1"
  local path="$STATUS_DIR/$name.status"
  if [[ -f "$path" ]]; then
    tr -d '\n' < "$path"
  else
    printf "loading"
  fi
}

render_event_feed() {
  if [[ ! -f "$EVENT_STATE" ]]; then
    echo "No overlay event state written yet."
    return
  fi
  python3 - "$EVENT_STATE" <<'PY'
import json
import sys

path = sys.argv[1]
try:
    payload = json.load(open(path, encoding="utf-8"))
except Exception as exc:
    print(f"Overlay state unavailable: {type(exc).__name__}")
    raise SystemExit(0)

event = payload.get("current_event", {})
handoff = payload.get("handoff_status", {})
print(f"Current event: {event.get('display_label', 'Review required')} | {event.get('zone', 'Unknown zone')} | {event.get('display_id', 'no id')}")
if handoff:
    print(f"Handoff: {handoff.get('label', 'Review required')}")
print("")
for item in payload.get("alert_feed", [])[-6:]:
    time = item.get("time", "")
    label = item.get("label", "CareSight activity")
    status = item.get("status", "Logged")
    detail = item.get("detail", "")
    print(f"- {time} | {label} | {status}")
    if detail:
        print(f"  {detail}")
PY
}

while true; do
  stack_status="$(read_status stack)"
  overlay_status="$(read_status overlay)"
  check_status="$(read_status check)"
  live_status="$(read_status live)"

  clear
  printf '\033]0;%s\007' "CareSight Status Board"
  printf '\033]1;%s\007' "CareSight Status Board"
  echo "CareSight Demo Status"
  echo "====================="
  echo
  echo "Terminal 1 - CareSight Stack: $(status_icon "$stack_status")"
  echo "Terminal 2 - OBS Overlay Watch: $(status_icon "$overlay_status")"
  echo "Terminal 3 - OBS/Feed Check: $(status_icon "$check_status")"
  echo "Terminal 4 - Live Detector + Handoff: $(status_icon "$live_status")"
  echo
  if [[ "$stack_status" =~ ^(ready|running|online)$ && "$overlay_status" =~ ^(ready|running|online)$ ]]; then
    echo "CareSight Hub: Online, view feeds in OBS"
  else
    echo "CareSight Hub: Loading local demo services"
  fi
  echo "----"
  echo
  echo "Event Feed"
  echo "----------"
  render_event_feed
  echo
  echo "Refreshes every 2 seconds. Ctrl-C closes this status board only."
  sleep 2
done
