from __future__ import annotations

from pathlib import Path
from typing import Callable


def attach_local_snapshot(
    event: dict,
    snapshot_dir: str | Path,
    write_snapshot: Callable[[Path], None],
) -> dict:
    target_dir = Path(snapshot_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = target_dir / f"{event['event_id']}.jpg"
    write_snapshot(snapshot_path)

    event["evidence"]["snapshot_path"] = str(snapshot_path)
    event["evidence"]["snapshot_stays_local"] = True
    return event
