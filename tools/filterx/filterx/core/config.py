from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .schema import ConfigValidationError, EffectiveConfig, deep_merge

_IMPORT_PATH_RE = re.compile(r"^[A-Za-z0-9_\.]+:[A-Za-z0-9_]+$")


def default_config() -> Dict[str, Any]:
    return {
        "version": 1,
        "project": {
            "name": "",
            "root": ".",
            "backend_root": "app",
            "frontend_root": "frontend",
            "alembic_ini": "alembic.ini",
        },
        "python": {
            "app_import": "app.main:app",
            "base_class_import": "app.database:Base",
            "models_package": "app.models",
            "session_dependency_import": "app.database:get_db",
            "sqlalchemy_url_env": "DATABASE_URL",
        },
        "backend": {
            "enabled": True,
            "framework": "fastapi-sqlalchemy",
            "api_prefix": "/api",
            "generated_package": "app/filterx_generated",
            "mount_file": "app/main.py",
            "mount_anchor": "# FILTERX:ROUTER_MOUNT",
            "entities": [],
            "exclude_entities": [],
            "auth_dependency_import": None,
            "permission_hook_import": None,
            "field_visibility_hook_import": None,
            "global_predicate_hooks": [],
            "entity_predicate_hooks": {},
            "express": {
                "generated_root": "src/filterx-generated",
                "app_file": "src/app.ts",
                "app_anchor": "// FILTERX:ROUTER_MOUNT",
                "package_json": "package.json",
                "tsconfig": "tsconfig.json",
                "hooks_module": None,
                "rate_limit_per_minute": 120,
                "max_query_cost": 100,
            },
            "spring": {
                "module_path": ".",
                "build_tool": None,
                "maven_command": None,
                "gradle_command": None,
                "source_root": "src/main/java",
                "generated_package": "com.example.filterx.generated",
                "application_class": None,
                "pom_file": "pom.xml",
                "gradle_file": None,
                "use_records": True,
                "jpa_provider": "hibernate",
                "springdoc_version": "2.8.9",
                "resilience4j_version": "2.3.0",
                "poi_version": "5.4.1",
                "rate_limit_per_minute": 120,
                "max_query_cost": 100,
                "compile_timeout_seconds": 180,
                "maven_args": [],
                "gradle_args": [],
            },
        },
        "frontend": {
            "enabled": True,
            "framework": "angular",
            "workspace_root": "frontend",
            "generated_root": "frontend/src/app/filterx-generated",
            "routes_file": "frontend/src/app/app.routes.ts",
            "routes_anchor": "// FILTERX:ROUTES",
            "app_config_file": "frontend/src/app/app.config.ts",
            "app_config_anchor": "// FILTERX:PROVIDERS",
            "entity_style": "kebab",
            "react_vite": {
                "workspace_root": "frontend",
                "generated_root": "src/filterx-generated",
                "host_file": "src/App.tsx",
                "host_anchor": "// FILTERX:APP",
                "api_base_url": "/api/filterx",
            },
            "nextjs": {
                "workspace_root": "frontend",
                "generated_root": "src/filterx-generated",
                "api_base_url": "/api/filterx",
            },
            "vue": {
                "workspace_root": "frontend",
                "generated_root": "src/filterx-generated",
                "host_file": "src/App.vue",
                "host_anchor": "<!-- FILTERX:APP -->",
                "api_base_url": "/api/filterx",
            },
        },
        "database": {
            "enabled": False,
            "provider": "alembic",
            "migration_dir": "alembic/versions",
            "features": {
                "saved_filters": True,
                "shared_filters": False,
                "auditing": False,
            },
        },
        "scan": {
            "framework": "sqlalchemy",
            "emit_ir": False,
            "timeout_seconds": 30,
            "prisma": {
                "schema": "prisma/schema.prisma",
                "package_json": "package.json",
                "client_marker": "node_modules/.prisma/client/index.js",
                "node_command": "node",
                "allow_stale_client": False,
            },
            "jpa": {
                "module_path": ".",
                "build_tool": None,
                "java_command": "java",
                "maven_command": None,
                "gradle_command": None,
                "helper_source": None,
                "classes_dir": None,
                "classpath": None,
                "compile_timeout_seconds": 120,
                "helper_timeout_seconds": 60,
                "maven_args": [],
                "gradle_args": [],
            },
            "max_relationship_depth": 3,
            "include_views": False,
            "include_hybrid_properties": False,
            "respect_soft_delete": True,
        },
        "safety": {
            "dry_run_default": True,
            "require_anchor_comments": True,
            "idempotency_manifest": ".filterx/manifest.json",
            "allow_overwrite_generated": True,
            "strict_conflict_mode": True,
        },
        "output": {
            "scan_file": ".filterx/scan.json",
            "ir_file": ".filterx/ir.json",
            "plan_file": ".filterx/plan.json",
            "diagnostics_file": ".filterx/diagnostics.json",
            "patch_dir": ".filterx/patches",
        },
    }


def _read_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise ConfigValidationError(f"Config file not found: {path}")
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ConfigValidationError("Config root must be a mapping/object.")
    return loaded


def _require_import_path(value: str, field_name: str) -> None:
    if not _IMPORT_PATH_RE.match(value):
        raise ConfigValidationError(
            f"Invalid import path for '{field_name}': '{value}'. Expected module:object"
        )


def _require_optional_import_path(value: Any, field_name: str) -> None:
    if value is None or value == "":
        return
    if not isinstance(value, str):
        raise ConfigValidationError(f"'{field_name}' must be null or a module:object string")
    _require_import_path(value, field_name)


def _validate(cfg: Dict[str, Any]) -> None:
    required_top = [
        "version",
        "project",
        "python",
        "backend",
        "frontend",
        "database",
        "scan",
        "safety",
        "output",
    ]
    for key in required_top:
        if key not in cfg:
            raise ConfigValidationError(f"Missing top-level config section: '{key}'")

    if cfg["version"] != 1:
        raise ConfigValidationError("Unsupported config version. Expected version: 1")

    _require_import_path(cfg["python"]["app_import"], "python.app_import")
    _require_import_path(cfg["python"]["base_class_import"], "python.base_class_import")
    _require_import_path(
        cfg["python"]["session_dependency_import"],
        "python.session_dependency_import",
    )

    backend_cfg = cfg["backend"]
    _require_optional_import_path(
        backend_cfg.get("auth_dependency_import"),
        "backend.auth_dependency_import",
    )
    _require_optional_import_path(
        backend_cfg.get("permission_hook_import"),
        "backend.permission_hook_import",
    )
    _require_optional_import_path(
        backend_cfg.get("field_visibility_hook_import"),
        "backend.field_visibility_hook_import",
    )

    for section in ("backend", "frontend", "scan"):
        framework = cfg[section].get("framework")
        if not isinstance(framework, str) or not framework.strip():
            raise ConfigValidationError(f"{section}.framework must be a non-empty string")

    global_hooks = backend_cfg.get("global_predicate_hooks")
    if not isinstance(global_hooks, list):
        raise ConfigValidationError("backend.global_predicate_hooks must be a list")
    for index, hook in enumerate(global_hooks):
        if not isinstance(hook, str):
            raise ConfigValidationError(
                f"backend.global_predicate_hooks[{index}] must be a module:object string"
            )
        _require_import_path(hook, f"backend.global_predicate_hooks[{index}]")

    entity_hooks = backend_cfg.get("entity_predicate_hooks")
    if not isinstance(entity_hooks, dict):
        raise ConfigValidationError("backend.entity_predicate_hooks must be a mapping")
    for entity_name, hooks in entity_hooks.items():
        if not isinstance(entity_name, str) or not entity_name.strip():
            raise ConfigValidationError("backend.entity_predicate_hooks keys must be entity names")
        if not isinstance(hooks, list):
            raise ConfigValidationError(
                f"backend.entity_predicate_hooks.{entity_name} must be a list"
            )
        for index, hook in enumerate(hooks):
            if not isinstance(hook, str):
                raise ConfigValidationError(
                    f"backend.entity_predicate_hooks.{entity_name}[{index}] must be a module:object string"
                )
            _require_import_path(
                hook,
                f"backend.entity_predicate_hooks.{entity_name}[{index}]",
            )

    max_depth = cfg["scan"]["max_relationship_depth"]
    if not isinstance(max_depth, int) or max_depth < 1 or max_depth > 8:
        raise ConfigValidationError("scan.max_relationship_depth must be an integer between 1 and 8")

    timeout = cfg["scan"].get("timeout_seconds", 30)
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ConfigValidationError("scan.timeout_seconds must be a positive number")

    jpa = cfg["scan"].get("jpa")
    if not isinstance(jpa, dict):
        raise ConfigValidationError("scan.jpa must be a mapping")
    if jpa.get("build_tool") not in {None, "maven", "gradle"}:
        raise ConfigValidationError("scan.jpa.build_tool must be null, 'maven', or 'gradle'")
    for field_name in ("module_path", "java_command"):
        if not isinstance(jpa.get(field_name), str) or not jpa[field_name].strip():
            raise ConfigValidationError(f"scan.jpa.{field_name} must be a non-empty string")
    for field_name in ("compile_timeout_seconds", "helper_timeout_seconds"):
        value = jpa.get(field_name)
        if not isinstance(value, (int, float)) or value <= 0:
            raise ConfigValidationError(f"scan.jpa.{field_name} must be a positive number")
    for field_name in ("maven_args", "gradle_args"):
        value = jpa.get(field_name)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ConfigValidationError(f"scan.jpa.{field_name} must be a list of strings")

    spring = backend_cfg.get("spring")
    if not isinstance(spring, dict):
        raise ConfigValidationError("backend.spring must be a mapping")
    if spring.get("build_tool") not in {None, "maven", "gradle"}:
        raise ConfigValidationError("backend.spring.build_tool must be null, 'maven', or 'gradle'")
    for field_name in ("module_path", "source_root", "generated_package"):
        if not isinstance(spring.get(field_name), str) or not spring[field_name].strip():
            raise ConfigValidationError(f"backend.spring.{field_name} must be a non-empty string")
    if spring.get("application_class") is not None and (
        not isinstance(spring["application_class"], str) or not spring["application_class"].strip()
    ):
        raise ConfigValidationError("backend.spring.application_class must be null or a non-empty class name")
    for field_name in ("maven_command", "gradle_command"):
        if spring.get(field_name) is not None and (
            not isinstance(spring[field_name], str) or not spring[field_name].strip()
        ):
            raise ConfigValidationError(f"backend.spring.{field_name} must be null or a non-empty command")
    for field_name in ("springdoc_version", "resilience4j_version", "poi_version"):
        if not isinstance(spring.get(field_name), str) or not spring[field_name].strip():
            raise ConfigValidationError(f"backend.spring.{field_name} must be a pinned non-empty version")
    for field_name in ("rate_limit_per_minute", "max_query_cost"):
        value = spring.get(field_name)
        if not isinstance(value, int) or value < 1:
            raise ConfigValidationError(f"backend.spring.{field_name} must be a positive integer")
    timeout = spring.get("compile_timeout_seconds")
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ConfigValidationError("backend.spring.compile_timeout_seconds must be a positive number")
    for field_name in ("maven_args", "gradle_args"):
        value = spring.get(field_name)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ConfigValidationError(f"backend.spring.{field_name} must be a list of strings")



def load_effective_config(project_root: Path, config_path: Optional[Path]) -> EffectiveConfig:
    if config_path is None:
        default_a = project_root / "filterx.yaml"
        default_b = project_root / "filterx.yml"
        if default_a.exists():
            config_path = default_a
        elif default_b.exists():
            config_path = default_b
        else:
            raise ConfigValidationError(
                "No filterx config file found. Expected filterx.yaml or filterx.yml in project root."
            )

    user_cfg = _read_yaml(config_path)
    merged = deep_merge(default_config(), user_cfg)

    if not merged["project"]["name"]:
        merged["project"]["name"] = project_root.name
    merged["project"]["root"] = str(project_root)

    _validate(merged)
    return EffectiveConfig(raw=merged, project_root=project_root)
