from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from filterx.core.config import load_effective_config
from filterx.core.conflicts import check_route_path_conflicts
from filterx.core.io import load_json
from filterx.core.patcher import PatchOp, apply_patch_operations

from ._stub import run_stub


def _resolve_dry_run(args: Any, cfg: dict[str, Any]) -> bool:
    dry_run = getattr(args, "dry_run", None)
    if dry_run is None:
        return bool(cfg["safety"].get("dry_run_default", True))
    return bool(dry_run)


def _csv_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _filter_entities(scan_entities: list[dict[str, Any]], cfg: dict[str, Any], args: Any) -> list[dict[str, Any]]:
    allow = set(_csv_list(getattr(args, "entities", None)) or (cfg["backend"].get("entities") or []))
    deny = set(cfg["backend"].get("exclude_entities") or [])

    selected: list[dict[str, Any]] = []
    for entity in scan_entities:
        model = entity.get("model")
        if allow and model not in allow:
            continue
        if model in deny:
            continue
        selected.append(entity)
    return selected


def _py_module_path(path_like: str) -> str:
    return Path(path_like).as_posix().strip("/").replace("/", ".")


def _to_filterx_base_path(api_prefix: str) -> str:
    prefix = api_prefix.strip() or "/api"
    if not prefix.startswith("/"):
        prefix = f"/{prefix}"
    if prefix != "/":
        prefix = prefix.rstrip("/")
    else:
        prefix = ""
    return f"{prefix}/filterx"


def _render_entities_py(entities: list[dict[str, Any]]) -> str:
    compact_entities: list[dict[str, Any]] = []
    for entity in entities:
        compact_entities.append(
            {
                "model": entity.get("model"),
                "table": entity.get("table"),
                "primary_keys": entity.get("primary_keys", []),
                "fields": [
                    {
                        "name": field.get("name"),
                        "type": field.get("type"),
                        "ops": field.get("ops", []),
                    }
                    for field in entity.get("fields", [])
                ],
                "relationships": [
                    {
                        "name": rel.get("name"),
                        "related_model": rel.get("related_model"),
                        "cardinality": rel.get("cardinality"),
                    }
                    for rel in entity.get("relationships", [])
                ],
            }
        )

    payload = json.dumps(compact_entities, indent=2)
    return (
        "from __future__ import annotations\n\n"
        "import json\n\n"
        f"_ENTITIES_JSON = '''{payload}'''\n"
        "ENTITIES = json.loads(_ENTITIES_JSON)\n"
    )


def _render_metadata_py() -> str:
    return (
        "from __future__ import annotations\n\n"
        "from .entities import ENTITIES\n\n"
        "\n"
        "def build_metadata() -> dict[str, object]:\n"
        "    return {\n"
        "        \"entities\": ENTITIES,\n"
        "        \"entity_count\": len(ENTITIES),\n"
        "    }\n"
    )


def _render_router_factory_py() -> str:
    return (
        "from __future__ import annotations\n\n"
        "from fastapi import APIRouter\n\n"
        "from .metadata import build_metadata\n\n"
        "\n"
        "def create_router(api_prefix: str = \"/api\") -> APIRouter:\n"
        "    prefix = api_prefix.strip() or \"/api\"\n"
        "    if not prefix.startswith(\"/\"):\n"
        "        prefix = f\"/{prefix}\"\n"
        "    if prefix != \"/\":\n"
        "        prefix = prefix.rstrip(\"/\")\n"
        "    else:\n"
        "        prefix = \"\"\n"
        "\n"
        "    router = APIRouter(prefix=f\"{prefix}/filterx\", tags=[\"filterx\"])\n"
        "\n"
        "    @router.get(\"/metadata\")\n"
        "    def get_metadata() -> dict[str, object]:\n"
        "        return build_metadata()\n"
        "\n"
        "    return router\n"
    )


def _render_router_py(api_prefix: str) -> str:
    escaped = api_prefix.replace("\\", "\\\\").replace('"', '\\"')
    return (
        "from __future__ import annotations\n\n"
        "from .router_factory import create_router\n\n"
        f"API_PREFIX = \"{escaped}\"\n"
        "router = create_router(api_prefix=API_PREFIX)\n"
    )


def _render_predicates_py() -> str:
    return (
        "from __future__ import annotations\n\n"
        "from typing import Callable, Iterable\n\n"
        "\n"
        "PredicateHook = Callable[[str, object], object]\n"
        "\n"
        "\n"
        "def register_global_predicates(hooks: Iterable[PredicateHook]) -> list[PredicateHook]:\n"
        "    return [hook for hook in hooks]\n"
    )


def _render_init_py() -> str:
    return (
        "from .router import router\n\n"
        "__all__ = [\"router\"]\n"
    )


def _build_patch_ops(
    generated_root: str,
    entities: list[dict[str, Any]],
    api_prefix: str,
    mount_file: str,
    mount_anchor: str,
    generated_module: str,
    include_mount: bool,
) -> list[PatchOp]:
    root = Path(generated_root).as_posix().rstrip("/")

    ops = [
        PatchOp(
            kind="generated_file",
            path=f"{root}/__init__.py",
            content=_render_init_py(),
            description="FilterX backend package exports",
        ),
        PatchOp(
            kind="generated_file",
            path=f"{root}/entities.py",
            content=_render_entities_py(entities),
            description="FilterX scanned entity registry",
        ),
        PatchOp(
            kind="generated_file",
            path=f"{root}/metadata.py",
            content=_render_metadata_py(),
            description="FilterX metadata builder",
        ),
        PatchOp(
            kind="generated_file",
            path=f"{root}/router_factory.py",
            content=_render_router_factory_py(),
            description="FilterX router factory",
        ),
        PatchOp(
            kind="generated_file",
            path=f"{root}/router.py",
            content=_render_router_py(api_prefix),
            description="FilterX mountable router",
        ),
        PatchOp(
            kind="generated_file",
            path=f"{root}/predicates.py",
            content=_render_predicates_py(),
            description="FilterX global predicate hooks",
        ),
    ]

    if include_mount:
        snippet = (
            f"from {generated_module}.router import router as filterx_generated_router\n"
            "app.include_router(filterx_generated_router)"
        )
        ops.append(
            PatchOp(
                kind="anchor_insert",
                path=mount_file,
                anchor=mount_anchor,
                snippet=snippet,
                insert_mode="after",
                owner="host",
                description="Mount generated FilterX router",
            )
        )

    return ops


def _detect_generation_conflicts(
    project_root: Path,
    operations: list[PatchOp],
    allow_overwrite_generated: bool,
) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    for op in operations:
        if op.kind != "generated_file":
            continue
        target = project_root / op.path
        if target.exists():
            existing = target.read_text(encoding="utf-8")
            if existing != op.content and not allow_overwrite_generated:
                conflicts.append(
                    {
                        "code": "GENERATED_FILE_HASH_MISMATCH",
                        "path": op.path,
                        "message": "Existing generated file differs and overwrite is disabled.",
                    }
                )
    return conflicts


def _backend_validate_payload(
    project_root: Path,
    cfg: dict[str, Any],
    generated_module: str,
) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    root = Path(cfg["backend"]["generated_package"]).as_posix().rstrip("/")
    required = [
        f"{root}/__init__.py",
        f"{root}/entities.py",
        f"{root}/metadata.py",
        f"{root}/router_factory.py",
        f"{root}/router.py",
        f"{root}/predicates.py",
    ]
    for rel in required:
        if not (project_root / rel).exists():
            errors.append({"code": "BACKEND_GENERATED_FILE_MISSING", "path": str(project_root / rel)})

    mount_file = project_root / cfg["backend"]["mount_file"]
    mount_anchor = cfg["backend"]["mount_anchor"]
    mount_snippet = f"from {generated_module}.router import router as filterx_generated_router"

    if not mount_file.exists():
        errors.append({"code": "BACKEND_MOUNT_FILE_MISSING", "path": str(mount_file)})
    else:
        content = mount_file.read_text(encoding="utf-8")
        if mount_anchor not in content:
            warnings.append(
                {
                    "code": "BACKEND_MOUNT_ANCHOR_NOT_FOUND",
                    "path": str(mount_file),
                    "anchor": mount_anchor,
                }
            )
        if mount_snippet not in content:
            warnings.append(
                {
                    "code": "BACKEND_MOUNT_SNIPPET_NOT_FOUND",
                    "path": str(mount_file),
                    "snippet": mount_snippet,
                }
            )

    return {
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings),
    }


def run_install(args: Any) -> int:
    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config).resolve() if args.config else None
    effective = load_effective_config(project_root, config_path)
    cfg = effective.raw

    if not cfg["backend"].get("enabled", True):
        if args.json:
            print(json.dumps({"skipped": True, "reason": "backend disabled in config"}, indent=2))
        else:
            print("FilterX backend install skipped: backend.enabled is false.")
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
                    "message": "Run 'filterx scan' before backend install.",
                }
            ]
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print("FilterX backend install failed: scan artifact is missing.")
            print(f"- Expected scan file: {scan_path}")
        return 2

    scan_payload = load_json(scan_path)
    scan_entities = list(scan_payload.get("entities", []))
    selected_entities = _filter_entities(scan_entities, cfg, args)

    api_prefix = str(getattr(args, "api_prefix", None) or cfg["backend"].get("api_prefix", "/api"))
    mount_file = str(getattr(args, "mount_file", None) or cfg["backend"]["mount_file"])
    mount_anchor = str(getattr(args, "mount_anchor", None) or cfg["backend"]["mount_anchor"])
    include_mount = not bool(getattr(args, "no_mount", False))

    generated_root = str(cfg["backend"]["generated_package"])
    generated_module = _py_module_path(generated_root)

    operations = _build_patch_ops(
        generated_root=generated_root,
        entities=selected_entities,
        api_prefix=api_prefix,
        mount_file=mount_file,
        mount_anchor=mount_anchor,
        generated_module=generated_module,
        include_mount=include_mount,
    )

    existing_routes = list(scan_payload.get("routes", []))
    candidate_paths = [f"{_to_filterx_base_path(api_prefix)}/metadata"]
    route_conflicts = check_route_path_conflicts(existing_routes, candidate_paths)
    conflict_payload = [
        {
            "code": conflict.code,
            "message": conflict.message,
            "context": conflict.context,
        }
        for conflict in route_conflicts.conflicts
    ]

    allow_overwrite_generated = bool(cfg["safety"].get("allow_overwrite_generated", True)) or bool(
        getattr(args, "force", False)
    )
    generation_conflicts = _detect_generation_conflicts(
        project_root=project_root,
        operations=operations,
        allow_overwrite_generated=allow_overwrite_generated,
    )

    all_conflicts = conflict_payload + generation_conflicts
    if strict_conflict_mode and all_conflicts:
        payload = {
            "dry_run": dry_run or check_mode,
            "strict_conflict_mode": strict_conflict_mode,
            "conflicts": all_conflicts,
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print("FilterX backend install blocked by safety conflicts.")
            for conflict in all_conflicts:
                print(f"- {conflict['code']}: {conflict['message']}")
        return 3

    manifest_path = project_root / cfg["safety"]["idempotency_manifest"]
    patch_dir = project_root / cfg["output"]["patch_dir"]

    result = apply_patch_operations(
        project_root=project_root,
        operations=operations,
        manifest_path=manifest_path,
        patch_dir=patch_dir,
        dry_run=dry_run,
        check_mode=check_mode,
        strict_conflict_mode=strict_conflict_mode,
        description="backend.install",
    )

    payload = {
        "dry_run": result.dry_run,
        "check_mode": check_mode,
        "patch_id": result.patch_id,
        "generated_root": str((project_root / generated_root).resolve()),
        "selected_entities": [entity.get("model") for entity in selected_entities],
        "touched_files": result.touched_files,
        "applied_ops": result.applied_ops,
        "skipped_ops": result.skipped_ops,
        "issues": [
            {
                "code": issue.code,
                "message": issue.message,
                "context": issue.context,
            }
            for issue in result.issues
        ],
        "conflicts": all_conflicts,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("FilterX backend install completed.")
        print(f"- Dry run: {payload['dry_run']}")
        print(f"- Check mode: {payload['check_mode']}")
        print(f"- Patch ID: {payload['patch_id']}")
        print(f"- Applied ops: {payload['applied_ops']}")
        print(f"- Skipped ops: {payload['skipped_ops']}")
        print(f"- Touched files: {len(payload['touched_files'])}")

    if result.has_conflicts:
        return 3
    if getattr(args, "fail_on_warning", False) and result.issues:
        return 3
    return 0


def run_validate(args: Any) -> int:
    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config).resolve() if args.config else None
    effective = load_effective_config(project_root, config_path)
    cfg = effective.raw

    generated_module = _py_module_path(cfg["backend"]["generated_package"])
    payload = _backend_validate_payload(project_root=project_root, cfg=cfg, generated_module=generated_module)

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("FilterX backend validation completed.")
        print(f"- Errors: {payload['error_count']}")
        print(f"- Warnings: {payload['warning_count']}")

    if payload["errors"]:
        return 4
    if getattr(args, "fail_on_warning", False) and payload["warnings"]:
        return 3
    return 0


def run_remove(args: Any) -> int:
    return run_stub(args, "backend remove")
