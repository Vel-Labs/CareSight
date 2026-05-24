from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]


def load_model_manifests(path: str | Path) -> list[dict[str, object]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    manifests = data.get("models", data)
    if not isinstance(manifests, list):
        raise ValueError("model manifest config must be a JSON array or an object with models")
    return [dict(item) for item in manifests]


def check_model_manifest(manifest: dict[str, object], *, run_validation: bool = False) -> dict[str, object]:
    model_id = str(manifest.get("model_id", ""))
    blockers: list[dict[str, str]] = []
    required_fields = [
        "model_id",
        "purpose_lane",
        "source_url",
        "license",
        "local_path",
        "sha256",
        "expected_size_bytes",
        "runtime",
        "allowed_uses",
        "blocked_uses",
        "validation_command",
        "last_validated_at",
    ]
    for field in required_fields:
        if field not in manifest:
            blockers.append({"code": "missing_manifest_field", "detail": field})
            continue
        if field != "last_validated_at" and manifest[field] in (None, "", []):
            blockers.append({"code": "missing_manifest_field", "detail": field})
    if blockers:
        return _result(model_id=model_id or "unknown", status="blocked", blockers=blockers, manifest=manifest)

    local_path = _resolve_path(str(manifest["local_path"]))
    if not local_path.exists():
        blockers.append({"code": "missing_model_path", "detail": str(local_path)})
        return _result(model_id=model_id, status="blocked", blockers=blockers, manifest=manifest)

    expected_size = int(manifest["expected_size_bytes"])
    actual_size = _path_size(local_path)
    if actual_size != expected_size:
        blockers.append({"code": "size_mismatch", "detail": f"expected={expected_size} actual={actual_size}"})

    expected_sha = str(manifest["sha256"]).lower()
    actual_sha = sha256_path(local_path)
    if actual_sha != expected_sha:
        blockers.append({"code": "checksum_mismatch", "detail": f"expected={expected_sha} actual={actual_sha}"})

    validation = {"ran": False, "returncode": None}
    if run_validation and not blockers:
        command = str(manifest["validation_command"])
        completed = subprocess.run(command, cwd=REPO_ROOT, shell=True, capture_output=True, text=True, check=False)
        validation = {"ran": True, "returncode": completed.returncode}
        if completed.returncode != 0:
            blockers.append({"code": "validation_command_failed", "detail": (completed.stderr or completed.stdout)[-300:]})

    return _result(
        model_id=model_id,
        status="pass" if not blockers else "blocked",
        blockers=blockers,
        manifest=manifest,
        actual_size=actual_size,
        actual_sha256=actual_sha,
        validation=validation,
    )


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    if path.is_dir():
        for child in sorted(item for item in path.rglob("*") if item.is_file()):
            digest.update(str(child.relative_to(path)).encode("utf-8"))
            digest.update(b"\0")
            with child.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
    else:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def _path_size(path: Path) -> int:
    if path.is_dir():
        return sum(child.stat().st_size for child in path.rglob("*") if child.is_file())
    return path.stat().st_size


def _resolve_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def _result(
    *,
    model_id: str,
    status: str,
    blockers: list[dict[str, str]],
    manifest: dict[str, object],
    actual_size: int | None = None,
    actual_sha256: str | None = None,
    validation: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "model_id": model_id,
        "purpose_lane": manifest.get("purpose_lane"),
        "runtime": manifest.get("runtime"),
        "license": manifest.get("license"),
        "status": status,
        "blockers": blockers,
        "actual_size_bytes": actual_size,
        "actual_sha256": actual_sha256,
        "validation": validation or {"ran": False, "returncode": None},
    }
