"""Shared, conservative frontend regeneration for every renderer.

Presentation is user-owned; schema and runtime files are generator-owned. A
stored hash is an overwrite permission, not merely an idempotency optimization.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping

from .manifest import load_manifest
from .patcher import PatchOp, apply_patch_operations


def customization_root(cfg: Mapping[str, Any], framework: str) -> str:
    frontend = cfg["frontend"]
    if frontend.get("customization_root"):
        return str(frontend["customization_root"])
    target = frontend if framework == "angular" else frontend[framework.replace("-", "_")]
    workspace = str(target.get("workspace_root", "frontend")).rstrip("/\\")
    return f"{workspace}/src/{'app/' if framework == 'angular' else ''}filterx-custom"


def _generated_root(cfg: Mapping[str, Any], framework: str) -> str:
    if framework == "angular":
        return str(cfg["frontend"]["generated_root"])
    target = cfg["frontend"][framework.replace("-", "_")]
    return f"{target['workspace_root'].rstrip('/')}/{target['generated_root'].strip('/')}"


def schema_from_scan(scan: Mapping[str, Any]) -> dict[str, Any]:
    return {entity["model"]: {
        "table": entity.get("table"),
        "fields": {field["name"]: {"type": field.get("type"), "nullable": field.get("nullable", False),
                                     "operations": field.get("ops", []), "enum_values": field.get("enum_values", [])}
                   for field in entity.get("fields", [])},
        "relationships": {rel["name"]: {key: rel.get(key) for key in ("related_model", "uselist", "cardinality")}
                          for rel in entity.get("relationships", [])},
    } for entity in scan.get("entities", [])}


def schema_from_ir(ir: Any) -> dict[str, Any]:
    return {entity.name: {
        "table": entity.identity.table,
        "fields": {field.name: {"type": field.type.value, "nullable": field.nullable,
                                  "operations": list(field.operations), "enum_values": list(field.enum_values)}
                   for field in entity.fields},
        "relationships": {rel.name: json.loads(json.dumps(asdict(rel))) for rel in entity.relationships},
    } for entity in ir.entities}


def _presentation(project_root: Path, cfg: Mapping[str, Any], framework: str,
                  schema: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    path = project_root / customization_root(cfg, framework) / "presentation.json"
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    if not isinstance(data, dict):
        raise ValueError("presentation.json must contain an entity-to-presentation object")
    cleaned: dict[str, Any] = {}
    warnings: list[dict[str, str]] = []
    for entity, settings in data.items():
        if not isinstance(settings, dict) or set(settings) - {"label", "columns", "labels"}:
            raise ValueError(f"Presentation for {entity} accepts only label, columns and labels; query overrides are forbidden")
        if "label" in settings and not isinstance(settings["label"], str):
            raise ValueError(f"Presentation label for {entity} must be a string")
        if "columns" in settings and (not isinstance(settings["columns"], list) or
                                       any(not isinstance(value, str) for value in settings["columns"])):
            raise ValueError(f"Presentation columns for {entity} must be a list of strings")
        labels = settings.get("labels", {})
        if not isinstance(labels, dict) or any(not isinstance(value, str) for value in labels.values()):
            raise ValueError(f"Presentation labels for {entity} must map field names to strings")
        if entity not in schema:
            warnings.append({"code": "PRESENTATION_ENTITY_REMOVED", "entity": entity})
            continue
        fields = schema[entity]["fields"]
        unknown = (set(settings.get("columns", [])) | set(labels)) - set(fields)
        for name in sorted(unknown):
            warnings.append({"code": "PRESENTATION_FIELD_REMOVED", "entity": entity, "field": name})
        result = {"label": settings["label"]} if "label" in settings else {}
        if "columns" in settings:
            result["columns"] = list(dict.fromkeys(name for name in settings["columns"] if name in fields))
        if "labels" in settings:
            result["labels"] = {name: label for name, label in labels.items() if name in fields}
        cleaned[entity] = result
    return cleaned, warnings


def presentation_operations(project_root: Path, cfg: Mapping[str, Any], framework: str,
                            schema: dict[str, Any]) -> list[PatchOp]:
    data, _ = _presentation(project_root, cfg, framework, schema)
    # JSON.parse avoids JavaScript object-literal __proto__ semantics. No source
    # from a user-owned file is evaluated or interpolated as executable code.
    literal = json.dumps(json.dumps(data, ensure_ascii=True), ensure_ascii=True)
    content = ("// Generated display-only projection. Edit the user-owned presentation.json.\n"
               "export const FILTERX_PRESENTATION: Record<string, {label?: string; columns?: string[]; labels?: Record<string, string>}> = JSON.parse("
               + literal + ");\n")
    return [PatchOp(kind="generated_file", path=f"{customization_root(cfg, framework)}/presentation.json",
                    content="{}\n", owner="host", write_policy="create_once", metadata={"layer": "custom"}),
            PatchOp(kind="generated_file", path=f"{_generated_root(cfg, framework)}/presentation.ts",
                    content=content, metadata={"layer": "schema"})]


def _hash(text: str) -> str:
    # Older manifests used read_text/write_text with universal newlines.
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def _read(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


_ROUTES = re.compile(r"// FILTERX GENERATED ROUTES START.*?// FILTERX GENERATED ROUTES END", re.DOTALL)


def schema_changes(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for name in sorted(set(before) | set(after)):
        if name not in before or name not in after:
            changes.append({"entity": name, "kind": "entity_added" if name in after else "entity_removed",
                            "breaking": name not in after})
            continue
        for category in ("fields", "relationships"):
            old, new = before[name].get(category, {}), after[name].get(category, {})
            for key in sorted(set(old) | set(new)):
                if key not in old or key not in new or old[key] != new[key]:
                    changes.append({"entity": name, "member": key, "category": category,
                                    "kind": "added" if key not in old else "removed" if key not in new else "changed",
                                    "breaking": key in old})
        if before[name].get("table") != after[name].get("table"):
            changes.append({"entity": name, "kind": "table_changed", "breaking": True})
    return changes


def finish_frontend_install(args: Any, cfg: dict[str, Any], operations: list[PatchOp],
                            schema: dict[str, Any], payload: dict[str, Any]) -> int:
    root = Path(args.project_root).resolve()
    framework = payload["framework"]
    manifest_path = root / cfg["safety"]["idempotency_manifest"]
    entries = load_manifest(manifest_path).data["entries"]
    state_path = f".filterx/frontend-{framework}.json"
    state_file = root / state_path
    state = json.loads(_read(state_file)) if state_file.exists() else {}
    previous = state.get("files", {})
    issues: list[dict[str, Any]] = []
    layout = {"generated_root": _generated_root(cfg, framework), "customization_root": customization_root(cfg, framework)}
    if state.get("layout") and state["layout"] != layout:
        issues.append({"code": "CONFLICT_FRONTEND_LAYOUT_CHANGED", "message": "Existing user shells import the installed runtime. Restore the previous paths or migrate those imports and ownership state explicitly before changing layout."})
    generated, custom = ((root / layout[key]).resolve() for key in ("generated_root", "customization_root"))
    if generated.is_relative_to(custom) or custom.is_relative_to(generated):
        issues.append({"code": "CONFLICT_FRONTEND_ROOTS_OVERLAP", "message": "Generated and customization roots must be separate sibling trees."})
    files: dict[str, Any] = {}
    planned = list(operations)
    include_diff = getattr(args, "frontend_command", "") == "diff" or getattr(args, "verbose", False)
    desired_paths = {str((root / op.path).resolve()) for op in operations}
    if len(desired_paths) != len(operations):
        issues.append({"code": "CONFLICT_FRONTEND_DUPLICATE_PATH", "message": "Multiple generated/custom operations target the same file. Separate the configured paths."})
    # Only prune files recorded as generated by a previous successful frontend
    # install. Never infer ownership from a directory name or delete user files.
    for rel, info in previous.items():
        if info.get("owner") == "filterx-generated" and info.get("write_policy") != "create_once" and str((root / rel).resolve()) not in desired_paths:
            planned.append(PatchOp(kind="delete_file", path=rel, metadata=info))

    changes = []
    for op in planned:
        path = (root / op.path).resolve()
        if not path.is_relative_to(root):
            issues.append({"code": "CONFLICT_FRONTEND_PATH_OUTSIDE_PROJECT", "path": op.path})
            continue
        rel = path.relative_to(root).as_posix()
        if op.kind != "delete_file":
            files[rel] = {**previous.get(rel, {}), "owner": op.owner, "write_policy": op.write_policy, **op.metadata}
        if op.write_policy == "create_once" and path.exists():
            changes.append({"path": rel, "action": "preserve", "layer": "custom"})
            continue
        old = _read(path) if path.exists() else ""
        new = op.content if op.kind == "generated_file" else "" if op.kind == "delete_file" else None
        entry = entries.get(rel, {})
        baseline = entry.get("sha256")
        if path.exists() and op.owner == "filterx-generated":
            # Even if a template happens to match a manual edit, require an
            # explicit resolution instead of silently adopting the edited core.
            conflict = _hash(old) != baseline if baseline else (new != old)
            if conflict:
                issues.append({"code": "CONFLICT_FRONTEND_MODIFIED", "path": rel,
                               "message": "Managed file differs from its installed baseline. Move customization to the shell/theme, then restore or merge this file before reinstalling."})
        # Host edits outside the route block are allowed. The managed block is
        # checked independently so route guards inside it cannot vanish silently.
        if op.owner == "host" and op.kind == "generated_file" and op.write_policy != "create_once":
            block = _ROUTES.search(old)
            old_block = previous.get(rel, {}).get("route_hash")
            if block and not old_block and baseline and _hash(old) != baseline:
                issues.append({"code": "CONFLICT_FRONTEND_LEGACY_ROUTE_MODIFIED", "path": rel,
                               "message": "Legacy route file has local edits and no block-level baseline. Review/restore the installed route block before migrating."})
            if old_block and _hash(block.group(0) if block else "") != old_block:
                issues.append({"code": "CONFLICT_FRONTEND_ROUTE_BLOCK_MODIFIED", "path": rel})
            next_block = _ROUTES.search(op.content)
            if next_block:
                files[rel]["route_hash"] = _hash(next_block.group(0))
            else:
                files[rel].pop("route_hash", None)
        if new is not None:
            action = "unchanged" if old == new and path.exists() else "delete" if op.kind == "delete_file" else "update" if path.exists() else "create"
            if op.kind == "delete_file" and not path.exists():
                action = "unchanged"
            changes.append({"path": rel, "action": action, "layer": op.metadata.get("layer", "host"),
                            "diff": "".join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), fromfile=rel, tofile=rel)) if include_diff and action != "unchanged" else ""})
        else:
            changes.append({"path": rel, "action": "reconcile", "layer": "host"})

    _, warnings = _presentation(root, cfg, framework, schema)
    payload = {**payload, "schema_changes": schema_changes(state.get("schema", {}), schema),
               "changes": changes, "issues": issues, "warnings": payload.get("warnings", []) + warnings}
    diagnostic = getattr(args, "frontend_command", "install") in {"diff", "doctor"}
    dry_run = diagnostic or bool(getattr(args, "check", False))
    configured_dry = getattr(args, "dry_run", None)
    dry_run = dry_run or bool(cfg["safety"].get("dry_run_default", True) if configured_dry is None else configured_dry)
    payload["dry_run"] = dry_run
    payload["ok"] = not issues
    if issues or (getattr(args, "fail_on_warning", False) and payload["warnings"]):
        code = 3
    else:
        # Retain skipped host/custom entries for future ownership checks, never
        # retain removed generator files. This snapshot is itself rollbackable.
        for rel, info in previous.items():
            if info.get("owner") == "host" and rel not in files:
                files[rel] = info
        state_content = json.dumps({"version": 1, "framework": framework, "layout": layout, "schema": schema, "files": files}, indent=2, sort_keys=True) + "\n"
        planned.append(PatchOp(kind="generated_file", path=state_path, content=state_content))
        result = apply_patch_operations(root, planned, manifest_path, root / cfg["output"]["patch_dir"],
                                        dry_run, False, True, f"frontend.install.{framework}")
        payload.update(patch_id=result.patch_id, touched_files=result.touched_files,
                       applied_ops=result.applied_ops, skipped_ops=result.skipped_ops)
        payload["issues"].extend({"code": issue.code, "message": issue.message, **issue.context} for issue in result.issues)
        code = 3 if result.has_conflicts else 0
    payload["ok"] = code == 0
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2))
    else:
        print(f"FilterX {framework} frontend {'preview' if dry_run else 'install'}: {'blocked' if code else 'ready'}")
        for item in changes:
            if item["action"] != "unchanged":
                print(f"  {item['action']}: {item['path']}")
                if getattr(args, "frontend_command", "") == "diff":
                    print(item.get("diff", ""), end="")
        for item in payload["issues"] + payload["warnings"] + payload["schema_changes"]:
            print(json.dumps(item))
    return code