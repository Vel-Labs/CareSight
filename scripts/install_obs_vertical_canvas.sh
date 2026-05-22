#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOWNLOAD_DIR="$ROOT_DIR/apps/obs-hub/vendor/aitum"
REPO_API="https://api.github.com/repos/Aitum/obs-vertical-canvas/releases/latest"

mkdir -p "$DOWNLOAD_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to resolve the latest Aitum Vertical Canvas release." >&2
  exit 2
fi

read -r VERSION ASSET_URL ASSET_NAME < <(
  python3 - <<'PY'
import json
import sys
from urllib.request import Request, urlopen

request = Request("https://api.github.com/repos/Aitum/obs-vertical-canvas/releases/latest")
with urlopen(request, timeout=20) as response:
    payload = json.loads(response.read().decode("utf-8"))

for asset in payload.get("assets", []):
    name = str(asset.get("name", ""))
    if name == "vertical-canvas-macos-universal.pkg":
        print(payload.get("tag_name", "unknown"), asset["browser_download_url"], name)
        raise SystemExit(0)

print("Latest release did not include vertical-canvas-macos-universal.pkg", file=sys.stderr)
raise SystemExit(2)
PY
)

PKG_PATH="$DOWNLOAD_DIR/$ASSET_NAME"

echo "Aitum Vertical Canvas release: $VERSION"
echo "Download: $ASSET_URL"

if [[ ! -f "$PKG_PATH" ]]; then
  curl -L "$ASSET_URL" -o "$PKG_PATH"
fi

echo
echo "Downloaded installer:"
echo "$PKG_PATH"
echo
echo "Install with:"
echo "open \"$PKG_PATH\""
echo
echo "After installation, restart OBS and confirm the Vertical dock appears."
echo "Then run:"
echo "apps/obs-hub/tools/aitum_vertical.py status"
