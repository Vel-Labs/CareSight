#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
YOLO_DIR = ROOT_DIR / "vendor" / "yolo-mlx"
DEFAULT_CONFIG = ROOT_DIR / "config" / "v0.example.json"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "data" / "appearance-validation" / "annotated"
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(YOLO_DIR))

from caresight.runtime.appearance import build_yolo_appearance_review  # noqa: E402
from caresight.runtime.inference import CareSightInferenceHarness  # noqa: E402
from caresight.runtime.inference.adapter import InferenceUnavailableError, ModelLoadError  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run YOLO26 MLX on a still image and write person-level appearance review annotations."
    )
    parser.add_argument("image_path")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    harness = CareSightInferenceHarness.from_config_path(args.config)
    try:
        result = harness.run(args.image_path)
    except (ModelLoadError, InferenceUnavailableError) as error:
        raise SystemExit(f"fail_closed={error}") from error
    receipt = build_yolo_appearance_review(
        snapshot_path=args.image_path,
        detections=result.detections,
        output_dir=args.output_dir,
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
