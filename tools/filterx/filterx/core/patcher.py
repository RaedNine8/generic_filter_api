from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Mapping, Optional

from .conflicts import check_anchor_exists
from .io import ensure_parent_dir, utc_now_iso, write_json
from .manifest import (
    ManifestState,
    append_patch_history,
    delete_entry,
    load_manifest,
    save_manifest,
    set_entry,
)
from .structured_merge import render_gradle_merge, render_maven_merge

PatchKind = Literal["generated_file", "anchor_insert", "delete_file", "structured_merge"]
InsertMode = Literal["after", "before"]
StructuredFormat = Literal["json", "xml", "gradle"]


@dataclass
class PatchOp:
    kind: PatchKind
    path: str
    content: str = ""
    owner: Literal["filterx-generated", "host"] = "filterx-generated"
    anchor: Optional[str] = None
    snippet: Optional[str] = None
    insert_mode: InsertMode = "after"
    description: str = ""
    structured_format: Optional[StructuredFormat] = None
    merge: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class PatchIssue:
    code: str
    message: str
    context: Dict[str, str] = field(default_factory=dict)


@dataclass
class ApplyResult:
    patch_id: str
    dry_run: bool
    touched_files: List[str]
    applied_ops: int
    skipped_ops: int
    issues: List[PatchIssue]

    @property
    def has_conflicts(self) -> bool:
        return any(issue.code.startswith("CONFLICT_") for issue in self.issues)



def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()



def _new_patch_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    suffix = uuid.uuid4().hex[:8]
    return f"patch-{ts}-{suffix}"



def _resolve(project_root: Path, rel_or_abs: str) -> Path:
    p = Path(rel_or_abs)
    return p if p.is_absolute() else (project_root / p)


def _project_relative_path(project_root: Path, target_path: Path) -> str:
    root = project_root.resolve()
    target = target_path.resolve()
    try:
        return target.relative_to(root).as_posix()
    except ValueError:
        try:
            return Path(os.path.relpath(target, root)).as_posix()
        except ValueError:
            return target.as_posix()


def _safe_backup_relative_path(relative_path: str) -> str:
    parts: list[str] = []
    for part in Path(relative_path).parts:
        if part in {"", "."}:
            continue
        if part == "..":
            parts.append("__up__")
            continue
        parts.append(part.replace(":", ""))
    return "/".join(parts) if parts else "__root__"



def _backup_file(project_root: Path, bundle_root: Path, target_path: Path) -> Dict[str, str | bool]:
    rel = _project_relative_path(project_root, target_path)
    backup_dir = bundle_root / "backup"
    backup_file = backup_dir / _safe_backup_relative_path(rel)

    existed = target_path.exists()
    if existed:
        ensure_parent_dir(backup_file)
        backup_file.write_text(target_path.read_text(encoding="utf-8"), encoding="utf-8")

    return {
        "relative_path": rel,
        "existed": existed,
        "backup_path": str(backup_file.relative_to(bundle_root)) if existed else "",
    }



def _apply_anchor_insert(original: str, anchor: str, snippet: str, mode: InsertMode) -> str:
    if snippet in original:
        return original

    lines = original.splitlines(keepends=True)
    for idx, line in enumerate(lines):
        if anchor in line:
            insert_line = snippet
            if not insert_line.endswith("\n"):
                insert_line += "\n"
            if mode == "after":
                lines.insert(idx + 1, insert_line)
            else:
                lines.insert(idx, insert_line)
            return "".join(lines)
    return original


def _deep_merge_mapping(base: Dict[str, Any], overlay: Mapping[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        if isinstance(value, Mapping) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge_mapping(merged[key], value)
        else:
            merged[key] = value
    return merged


def _render_json_merge(original: str, overlay: Mapping[str, Any]) -> str:
    parsed = json.loads(original) if original.strip() else {}
    if not isinstance(parsed, dict):
        raise ValueError("Structured JSON merge requires an object at the document root.")
    indent_match = next(
        (len(line) - len(line.lstrip(" ")) for line in original.splitlines()[1:] if line.startswith(" ")),
        2,
    )
    indent = indent_match if indent_match > 0 else 2
    newline = "\r\n" if "\r\n" in original else "\n"
    rendered = json.dumps(_deep_merge_mapping(parsed, overlay), indent=indent, ensure_ascii=False)
    return rendered.replace("\n", newline) + newline


def _render_structured_merge(op: PatchOp, original: str) -> str:
    if op.structured_format == "json":
        return _render_json_merge(original, op.merge)
    if op.structured_format == "xml":
        return render_maven_merge(original, op.merge)
    if op.structured_format == "gradle":
        return render_gradle_merge(original, op.merge, kotlin_dsl=op.path.endswith(".kts"))
    raise ValueError(
        f"No parser-backed structured patcher is registered for format '{op.structured_format or 'unspecified'}'."
    )



def apply_patch_operations(
    project_root: Path,
    operations: List[PatchOp],
    manifest_path: Path,
    patch_dir: Path,
    dry_run: bool,
    check_mode: bool,
    strict_conflict_mode: bool,
    description: str,
) -> ApplyResult:
    patch_id = _new_patch_id()
    touched_files: List[str] = []
    applied_ops = 0
    skipped_ops = 0
    issues: List[PatchIssue] = []

    manifest: ManifestState = load_manifest(manifest_path)

    bundle_root = patch_dir / patch_id
    backups: List[Dict[str, str | bool]] = []

    # Preflight operations whose safety can be established without writing.
    for op in operations:
        if op.kind == "anchor_insert":
            if not op.anchor or not op.snippet:
                issues.append(
                    PatchIssue(
                        code="CONFLICT_INVALID_ANCHOR_OP",
                        message="Anchor operation missing anchor or snippet.",
                        context={"path": op.path},
                    )
                )
                continue
            target = _resolve(project_root, op.path)
            report = check_anchor_exists(target, op.anchor)
            for conflict in report.conflicts:
                issues.append(
                    PatchIssue(
                        code=f"CONFLICT_{conflict.code}",
                        message=conflict.message,
                        context={k: str(v) for k, v in conflict.context.items()},
                    )
                )
        elif op.kind == "structured_merge":
            target = _resolve(project_root, op.path)
            if op.structured_format not in {"json", "xml", "gradle"}:
                issues.append(
                    PatchIssue(
                        code="CONFLICT_STRUCTURED_FORMAT_UNKNOWN",
                        message="Structured merge requires json, xml, or gradle format metadata.",
                        context={"path": op.path, "format": str(op.structured_format)},
                    )
                )
            else:
                try:
                    if target.exists():
                        original = target.read_text(encoding="utf-8")
                    elif op.structured_format == "json":
                        original = "{}\n"
                    else:
                        original = ""
                    _render_structured_merge(op, original)
                except (json.JSONDecodeError, ValueError, SyntaxError) as exc:
                    issues.append(
                        PatchIssue(
                            code="CONFLICT_STRUCTURED_DOCUMENT_INVALID",
                            message="Structured dependency document could not be parsed safely.",
                            context={"path": op.path, "format": op.structured_format, "error": str(exc)},
                        )
                    )

    if strict_conflict_mode and any(i.code.startswith("CONFLICT_") for i in issues):
        return ApplyResult(
            patch_id=patch_id,
            dry_run=dry_run or check_mode,
            touched_files=[],
            applied_ops=0,
            skipped_ops=len(operations),
            issues=issues,
        )

    for op in operations:
        target = _resolve(project_root, op.path)
        rel = _project_relative_path(project_root, target)

        if op.kind == "generated_file":
            new_content = op.content
            if target.exists() and target.read_text(encoding="utf-8") == new_content:
                skipped_ops += 1
                continue

            touched_files.append(rel)
            applied_ops += 1
            if dry_run or check_mode:
                continue

            backups.append(_backup_file(project_root, bundle_root, target))
            ensure_parent_dir(target)
            target.write_text(new_content, encoding="utf-8")
            set_entry(
                manifest,
                relative_path=rel,
                kind="generated_file",
                sha256=_sha256_text(new_content),
                patch_id=patch_id,
                metadata={"owner": op.owner},
            )

        elif op.kind == "anchor_insert":
            if not op.anchor or not op.snippet:
                skipped_ops += 1
                continue
            if not target.exists():
                skipped_ops += 1
                continue

            old_content = target.read_text(encoding="utf-8")
            new_content = _apply_anchor_insert(old_content, op.anchor, op.snippet, op.insert_mode)
            if new_content == old_content:
                skipped_ops += 1
                continue

            touched_files.append(rel)
            applied_ops += 1
            if dry_run or check_mode:
                continue

            backups.append(_backup_file(project_root, bundle_root, target))
            target.write_text(new_content, encoding="utf-8")
            set_entry(
                manifest,
                relative_path=rel,
                kind="anchor_insert",
                sha256=_sha256_text(new_content),
                patch_id=patch_id,
                metadata={"anchor": op.anchor, "snippet_hash": _sha256_text(op.snippet)},
            )

        elif op.kind == "delete_file":
            if not target.exists():
                skipped_ops += 1
                continue

            touched_files.append(rel)
            applied_ops += 1
            if dry_run or check_mode:
                continue

            backups.append(_backup_file(project_root, bundle_root, target))
            target.unlink(missing_ok=True)
            delete_entry(manifest, rel)

        elif op.kind == "structured_merge":
            if target.exists():
                old_content = target.read_text(encoding="utf-8")
            elif op.structured_format == "json":
                old_content = "{}\n"
            elif op.structured_format == "gradle":
                old_content = ""
            else:
                old_content = ""
            try:
                new_content = _render_structured_merge(op, old_content)
            except (json.JSONDecodeError, ValueError, SyntaxError):
                skipped_ops += 1
                continue
            if new_content == old_content:
                skipped_ops += 1
                continue

            touched_files.append(rel)
            applied_ops += 1
            if dry_run or check_mode:
                continue

            backups.append(_backup_file(project_root, bundle_root, target))
            ensure_parent_dir(target)
            target.write_text(new_content, encoding="utf-8", newline="")
            set_entry(
                manifest,
                relative_path=rel,
                kind="structured_merge",
                sha256=_sha256_text(new_content),
                patch_id=patch_id,
                metadata={"owner": op.owner, "format": op.structured_format},
            )

    if not (dry_run or check_mode):
        ensure_parent_dir(bundle_root)
        write_json(
            bundle_root / "meta.json",
            {
                "patch_id": patch_id,
                "created_at": utc_now_iso(),
                "description": description,
                "touched_files": touched_files,
                "backups": backups,
            },
        )
        append_patch_history(
            manifest,
            patch_id=patch_id,
            touched_files=touched_files,
            mode="apply",
            description=description,
        )
        save_manifest(manifest)

    return ApplyResult(
        patch_id=patch_id,
        dry_run=dry_run or check_mode,
        touched_files=touched_files,
        applied_ops=applied_ops,
        skipped_ops=skipped_ops,
        issues=issues,
    )



def list_patch_bundles(patch_dir: Path) -> List[str]:
    if not patch_dir.exists():
        return []
    return sorted([p.name for p in patch_dir.iterdir() if p.is_dir()])



def rollback_patch_bundle(project_root: Path, patch_dir: Path, patch_id: str) -> Dict[str, object]:
    bundle_root = patch_dir / patch_id
    meta_path = bundle_root / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Patch bundle meta not found: {meta_path}")

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    backups = meta.get("backups", [])

    restored: List[str] = []
    removed: List[str] = []

    for item in backups:
        rel = item["relative_path"]
        existed = bool(item["existed"])
        target = project_root / rel

        if existed:
            backup_rel = item["backup_path"]
            backup_file = bundle_root / backup_rel
            ensure_parent_dir(target)
            target.write_text(backup_file.read_text(encoding="utf-8"), encoding="utf-8")
            restored.append(rel)
        else:
            if target.exists():
                target.unlink(missing_ok=True)
                removed.append(rel)

    return {
        "patch_id": patch_id,
        "restored": restored,
        "removed": removed,
        "count": len(restored) + len(removed),
    }
