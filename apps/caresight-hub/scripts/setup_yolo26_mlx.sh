#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
YOLO_DIR="$ROOT_DIR/vendor/yolo-mlx"
VENV_DIR="$YOLO_DIR/.venv"

if [[ ! -d "$YOLO_DIR/.git" ]]; then
  echo "Missing YOLO26 MLX checkout at $YOLO_DIR" >&2
  echo "Expected: git clone https://github.com/thewebAI/yolo-mlx.git $YOLO_DIR" >&2
  exit 1
fi

python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip
python -m pip install -e "$YOLO_DIR"
python -m pip install -e "$YOLO_DIR[convert]"
python -m pip install opencv-python

python - <<'PY'
import platform
from yolo26mlx import YOLO

print(f"processor={platform.processor()}")
print(f"yolo26mlx.YOLO={YOLO.__name__}")
PY

echo
echo "YOLO26 MLX environment ready."
echo "Activate with: source $VENV_DIR/bin/activate"
