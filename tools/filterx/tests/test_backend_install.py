from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from filterx.commands import backend


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_config(project_root: Path) -> Path:
    config = {
        "version": 1,
        "project": {
            "name": "sample",
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
            "enabled": False,
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
        "scan": {
            "max_relationship_depth": 3,
            "include_views": False,
            "include_hybrid_properties": False,
            "respect_soft_delete": True,
        },
        "safety": {
            "dry_run_default": False,
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

    path = project_root / "filterx.yaml"
    _write_file(path, json.dumps(config, indent=2))
    return path


def _write_scan(project_root: Path) -> None:
    payload = {
        "entities": [
            {
                "model": "Book",
                "table": "books",
                "primary_keys": ["id"],
                "fields": [
                    {"name": "id", "type": "integer", "ops": ["eq"]},
                    {"name": "title", "type": "string", "ops": ["eq", "like"]},
                ],
                "relationships": [
                    {
                        "name": "author",
                        "related_model": "Author",
                        "cardinality": "m2o",
                    }
                ],
            }
        ],
        "routes": [],
    }
    _write_file(project_root / ".filterx/scan.json", json.dumps(payload, indent=2))


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
        "entities": None,
        "mount_file": None,
        "mount_anchor": None,
        "api_prefix": None,
        "force": False,
        "no_mount": False,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_backend_install_generates_files_and_mounts_router(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    _write_scan(tmp_path)
    _write_file(
        tmp_path / "app/main.py",
        "from fastapi import FastAPI\napp = FastAPI()\n# FILTERX:ROUTER_MOUNT\n",
    )

    exit_code = backend.run_install(_args(tmp_path, config_path))

    assert exit_code == 0
    assert (tmp_path / "app/filterx_generated/router.py").exists()
    assert (tmp_path / "app/filterx_generated/entities.py").exists()

    mount_content = (tmp_path / "app/main.py").read_text(encoding="utf-8")
    assert "from app.filterx_generated.router import router as filterx_generated_router" in mount_content
    assert "app.include_router(filterx_generated_router)" in mount_content


def test_backend_install_blocks_on_missing_mount_anchor_in_strict_mode(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    _write_scan(tmp_path)
    _write_file(tmp_path / "app/main.py", "from fastapi import FastAPI\napp = FastAPI()\n")

    exit_code = backend.run_install(_args(tmp_path, config_path))

    assert exit_code == 3
    assert not (tmp_path / "app/filterx_generated/router.py").exists()


def test_backend_install_no_mount_generates_even_without_anchor(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    _write_scan(tmp_path)
    _write_file(tmp_path / "app/main.py", "from fastapi import FastAPI\napp = FastAPI()\n")

    exit_code = backend.run_install(_args(tmp_path, config_path, no_mount=True))

    assert exit_code == 0
    assert (tmp_path / "app/filterx_generated/router.py").exists()
    mount_content = (tmp_path / "app/main.py").read_text(encoding="utf-8")
    assert "filterx_generated_router" not in mount_content
