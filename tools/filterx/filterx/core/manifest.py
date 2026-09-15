from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from .io import ensure_parent_dir, load_json, utc_now_iso, write_json

MANIFEST_VERSION = 1
SUPPORTED_MANIFEST_VERSIONS = (MANIFEST_VERSION,)


@dataclass
class ManifestState:
    data: Dict[str, Any]
    path: Path


def _default_manifest() -> Dict[str, Any]:
    return {
        "version": MANIFEST_VERSION,
        "created_at": utc_now_iso(),
        "updated_at": utc_now_iso(),
        "entries": {},
        "patch_history": [],
    }


def load_manifest(path: Path) -> ManifestState:
    if not path.exists():
        return ManifestState(data=_default_manifest(), path=path)
    data = load_json(path)
    if not isinstance(data, dict):
        data = _default_manifest()
    if "entries" not in data or not isinstance(data["entries"], dict):
        data["entries"] = {}
    if "patch_history" not in data or not isinstance(data["patch_history"], list):
        data["patch_history"] = []
    if "version" not in data:
        data["version"] = MANIFEST_VERSION
    return ManifestState(data=data, path=path)


def validate_manifest(state: ManifestState) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    version = state.data.get("version", MANIFEST_VERSION)
    if version not in SUPPORTED_MANIFEST_VERSIONS:
        issues.append(
            {
                "code": "MANIFEST_VERSION_UNSUPPORTED",
                "path": str(state.path),
                "version": version,
                "supported_versions": list(SUPPORTED_MANIFEST_VERSIONS),
            }
        )
    if not isinstance(state.data.get("entries"), dict):
        issues.append({"code": "MANIFEST_ENTRIES_INVALID", "path": str(state.path)})
    if not isinstance(state.data.get("patch_history"), list):
        issues.append({"code": "MANIFEST_PATCH_HISTORY_INVALID", "path": str(state.path)})
    return issues


def save_manifest(state: ManifestState) -> None:
    state.data["updated_at"] = utc_now_iso()
    ensure_parent_dir(state.path)
    write_json(state.path, state.data)


def set_entry(
    state: ManifestState,
    relative_path: str,
    kind: str,
    sha256: str,
    patch_id: str,
    metadata: Dict[str, Any] | None = None,
) -> None:
    entry: Dict[str, Any] = {
        "kind": kind,
        "sha256": sha256,
        "last_patch_id": patch_id,
        "updated_at": utc_now_iso(),
    }
    if metadata:
        entry["metadata"] = metadata
    state.data["entries"][relative_path] = entry


def delete_entry(state: ManifestState, relative_path: str) -> None:
    state.data["entries"].pop(relative_path, None)


def append_patch_history(
    state: ManifestState,
    patch_id: str,
    touched_files: List[str],
    mode: str,
    description: str,
) -> None:
    state.data["patch_history"].append(
        {
            "patch_id": patch_id,
            "created_at": utc_now_iso(),
            "mode": mode,
            "description": description,
            "touched_files": touched_files,
        }
    )
