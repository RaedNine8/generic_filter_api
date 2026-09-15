from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from filterx.commands import copilot
from filterx.core.config import load_effective_config
from filterx.core.schema import ConfigValidationError


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_config(project_root: Path) -> Path:
    config = {
        "version": 1,
        "project": {"name": "sample", "root": ".", "backend_root": "app", "frontend_root": "frontend", "alembic_ini": "alembic.ini"},
        "python": {"app_import": "app.main:app", "base_class_import": "app.database:Base", "models_package": "app.models", "session_dependency_import": "app.database:get_db", "sqlalchemy_url_env": "DATABASE_URL"},
        "backend": {"enabled": True, "api_prefix": "/api", "generated_package": "app/filterx_generated", "mount_file": "app/main.py", "mount_anchor": "# FILTERX:ROUTER_MOUNT", "entities": [], "exclude_entities": [], "global_predicate_hooks": []},
        "frontend": {"enabled": False, "workspace_root": "frontend", "generated_root": "frontend/src/app/filterx-generated", "routes_file": "frontend/src/app/app.routes.ts", "routes_anchor": "// FILTERX:ROUTES", "app_config_file": "frontend/src/app/app.config.ts", "app_config_anchor": "// FILTERX:PROVIDERS", "entity_style": "kebab"},
        "database": {"enabled": False, "provider": "alembic", "migration_dir": "alembic/versions", "features": {"saved_filters": True, "shared_filters": False, "auditing": False}},
        "agent": {"enabled": True, "providers": [{"name": "groq", "api_key_env": "GROQ_API_KEY", "model": "llama", "roles": ["compile"]}], "mount_file": "app/main.py", "mount_anchor": "# FILTERX:COPILOT_MOUNT", "generated_file": "app/filterx_generated/copilot_router.py"},
        "scan": {"max_relationship_depth": 3, "include_views": False, "include_hybrid_properties": False, "respect_soft_delete": True},
        "safety": {"dry_run_default": False, "require_anchor_comments": True, "idempotency_manifest": ".filterx/manifest.json", "allow_overwrite_generated": True, "strict_conflict_mode": True},
        "output": {"scan_file": ".filterx/scan.json", "plan_file": ".filterx/plan.json", "diagnostics_file": ".filterx/diagnostics.json", "patch_dir": ".filterx/patches"},
    }
    path = project_root / "filterx.yaml"
    _write_file(path, json.dumps(config, indent=2))
    return path


def _args(project_root: Path, config_path: Path, **overrides: object) -> SimpleNamespace:
    base: dict[str, object] = {
        "project_root": str(project_root),
        "config": str(config_path),
        "dry_run": False,
        "check": False,
        "json": True,
        "verbose": False,
        "yes": False,
        "fail_on_warning": False,
        "no_mount": False,
        "patch_id": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_copilot_install_is_idempotent_and_validate_passes(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    _write_file(tmp_path / "app/main.py", "from fastapi import FastAPI\napp = FastAPI()\n# FILTERX:COPILOT_MOUNT\n")
    _write_file(tmp_path / "app/filterx_generated/entities.py", "ENTITIES = []\n")
    _write_file(tmp_path / ".filterx/scan.json", '{"entities": []}\n')

    assert copilot.run_install(_args(tmp_path, config_path)) == 0
    first_main = (tmp_path / "app/main.py").read_text(encoding="utf-8")
    assert "filterx_copilot_router" in first_main
    generated_router = tmp_path / "app/filterx_generated/copilot_router.py"
    assert generated_router.exists()
    generated_content = generated_router.read_text(encoding="utf-8")
    assert "from app.filterx_generated.entities import ENTITIES" in generated_content
    assert "GenericQueryExecutor" not in generated_content
    compile(generated_content, str(generated_router), "exec")

    assert copilot.run_install(_args(tmp_path, config_path)) == 0
    second_main = (tmp_path / "app/main.py").read_text(encoding="utf-8")
    assert second_main == first_main
    assert copilot.run_validate(_args(tmp_path, config_path)) == 0


def test_agent_config_accepts_keyless_openai_compatible_provider(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["agent"]["providers"] = [
        {
            "name": "openai-compatible",
            "model": "qwen2.5:7b",
            "base_url": "http://localhost:11434/v1",
            "api_key_env": "",
            "require_api_key": False,
            "roles": ["compile"],
        }
    ]
    config_path.write_text(json.dumps(config), encoding="utf-8")

    loaded = load_effective_config(tmp_path, config_path)
    assert loaded.raw["agent"]["providers"][0]["api_key_env"] == ""


def test_agent_config_rejects_unsupported_backend(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["backend"]["framework"] = "express-prisma"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    with pytest.raises(ConfigValidationError, match="fastapi-sqlalchemy"):
        load_effective_config(tmp_path, config_path)


def test_copilot_dry_run_does_not_require_generated_entities(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    _write_file(tmp_path / "app/main.py", "from fastapi import FastAPI\napp = FastAPI()\n# FILTERX:COPILOT_MOUNT\n")

    result = copilot.run_install(_args(tmp_path, config_path, dry_run=True))

    assert result == 0
    assert not (tmp_path / "app/filterx_generated/copilot_router.py").exists()
