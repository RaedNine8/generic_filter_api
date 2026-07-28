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
            "api_prefix": "/api",
            "generated_package": "app/filterx_generated",
            "mount_file": "app/main.py",
            "mount_anchor": "# FILTERX:ROUTER_MOUNT",
            "entities": [],
            "exclude_entities": [],
            "global_predicate_hooks": [],
        },
        "frontend": {
            "enabled": True,
            "workspace_root": "frontend",
            "generated_root": "frontend/src/app/filterx-generated",
            "routes_file": "frontend/src/app/app.routes.ts",
            "routes_anchor": "// FILTERX:ROUTES",
            "app_config_file": "frontend/src/app/app.config.ts",
            "app_config_anchor": "// FILTERX:PROVIDERS",
            "entity_style": "kebab",
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
        "agent": {
            "enabled": False,
            "providers": [
                {
                    "name": "groq",
                    "api_key_env": "GROQ_API_KEY",
                    "model": "llama-3.3-70b-versatile",
                    "roles": ["compile", "retry", "summarize"],
                },
                {
                    "name": "gemini",
                    "api_key_env": "GEMINI_API_KEY",
                    "model": "gemini-2.5-flash",
                    "roles": ["fallback"],
                },
            ],
            "vector_store": {
                "enabled": False,
                "backend": "chroma",
                "path": ".filterx/vector_store",
                "embedding_model": "all-MiniLM-L6-v2",
            },
            "safety": {
                "require_human_preview": True,
                "max_validation_retries": 3,
                "max_provider_retries": 3,
                "circuit_breaker_failure_threshold": 5,
                "circuit_breaker_reset_seconds": 60,
            },
            "mount_file": "app/main.py",
            "mount_anchor": "# FILTERX:COPILOT_MOUNT",
            "generated_file": "app/filterx_generated/copilot_router.py",
        },
        "scan": {
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

    max_depth = cfg["scan"]["max_relationship_depth"]
    if not isinstance(max_depth, int) or max_depth < 1 or max_depth > 8:
        raise ConfigValidationError("scan.max_relationship_depth must be an integer between 1 and 8")

    agent_cfg = cfg.get("agent", {})
    if agent_cfg.get("enabled", False):
        providers = agent_cfg.get("providers")
        if not isinstance(providers, list) or not providers:
            raise ConfigValidationError("agent.providers must be a non-empty list when agent.enabled is true")
        providers_by_role: dict[str, int] = {}
        for idx, provider in enumerate(providers):
            if not isinstance(provider, dict):
                raise ConfigValidationError(f"agent.providers[{idx}] must be a mapping/object")
            for field_name in ("name", "api_key_env", "model", "roles"):
                if field_name not in provider:
                    raise ConfigValidationError(f"agent.providers[{idx}] missing required field '{field_name}'")
            roles = provider.get("roles")
            if not isinstance(roles, list) or not all(isinstance(role, str) and role for role in roles):
                raise ConfigValidationError(f"agent.providers[{idx}].roles must be a non-empty list of strings")
            for role in roles:
                providers_by_role[role] = providers_by_role.get(role, 0) + 1
        if providers_by_role.get("compile", 0) < 1:
            raise ConfigValidationError("agent.providers must include at least one provider with the 'compile' role")



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
