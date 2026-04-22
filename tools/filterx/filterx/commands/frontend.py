from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from filterx.core.config import load_effective_config
from filterx.core.io import load_json
from filterx.core.patcher import (
    PatchOp,
    apply_patch_operations,
    list_patch_bundles,
    rollback_patch_bundle,
)


def _resolve_dry_run(args: Any, cfg: dict[str, Any]) -> bool:
    dry_run = getattr(args, "dry_run", None)
    if dry_run is None:
        return bool(cfg["safety"].get("dry_run_default", True))
    return bool(dry_run)


def _csv_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _to_snake(value: str) -> str:
    out = []
    for idx, char in enumerate(value):
        if char.isupper() and idx > 0 and (value[idx - 1].islower() or (idx + 1 < len(value) and value[idx + 1].islower())):
            out.append("_")
        out.append(char.lower())
    return "".join(out).replace("__", "_")


def _to_kebab(value: str) -> str:
    return _to_snake(value).replace("_", "-")


def _to_camel(value: str) -> str:
    snake = _to_snake(value)
    parts = [p for p in snake.split("_") if p]
    if not parts:
        return ""
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


def _styled_name(value: str, style: str) -> str:
    if style == "snake":
        return _to_snake(value)
    if style == "camel":
        return _to_camel(value)
    return _to_kebab(value)


def _to_pascal(value: str) -> str:
    normalized = _to_snake(value)
    return "".join(part.capitalize() for part in normalized.split("_") if part)


def _ts_field_type(field_type: str) -> str:
    if field_type in {"integer", "float"}:
        return "number"
    if field_type == "boolean":
        return "boolean"
    return "string"


def _ui_field_type(field_type: str) -> str:
    if field_type in {"integer", "float"}:
        return "number"
    if field_type == "boolean":
        return "boolean"
    if field_type in {"date", "datetime"}:
        return "date"
    return "text"


def _extract_existing_route_paths(routes_file: Path) -> set[str]:
    if not routes_file.exists():
        return set()
    content = routes_file.read_text(encoding="utf-8")
    matches = re.findall(r"path\s*:\s*['\"]([^'\"]+)['\"]", content)
    out = set()
    for match in matches:
        if match and match != "**":
            out.add(match.rstrip("/"))
    return out


def _build_entity_config_ts(entity: dict[str, Any], style: str) -> tuple[str, str]:
    model_name = str(entity.get("model", "Entity"))
    interface_name = _to_pascal(model_name)
    config_name = f"{_to_snake(model_name).upper()}_GENERATED_CONFIG"
    api_name = _styled_name(model_name, style)

    fields = list(entity.get("fields", []))
    field_lines = []
    interface_lines = []
    column_lines = []
    for field in fields:
        name = str(field.get("name", "field"))
        ts_type = _ts_field_type(str(field.get("type", "string")))
        ui_type = _ui_field_type(str(field.get("type", "string")))
        interface_lines.append(f"  '{name}': {ts_type};")
        field_lines.append(f"    createFieldConfig('{name}', '{name.replace('_', ' ').title()}', '{ui_type}'),")
        column_lines.append(f"    createColumnConfig<{interface_name}>('{name}', '{name.replace('_', ' ').title()}'),")

    content = (
        "import { SortOrder } from '../../core/enums/sort-order.enum';\n"
        "import {\n"
        "  EntityConfig,\n"
        "  createFieldConfig,\n"
        "  createColumnConfig,\n"
        "} from '../../core/interfaces/entity-config.interface';\n\n"
        f"export interface {interface_name} {{\n"
        + "\n".join(interface_lines)
        + "\n}\n\n"
        f"export const {config_name}: EntityConfig<{interface_name}> = {{\n"
        f"  name: '{interface_name}',\n"
        f"  pluralLabel: '{interface_name}s',\n"
        f"  singularLabel: '{interface_name}',\n"
        f"  apiEndpoint: '/api/{api_name}s',\n"
        f"  searchPlaceholder: 'Search {interface_name.lower()}...',\n"
        f"  emptyMessage: 'No {interface_name.lower()} records found',\n"
        "  defaults: {\n"
        "    pageSize: 20,\n"
        "    sortField: 'id',\n"
        "    sortOrder: SortOrder.ASC,\n"
        "    pageSizeOptions: [10, 20, 50],\n"
        "  },\n"
        "  fields: [\n"
        + "\n".join(field_lines)
        + "\n  ],\n"
        "  columns: [\n"
        + "\n".join(column_lines)
        + "\n  ],\n"
        "};\n"
    )
    return f"{_styled_name(model_name, style)}.config.ts", content


def _build_route_entry(entity: dict[str, Any], project_root: Path, frontend_root: str, style: str) -> tuple[str, str, str] | None:
    model_name = str(entity.get("model", "Entity"))
    model_slug = _styled_name(model_name, style)
    table_name = str(entity.get("table", f"{model_slug}s")).replace("_", "-")
    route_path = table_name.rstrip("/")

    feature_dir = route_path.replace("-", "_").replace("/", "")
    component_file = (
        project_root
        / frontend_root
        / "src"
        / "app"
        / "features"
        / feature_dir
        / f"{model_slug}-list-new.component.ts"
    )
    if not component_file.exists():
        return None

    class_name = f"{_to_pascal(model_slug)}ListComponent"
    generated_entry = (
        "  {\n"
        f"    path: '{route_path}',\n"
        "    loadComponent: () =>\n"
        f"      import('../features/{feature_dir}/{model_slug}-list-new.component').then((m) => m.{class_name}),\n"
        f"    title: '{_to_pascal(model_slug)} - FilterX Generated',\n"
        "  },"
    )
    host_entry = (
        "  {\n"
        f"    path: '{route_path}',\n"
        "    loadComponent: () =>\n"
        f"      import('./features/{feature_dir}/{model_slug}-list-new.component').then((m) => m.{class_name}),\n"
        f"    title: '{_to_pascal(model_slug)} - FilterX Generated',\n"
        "  },"
    )
    return route_path, generated_entry, host_entry


def _run_install_impl(args: Any) -> int:
    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config).resolve() if args.config else None
    effective = load_effective_config(project_root, config_path)
    cfg = effective.raw

    if not cfg["frontend"].get("enabled", True):
        if args.json:
            print(json.dumps({"skipped": True, "reason": "frontend disabled in config"}, indent=2))
        else:
            print("FilterX frontend install skipped: frontend.enabled is false.")
        return 0

    dry_run = _resolve_dry_run(args, cfg)
    check_mode = bool(getattr(args, "check", False))
    strict_conflict_mode = bool(cfg["safety"].get("strict_conflict_mode", True))

    scan_path = project_root / cfg["output"]["scan_file"]
    if not scan_path.exists():
        payload = {
            "errors": [
                {
                    "code": "SCAN_FILE_MISSING",
                    "path": str(scan_path),
                    "message": "Run 'filterx scan' before frontend install.",
                }
            ]
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print("FilterX frontend install failed: scan artifact is missing.")
        return 2

    style = str(getattr(args, "style", None) or cfg["frontend"].get("entity_style", "kebab"))
    frontend_root = str(cfg["frontend"].get("workspace_root", "frontend"))
    generated_root = str(cfg["frontend"]["generated_root"])
    routes_file = str(getattr(args, "routes_file", None) or cfg["frontend"]["routes_file"])
    routes_anchor = str(getattr(args, "routes_anchor", None) or cfg["frontend"]["routes_anchor"])
    include_route_patch = not bool(getattr(args, "no_route_patch", False))

    scan_payload = load_json(scan_path)
    entities = list(scan_payload.get("entities", []))
    allow = set(_csv_list(getattr(args, "entities", None)))
    if allow:
        entities = [entity for entity in entities if entity.get("model") in allow]

    root = Path(generated_root).as_posix().rstrip("/")
    ops: list[PatchOp] = []

    entity_export_lines = []
    for entity in entities:
        file_name, file_content = _build_entity_config_ts(entity, style)
        model_name = str(entity.get("model", "Entity"))
        export_name = f"{_to_snake(model_name).upper()}_GENERATED_CONFIG"
        entity_export_lines.append(f"export {{ {export_name} }} from './{file_name[:-3]}';")
        ops.append(
            PatchOp(
                kind="generated_file",
                path=f"{root}/entities/{file_name}",
                content=file_content,
                description=f"Generated frontend entity config for {model_name}",
            )
        )

    generated_routes_entries: list[str] = []
    host_routes_entries: list[str] = []
    existing_paths = _extract_existing_route_paths(project_root / routes_file)
    for entity in entities:
        route_data = _build_route_entry(entity, project_root, frontend_root, style)
        if route_data is None:
            continue
        route_path, generated_route_entry, host_route_entry = route_data
        if route_path in existing_paths:
            continue
        generated_routes_entries.append(generated_route_entry)
        host_routes_entries.append(host_route_entry)

    routes_ts = (
        "import { Routes } from '@angular/router';\n\n"
        "export const FILTERX_GENERATED_ROUTES: Routes = [\n"
        + ("\n".join(generated_routes_entries) if generated_routes_entries else "")
        + "\n];\n"
    )
    ops.extend(
        [
            PatchOp(
                kind="generated_file",
                path=f"{root}/routes.ts",
                content=routes_ts,
                description="Generated frontend route entries",
            ),
            PatchOp(
                kind="generated_file",
                path=f"{root}/entities/index.ts",
                content=("\n".join(entity_export_lines) + "\n") if entity_export_lines else "",
                description="Generated frontend entities index",
            ),
            PatchOp(
                kind="generated_file",
                path=f"{root}/index.ts",
                content="export * from './routes';\nexport * from './entities';\n",
                description="Generated frontend root index",
            ),
            PatchOp(
                kind="generated_file",
                path=f"{root}/services/filterx-entity-query.service.ts",
                content="export { EntityQueryService as FilterxEntityQueryService } from '../../core/services/entity-query.service';\n",
                description="Generated frontend query service alias",
            ),
        ]
    )

    if include_route_patch and host_routes_entries:
        snippet = "// FILTERX GENERATED ROUTES START\n" + "\n".join(host_routes_entries) + "\n// FILTERX GENERATED ROUTES END"
        ops.append(
            PatchOp(
                kind="anchor_insert",
                path=routes_file,
                anchor=routes_anchor,
                snippet=snippet,
                insert_mode="after",
                owner="host",
                description="Insert generated routes into app.routes.ts",
            )
        )

    manifest_path = project_root / cfg["safety"]["idempotency_manifest"]
    patch_dir = project_root / cfg["output"]["patch_dir"]
    result = apply_patch_operations(
        project_root=project_root,
        operations=ops,
        manifest_path=manifest_path,
        patch_dir=patch_dir,
        dry_run=dry_run,
        check_mode=check_mode,
        strict_conflict_mode=strict_conflict_mode,
        description="frontend.install",
    )

    payload = {
        "dry_run": result.dry_run,
        "check_mode": check_mode,
        "patch_id": result.patch_id,
        "generated_root": str((project_root / generated_root).resolve()),
        "entity_count": len(entities),
        "generated_route_count": len(host_routes_entries),
        "touched_files": result.touched_files,
        "applied_ops": result.applied_ops,
        "skipped_ops": result.skipped_ops,
        "issues": [
            {"code": issue.code, "message": issue.message, "context": issue.context}
            for issue in result.issues
        ],
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("FilterX frontend install completed.")
        print(f"- Dry run: {payload['dry_run']}")
        print(f"- Applied ops: {payload['applied_ops']}")
        print(f"- Skipped ops: {payload['skipped_ops']}")

    if result.has_conflicts:
        return 3
    if getattr(args, "fail_on_warning", False) and result.issues:
        return 3
    return 0


def _frontend_remove_candidates(patch_dir: Path) -> list[str]:
    candidates: list[str] = []
    for patch_id in list_patch_bundles(patch_dir):
        meta_path = patch_dir / patch_id / "meta.json"
        if not meta_path.exists():
            continue
        try:
            meta = load_json(meta_path)
        except Exception:
            continue
        if meta.get("description") == "frontend.install":
            candidates.append(patch_id)
    return candidates


def run_install(args: Any) -> int:
    return _run_install_impl(args)


def run_validate(args: Any) -> int:
    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config).resolve() if args.config else None
    effective = load_effective_config(project_root, config_path)
    cfg = effective.raw

    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    root = Path(cfg["frontend"]["generated_root"]).as_posix().rstrip("/")
    required = [
        f"{root}/index.ts",
        f"{root}/routes.ts",
        f"{root}/entities/index.ts",
        f"{root}/services/filterx-entity-query.service.ts",
    ]
    for rel in required:
        if not (project_root / rel).exists():
            errors.append({"code": "FRONTEND_GENERATED_FILE_MISSING", "path": str(project_root / rel)})

    routes_file = project_root / cfg["frontend"]["routes_file"]
    routes_anchor = cfg["frontend"]["routes_anchor"]
    if not routes_file.exists():
        errors.append({"code": "FRONTEND_ROUTES_FILE_MISSING", "path": str(routes_file)})
    else:
        content = routes_file.read_text(encoding="utf-8")
        if routes_anchor not in content:
            warnings.append(
                {
                    "code": "FRONTEND_ROUTES_ANCHOR_NOT_FOUND",
                    "path": str(routes_file),
                    "anchor": routes_anchor,
                }
            )

    payload = {
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings),
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("FilterX frontend validation completed.")
        print(f"- Errors: {payload['error_count']}")
        print(f"- Warnings: {payload['warning_count']}")

    if payload["errors"]:
        return 4
    if getattr(args, "fail_on_warning", False) and payload["warnings"]:
        return 3
    return 0


def run_remove(args: Any) -> int:
    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config).resolve() if args.config else None
    effective = load_effective_config(project_root, config_path)
    cfg = effective.raw

    patch_dir = project_root / cfg["output"]["patch_dir"]
    candidates = _frontend_remove_candidates(patch_dir)

    if getattr(args, "list", False):
        payload = {"patch_dir": str(patch_dir), "frontend_install_patches": candidates}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print("Available frontend remove patch bundles:")
            if not candidates:
                print("- (none)")
            for patch_id in candidates:
                print(f"- {patch_id}")
        return 0

    if not candidates:
        print("No frontend install patch bundles available for rollback.")
        return 2

    patch_id = getattr(args, "patch_id", None) or candidates[-1]
    if patch_id not in candidates:
        print(f"Frontend patch id '{patch_id}' not found.")
        return 2

    dry_run = _resolve_dry_run(args, cfg)
    check_mode = bool(getattr(args, "check", False))
    if dry_run or check_mode:
        payload = {
            "dry_run": True,
            "check_mode": check_mode,
            "would_rollback_patch_id": patch_id,
            "patch_dir": str(patch_dir),
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print("FilterX frontend remove preview.")
            print(f"- Patch ID: {patch_id}")
        return 0

    result = rollback_patch_bundle(project_root, patch_dir, patch_id)
    payload = {
        "patch_id": patch_id,
        "restored": result.get("restored", []),
        "removed": result.get("removed", []),
        "count": result.get("count", 0),
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"FilterX frontend remove completed for patch: {patch_id}")
        print(f"- Restored files: {len(payload['restored'])}")
        print(f"- Removed files: {len(payload['removed'])}")

    return 0
