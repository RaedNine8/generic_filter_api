from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from filterx.commands import db


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_config(project_root: Path) -> Path:
    config = {
        "version": 1,
        "project": {
            "name": "sample_db",
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
            "enabled": False,
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
            "enabled": True,
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
        "migration_dir": None,
        "name": None,
        "apply": False,
        "saved_filters": None,
        "shared_filters": None,
        "auditing": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_db_validate_reports_missing_generated_migration(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)

    exit_code = db.run_validate(_args(tmp_path, config_path))
    assert exit_code == 4


def test_db_install_generates_concrete_migration_and_validate_passes(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)

    install_code = db.run_install(_args(tmp_path, config_path))
    assert install_code == 0

    migration_file = tmp_path / "alembic/versions/filterx_generated_persistence.py"
    assert migration_file.exists()

    content = migration_file.read_text(encoding="utf-8")
    assert "from alembic import op" in content
    assert "op.create_table(" in content
    assert "'filterx_saved_filters'" in content
    assert "op.drop_table('filterx_saved_filters')" in content
    assert "'filterx_shared_filters'" not in content
    assert "'filterx_filter_audit_logs'" not in content
    assert "def upgrade()" in content
    assert "def downgrade()" in content

    validate_code = db.run_validate(_args(tmp_path, config_path))
    assert validate_code == 0


def test_db_install_can_enable_optional_features_from_args(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)

    install_code = db.run_install(
        _args(
            tmp_path,
            config_path,
            shared_filters=True,
            auditing=True,
        )
    )
    assert install_code == 0

    migration_file = tmp_path / "alembic/versions/filterx_generated_persistence.py"
    content = migration_file.read_text(encoding="utf-8")
    assert "'filterx_shared_filters'" in content
    assert "op.drop_table('filterx_shared_filters')" in content
    assert "'filterx_filter_audit_logs'" in content
    assert "op.drop_table('filterx_filter_audit_logs')" in content
