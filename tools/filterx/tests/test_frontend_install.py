from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from filterx.commands import frontend


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_config(project_root: Path) -> Path:
    config = {
        "version": 1,
        "project": {
            "name": "sample_frontend",
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
                    {"name": "id", "type": "integer"},
                    {"name": "title", "type": "string"},
                    {"name": "author.name", "type": "string"},
                ],
                "relationships": [],
            }
        ]
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
        "routes_file": None,
        "routes_anchor": None,
        "app_config_file": None,
        "app_config_anchor": None,
        "style": None,
        "force": False,
        "no_route_patch": False,
        "list": False,
        "patch_id": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_frontend_install_generates_files_and_patches_routes(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    _write_scan(tmp_path)

    _write_file(
        tmp_path / "frontend/src/app/app.routes.ts",
        "import { Routes } from '@angular/router';\n\n"
        "export const routes: Routes = [\n"
        "  { path: '', redirectTo: 'books', pathMatch: 'full' },\n"
        "  // FILTERX:ROUTES\n"
        "];\n",
    )
    _write_file(
        tmp_path / "frontend/src/app/features/books/book-list-new.component.ts",
        "export class BookListComponent {}\n",
    )

    exit_code = frontend.run_install(_args(tmp_path, config_path))
    assert exit_code == 0

    generated = tmp_path / "frontend/src/app/filterx-generated"
    assert (generated / "index.ts").exists()
    assert (generated / "routes.ts").exists()
    assert (generated / "entities/book.config.ts").exists()

    routes_content = (tmp_path / "frontend/src/app/app.routes.ts").read_text(encoding="utf-8")
    assert "FILTERX GENERATED ROUTES START" in routes_content
    assert "path: 'books'" in routes_content


def test_frontend_install_blocks_when_routes_anchor_missing(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    _write_scan(tmp_path)

    _write_file(
        tmp_path / "frontend/src/app/app.routes.ts",
        "import { Routes } from '@angular/router';\n\nexport const routes: Routes = [];\n",
    )
    _write_file(
        tmp_path / "frontend/src/app/features/books/book-list-new.component.ts",
        "export class BookListComponent {}\n",
    )

    exit_code = frontend.run_install(_args(tmp_path, config_path))
    assert exit_code == 3


def test_frontend_install_is_idempotent_on_route_patch(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    _write_scan(tmp_path)

    _write_file(
        tmp_path / "frontend/src/app/app.routes.ts",
        "import { Routes } from '@angular/router';\n\n"
        "export const routes: Routes = [\n"
        "  // FILTERX:ROUTES\n"
        "];\n",
    )
    _write_file(
        tmp_path / "frontend/src/app/features/books/book-list-new.component.ts",
        "export class BookListComponent {}\n",
    )

    assert frontend.run_install(_args(tmp_path, config_path)) == 0
    assert frontend.run_install(_args(tmp_path, config_path)) == 0

    routes_content = (tmp_path / "frontend/src/app/app.routes.ts").read_text(encoding="utf-8")
    assert routes_content.count("FILTERX GENERATED ROUTES START") == 1


def test_frontend_remove_rolls_back_generated_files_and_route_patch(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    _write_scan(tmp_path)

    original_routes = (
        "import { Routes } from '@angular/router';\n\n"
        "export const routes: Routes = [\n"
        "  // FILTERX:ROUTES\n"
        "];\n"
    )
    _write_file(tmp_path / "frontend/src/app/app.routes.ts", original_routes)
    _write_file(
        tmp_path / "frontend/src/app/features/books/book-list-new.component.ts",
        "export class BookListComponent {}\n",
    )

    assert frontend.run_install(_args(tmp_path, config_path)) == 0
    assert (tmp_path / "frontend/src/app/filterx-generated/index.ts").exists()

    assert frontend.run_remove(_args(tmp_path, config_path)) == 0

    assert not (tmp_path / "frontend/src/app/filterx-generated/index.ts").exists()
    routes_content = (tmp_path / "frontend/src/app/app.routes.ts").read_text(encoding="utf-8")
    assert routes_content == original_routes


def test_frontend_remove_returns_2_when_no_patch_bundle_exists(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    _write_scan(tmp_path)

    _write_file(
        tmp_path / "frontend/src/app/app.routes.ts",
        "import { Routes } from '@angular/router';\n\nexport const routes: Routes = [];\n",
    )

    assert frontend.run_remove(_args(tmp_path, config_path)) == 2
