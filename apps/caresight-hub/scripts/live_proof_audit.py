import argparse
import json
import sys
from datetime import timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
DEFAULT_CONFIG_PATH = ROOT_DIR / "config" / "v0.example.json"
DEFAULT_MODEL_PATH = ROOT_DIR / "vendor" / "yolo-mlx" / "models" / "yolo26n.npz"
DEFAULT_DB_PATH = ROOT_DIR / "data" / "caresight-v0.sqlite3"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect read-only CareSight live-proof readiness and audit bundles."
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="CareSight v0 config JSON.")
    parser.add_argument("--model", default=str(DEFAULT_MODEL_PATH), help="YOLO26 MLX .npz model path.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="CareSight SQLite database.")
    parser.add_argument("--output", help="Optional local JSON report artifact path.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    readiness = subparsers.add_parser("readiness", help="Check config/model environment readiness.")
    readiness.add_argument(
        "--camera-authorization",
        choices=["granted", "blocked", "not_checked"],
        default="not_checked",
        help="Operator-observed camera authorization state; use blocked after OpenCV reports not authorized.",
    )

    bundle = subparsers.add_parser("bundle", help="Emit a read-only SQLite-backed audit bundle.")
    bundle.add_argument("event_id", help="Fresh live event_id from an operator-captured event_persisted line.")
    bundle.add_argument(
        "--max-event-age-minutes",
        type=float,
        default=15.0,
        help="Reject older event IDs as not_complete live proof.",
    )
    return parser.parse_args()


def main() -> None:
    from caresight.runtime.audit.live_proof import (
        LiveProofAuditCollector,
        ReadinessInputs,
        build_readiness_report,
        write_json_report,
    )
    from caresight.storage.sqlite_store import SQLiteStore

    args = parse_args()

    if args.command == "readiness":
        payload = build_readiness_report(
            ReadinessInputs(
                config_path=Path(args.config),
                model_path=Path(args.model),
                camera_authorization=args.camera_authorization,
            )
        )
    elif args.command == "bundle":
        store = SQLiteStore(args.db)
        collector = LiveProofAuditCollector(
            store,
            max_event_age=timedelta(minutes=args.max_event_age_minutes),
        )
        payload = collector.collect(args.event_id)
    else:  # pragma: no cover - argparse enforces known commands.
        raise SystemExit(f"Unsupported command: {args.command}")

    if args.output:
        write_json_report(payload, args.output)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
