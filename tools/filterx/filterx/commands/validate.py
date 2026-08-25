from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from filterx.core.config import load_effective_config
from filterx.core.manifest import load_manifest, validate_manifest


def _frontend_rel(frontend_root: str, suffix: str) -> str:
    return f"{frontend_root.rstrip('/')}/{suffix}"


def _resolve_routes_file(project_root: Path, frontend_root: str, configured_path: str) -> Path:
    configured = (project_root / configured_path).resolve()
    if configured.exists():
        return configured
    for candidate in ("src/app/app.routes.ts", "src/app/app-routing.module.ts"):
        path = (project_root / _frontend_rel(frontend_root, candidate)).resolve()
        if path.exists():
            return path
    return configured


def _resolve_app_config_file(project_root: Path, frontend_root: str, configured_path: str) -> Path | None:
    configured = (project_root / configured_path).resolve()
    if configured.exists():
        return configured

    default_config = (project_root / _frontend_rel(frontend_root, "src/app/app.config.ts")).resolve()
    if default_config.exists():
        return default_config

    module_file = (project_root / _frontend_rel(frontend_root, "src/app/app.module.ts")).resolve()
    if module_file.exists():
        return None

    return configured


def _require_file(errors: list[dict[str, Any]], path: Path, code: str) -> None:
    if not path.exists():
        errors.append({"code": code, "path": str(path)})


def _validate_backend_artifacts(
    project_root: Path,
    cfg: dict[str, Any],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> None:
    backend = cfg["backend"]
    framework = str(backend.get("framework", "fastapi-sqlalchemy"))
    if framework == "fastapi-sqlalchemy":
        mount_file = project_root / backend["mount_file"]
        mount_anchor = backend["mount_anchor"]
        if not mount_file.exists():
            errors.append({"code": "BACKEND_MOUNT_FILE_MISSING", "path": str(mount_file)})
        elif mount_anchor not in mount_file.read_text(encoding="utf-8"):
            warnings.append(
                {"code": "BACKEND_MOUNT_ANCHOR_NOT_FOUND", "path": str(mount_file), "anchor": mount_anchor}
            )
        return
    if framework == "express-prisma":
        express = backend.get("express", {})
        generated = project_root / str(express.get("generated_root", "src/filterx-generated"))
        _require_file(errors, generated / "router.ts", "EXPRESS_GENERATED_ROUTER_MISSING")
        _require_file(
            errors,
            project_root / str(express.get("app_file", "src/app.ts")),
            "EXPRESS_APP_FILE_MISSING",
        )
        return
    if framework == "spring-boot-jpa":
        spring = backend.get("spring", {})
        module = project_root / str(spring.get("module_path", "."))
        source_root = module / str(spring.get("source_root", "src/main/java"))
        package_path = str(spring.get("generated_package", "com.example.filterx.generated")).replace(".", "/")
        _require_file(
            errors,
            source_root / package_path / "FilterxController.java",
            "SPRING_GENERATED_CONTROLLER_MISSING",
        )


def _validate_frontend_artifacts(
    project_root: Path,
    cfg: dict[str, Any],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> None:
    frontend = cfg["frontend"]
    framework = str(frontend.get("framework", "angular"))
    if framework != "angular":
        target = frontend.get(framework.replace("-", "_"), {})
        workspace = project_root / str(target.get("workspace_root", frontend.get("workspace_root", "frontend")))
        generated = workspace / str(target.get("generated_root", "src/filterx-generated"))
        entry = "FilterxApp.vue" if framework == "vue" else "FilterxApp.tsx"
        _require_file(errors, generated / entry, "FRONTEND_GENERATED_ENTRY_MISSING")
        if framework == "nextjs":
            _require_file(errors, workspace / "src/app/filterx/page.tsx", "NEXTJS_FILTERX_PAGE_MISSING")
        else:
            host_file = workspace / str(target.get("host_file", "src/App.vue" if framework == "vue" else "src/App.tsx"))
            _require_file(errors, host_file, "FRONTEND_HOST_FILE_MISSING")
        return

    frontend_root = str(frontend.get("workspace_root", "frontend"))
    routes_file = _resolve_routes_file(project_root, frontend_root, str(frontend["routes_file"]))
    routes_anchor = frontend["routes_anchor"]
    app_config_file = _resolve_app_config_file(project_root, frontend_root, str(frontend["app_config_file"]))
    app_config_anchor = frontend["app_config_anchor"]
    if not routes_file.exists():
        errors.append({"code": "FRONTEND_ROUTES_FILE_MISSING", "path": str(routes_file)})
    if app_config_file is not None and not app_config_file.exists():
        errors.append({"code": "FRONTEND_APP_CONFIG_FILE_MISSING", "path": str(app_config_file)})
    if routes_file.exists():
        routes_content = routes_file.read_text(encoding="utf-8")
        if routes_anchor not in routes_content and "FILTERX GENERATED ROUTES START" not in routes_content:
            warnings.append(
                {"code": "FRONTEND_ROUTES_ANCHOR_NOT_FOUND", "path": str(routes_file), "anchor": routes_anchor}
            )
    if app_config_file is not None and app_config_file.exists() and app_config_anchor not in app_config_file.read_text(encoding="utf-8"):
        warnings.append(
            {"code": "FRONTEND_APP_CONFIG_ANCHOR_NOT_FOUND", "path": str(app_config_file), "anchor": app_config_anchor}
        )


def run(args: Any) -> int:
    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config).resolve() if args.config else None
    effective = load_effective_config(project_root, config_path)
    cfg = effective.raw

    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    scan_file = project_root / cfg["output"]["scan_file"]
    diagnostics_file = project_root / cfg["output"]["diagnostics_file"]
    plan_file = project_root / cfg["output"]["plan_file"]
    manifest_file = project_root / cfg["safety"]["idempotency_manifest"]

    for p, code in [
        (scan_file, "SCAN_FILE_MISSING"),
        (diagnostics_file, "DIAGNOSTICS_FILE_MISSING"),
        (plan_file, "PLAN_FILE_MISSING"),
    ]:
        if not p.exists():
            errors.append({"code": code, "path": str(p)})

    if manifest_file.exists():
        errors.extend(validate_manifest(load_manifest(manifest_file)))

    if cfg["backend"]["enabled"]:
        _validate_backend_artifacts(project_root, cfg, errors, warnings)

    if cfg["frontend"]["enabled"]:
        _validate_frontend_artifacts(project_root, cfg, errors, warnings)

    payload = {
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings),
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("FilterX validation completed.")
        print(f"- Errors: {len(errors)}")
        print(f"- Warnings: {len(warnings)}")

    if errors:
        return 4
    if args.fail_on_warning and warnings:
        return 3
    return 0
