from __future__ import annotations

import json
from pprint import pformat
from pathlib import Path
from typing import Any

from filterx.core.config import load_effective_config
from filterx.core.manifest import load_manifest
from filterx.core.patcher import PatchOp, apply_patch_operations, rollback_patch_bundle


def _resolve_dry_run(args: Any, cfg: dict[str, Any]) -> bool:
    dry_run = getattr(args, "dry_run", None)
    if dry_run is None:
        return bool(cfg["safety"].get("dry_run_default", True))
    return bool(dry_run)


def _py_module_path(path_like: str) -> str:
    return Path(path_like).as_posix().strip("/").replace("/", ".")


def _render_copilot_router_py(api_prefix: str, scan_file: str, agent_config: dict[str, Any], session_dependency_import: str) -> str:
    escaped_prefix = api_prefix.replace("\\", "\\\\").replace('"', '\\"')
    escaped_scan_file = scan_file.replace("\\", "\\\\").replace('"', '\\"')
    escaped_session = session_dependency_import.replace("\\", "\\\\").replace('"', '\\"')
    agent_literal = pformat(agent_config, width=100)
    return (
        "from __future__ import annotations\n\n"
        "import importlib\n"
        "from pathlib import Path\n\n"
        "from app.filterx_generated.entities import ENTITIES\n"
        "from app.generics.query_executor import GenericQueryExecutor\n"
        "from app.schema.filter_node import FilterNode\n"
        "from app.schema.pagination import GenericPaginationParams\n"
        "from filterx.agent import create_copilot_router\n\n"
        f"API_PREFIX = \"{escaped_prefix}\"\n"
        f"SCAN_FILE = Path(\"{escaped_scan_file}\")\n"
        f"SESSION_DEPENDENCY_IMPORT = \"{escaped_session}\"\n"
        f"AGENT_CONFIG = {agent_literal}\n\n"
        "def _import_object(import_path: str) -> object:\n"
        "    module_name, obj_name = import_path.split(\":\", 1)\n"
        "    module = importlib.import_module(module_name)\n"
        "    return getattr(module, obj_name)\n\n"
        "router = create_copilot_router(\n"
        "    api_prefix=API_PREFIX,\n"
        "    entities=ENTITIES,\n"
        "    scan_file=SCAN_FILE,\n"
        "    agent_config=AGENT_CONFIG,\n"
        "    session_dependency=_import_object(SESSION_DEPENDENCY_IMPORT),\n"
        "    query_executor_cls=GenericQueryExecutor,\n"
        "    pagination_cls=GenericPaginationParams,\n"
        "    filter_node_cls=FilterNode,\n"
        ")\n"
    )


def _build_patch_ops(cfg: dict[str, Any], include_mount: bool) -> list[PatchOp]:
    agent_cfg = cfg["agent"]
    generated_file = str(agent_cfg.get("generated_file", "app/filterx_generated/copilot_router.py"))
    generated_module = _py_module_path(generated_file.removesuffix(".py"))
    operations = [
        PatchOp(
            kind="generated_file",
            path=generated_file,
            content=_render_copilot_router_py(
                api_prefix=str(cfg["backend"].get("api_prefix", "/api")),
                scan_file=str(cfg["output"].get("scan_file", ".filterx/scan.json")),
                agent_config=agent_cfg,
                session_dependency_import=str(cfg["python"]["session_dependency_import"]),
            ),
            description="FilterX copilot generated router",
        )
    ]
    if include_mount:
        snippet = (
            f"from {generated_module} import router as filterx_copilot_router\n"
            "app.include_router(filterx_copilot_router)"
        )
        operations.append(
            PatchOp(
                kind="anchor_insert",
                path=str(agent_cfg.get("mount_file", "app/main.py")),
                anchor=str(agent_cfg.get("mount_anchor", "# FILTERX:COPILOT_MOUNT")),
                snippet=snippet,
                insert_mode="after",
                owner="host",
                description="Mount generated FilterX copilot router",
            )
        )
    return operations


def run_install(args: Any) -> int:
    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config).resolve() if args.config else None
    effective = load_effective_config(project_root, config_path)
    cfg = effective.raw

    dry_run = _resolve_dry_run(args, cfg)
    check_mode = bool(getattr(args, "check", False))
    strict_conflict_mode = bool(cfg["safety"].get("strict_conflict_mode", True))
    operations = _build_patch_ops(cfg, include_mount=not bool(getattr(args, "no_mount", False)))

    result = apply_patch_operations(
        project_root=project_root,
        operations=operations,
        manifest_path=project_root / cfg["safety"]["idempotency_manifest"],
        patch_dir=project_root / cfg["output"]["patch_dir"],
        dry_run=dry_run,
        check_mode=check_mode,
        strict_conflict_mode=strict_conflict_mode,
        description="copilot.install",
    )
    payload = {
        "dry_run": result.dry_run,
        "check_mode": check_mode,
        "patch_id": result.patch_id,
        "generated_file": str(cfg["agent"].get("generated_file", "app/filterx_generated/copilot_router.py")),
        "touched_files": result.touched_files,
        "applied_ops": result.applied_ops,
        "skipped_ops": result.skipped_ops,
        "issues": [issue.__dict__ for issue in result.issues],
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("FilterX copilot install completed.")
        print(f"- Dry run: {payload['dry_run']}")
        print(f"- Patch ID: {payload['patch_id']}")
        print(f"- Applied ops: {payload['applied_ops']}")
        print(f"- Skipped ops: {payload['skipped_ops']}")
    if result.has_conflicts:
        return 3
    return 0


def run_validate(args: Any) -> int:
    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config).resolve() if args.config else None
    effective = load_effective_config(project_root, config_path)
    cfg = effective.raw
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    generated_file = project_root / str(cfg["agent"].get("generated_file", "app/filterx_generated/copilot_router.py"))
    if not generated_file.exists():
        errors.append({"code": "COPILOT_GENERATED_FILE_MISSING", "path": str(generated_file)})
    mount_file = project_root / str(cfg["agent"].get("mount_file", "app/main.py"))
    mount_anchor = str(cfg["agent"].get("mount_anchor", "# FILTERX:COPILOT_MOUNT"))
    if not mount_file.exists():
        errors.append({"code": "COPILOT_MOUNT_FILE_MISSING", "path": str(mount_file)})
    else:
        content = mount_file.read_text(encoding="utf-8")
        if mount_anchor not in content:
            warnings.append({"code": "COPILOT_MOUNT_ANCHOR_NOT_FOUND", "path": str(mount_file), "anchor": mount_anchor})
        if "filterx_copilot_router" not in content:
            warnings.append({"code": "COPILOT_MOUNT_SNIPPET_NOT_FOUND", "path": str(mount_file)})
    payload = {"errors": errors, "warnings": warnings, "error_count": len(errors), "warning_count": len(warnings)}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("FilterX copilot validation completed.")
        print(f"- Errors: {payload['error_count']}")
        print(f"- Warnings: {payload['warning_count']}")
    if errors:
        return 4
    if getattr(args, "fail_on_warning", False) and warnings:
        return 3
    return 0


def run_remove(args: Any) -> int:
    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config).resolve() if args.config else None
    effective = load_effective_config(project_root, config_path)
    cfg = effective.raw
    manifest = load_manifest(project_root / cfg["safety"]["idempotency_manifest"])
    generated_file = str(cfg["agent"].get("generated_file", "app/filterx_generated/copilot_router.py"))
    entry = manifest.data.get("entries", {}).get(generated_file)
    patch_id = getattr(args, "patch_id", None) or (entry or {}).get("last_patch_id")
    if not patch_id:
        payload = {"removed": False, "reason": "copilot patch not found"}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print("FilterX copilot remove skipped: no copilot patch found.")
        return 0
    result = rollback_patch_bundle(project_root, project_root / cfg["output"]["patch_dir"], str(patch_id))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"FilterX copilot remove completed via rollback: {patch_id}")
        print(f"- Restored files: {len(result['restored'])}")
        print(f"- Removed files: {len(result['removed'])}")
    return 0
