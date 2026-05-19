#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
YOLO_DIR="$ROOT_DIR/vendor/yolo-mlx"
VENV_DIR="$YOLO_DIR/.venv"

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "Missing YOLO26 MLX venv. Run apps/caresight-hub/scripts/setup_yolo26_mlx.sh first." >&2
  exit 1
fi

source "$VENV_DIR/bin/activate"
cd "$YOLO_DIR"

bash scripts/download_yolo26_models.sh
yolo26 converters convert models/yolo26n.pt -o models/yolo26n.npz --verify

echo
echo "Prepared $YOLO_DIR/models/yolo26n.npz"
