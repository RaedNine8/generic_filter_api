from __future__ import annotations

import contextlib
import io
import json
import re
import shutil
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

from filterx.commands import backend, db, frontend, rollback, scan

SCENARIOS = (
    "simple_entity",
    "one_to_many",
    "many_to_many",
    "relationship_cycle",
    "soft_delete",
    "custom_predicate",
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _model_source(scenario: str) -> str:
    header = (
        "from __future__ import annotations\n\n"
        "from datetime import datetime\n"
        "from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table\n"
        "from sqlalchemy.orm import relationship\n\n"
        "from app.database import Base\n\n"
    )
    simple = (
        "class Author(Base):\n"
        "    __tablename__ = 'authors'\n\n"
        "    id = Column(Integer, primary_key=True)\n"
        "    name = Column(String(120), nullable=False)\n"
        "    email = Column(String(255), nullable=True, unique=True)\n"
    )
    if scenario == "simple_entity":
        return header + simple
    if scenario == "one_to_many":
        return header + (
            "class Author(Base):\n"
            "    __tablename__ = 'authors'\n"
            "    id = Column(Integer, primary_key=True)\n"
            "    name = Column(String(120), nullable=False)\n"
            "    books = relationship('Book', back_populates='author')\n\n"
            "class Book(Base):\n"
            "    __tablename__ = 'books'\n"
            "    id = Column(Integer, primary_key=True)\n"
            "    title = Column(String(255), nullable=False)\n"
            "    author_id = Column(Integer, ForeignKey('authors.id'), nullable=False)\n"
            "    author = relationship('Author', back_populates='books')\n"
        )
    if scenario == "many_to_many":
        return header + (
            "author_books = Table(\n"
            "    'author_books', Base.metadata,\n"
            "    Column('author_id', ForeignKey('authors.id'), primary_key=True),\n"
            "    Column('book_id', ForeignKey('books.id'), primary_key=True),\n"
            ")\n\n"
            "class Author(Base):\n"
            "    __tablename__ = 'authors'\n"
            "    id = Column(Integer, primary_key=True)\n"
            "    name = Column(String(120), nullable=False)\n"
            "    books = relationship('Book', secondary=author_books, back_populates='authors')\n\n"
            "class Book(Base):\n"
            "    __tablename__ = 'books'\n"
            "    id = Column(Integer, primary_key=True)\n"
            "    title = Column(String(255), nullable=False)\n"
            "    authors = relationship('Author', secondary=author_books, back_populates='books')\n"
        )
    if scenario == "relationship_cycle":
        return header + (
            "class Author(Base):\n"
            "    __tablename__ = 'authors'\n"
            "    id = Column(Integer, primary_key=True)\n"
            "    name = Column(String(120), nullable=False)\n"
            "    favorite_book_id = Column(Integer, ForeignKey('books.id'), nullable=True)\n"
            "    favorite_book = relationship('Book', back_populates='recommended_by')\n\n"
            "class Book(Base):\n"
            "    __tablename__ = 'books'\n"
            "    id = Column(Integer, primary_key=True)\n"
            "    title = Column(String(255), nullable=False)\n"
            "    recommended_by = relationship('Author', back_populates='favorite_book')\n"
        )
    if scenario == "soft_delete":
        return header + simple + "    deleted_at = Column(DateTime, nullable=True)\n"
    if scenario == "custom_predicate":
        return header + simple
    raise ValueError(f"Unknown golden scenario: {scenario}")


def _config(scenario: str) -> dict[str, Any]:
    hooks = ["app.security:active_rows"] if scenario == "custom_predicate" else []
    return {
        "version": 1,
        "project": {
            "name": f"golden_{scenario}",
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
            "auth_dependency_import": None,
            "permission_hook_import": None,
            "global_predicate_hooks": hooks,
            "entity_predicate_hooks": {},
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


def build_golden_project(project_root: Path, scenario: str) -> Path:
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown golden scenario: {scenario}")
    if project_root.exists():
        shutil.rmtree(project_root)
    project_root.mkdir(parents=True)

    _write(project_root / "app/__init__.py", "")
    _write(project_root / "app/models/__init__.py", "")
    _write(
        project_root / "app/database.py",
        "from sqlalchemy.orm import declarative_base\n\n"
        "Base = declarative_base()\n\n"
        "def get_db():\n"
        "    raise RuntimeError('golden fixture stub')\n",
    )
    _write(project_root / "app/models/entities.py", _model_source(scenario))
    _write(
        project_root / "app/main.py",
        "from fastapi import FastAPI\n\n"
        "app = FastAPI()\n\n"
        "@app.get('/health')\n"
        "def health():\n"
        "    return {'ok': True}\n\n"
        "# FILTERX:ROUTER_MOUNT\n",
    )
    if scenario == "custom_predicate":
        _write(
            project_root / "app/security.py",
            "def active_rows(query, **context):\n"
            "    return query\n",
        )

    _write(
        project_root / "frontend/package.json",
        json.dumps(
            {
                "name": f"golden-{scenario}",
                "version": "0.0.0",
                "private": True,
                "dependencies": {
                    "@angular/common": "^19.0.0",
                    "@angular/core": "^19.0.0",
                    "@angular/router": "^19.0.0",
                    "rxjs": "~7.8.0",
                },
                "devDependencies": {"@angular/cli": "^19.0.0"},
            },
            indent=2,
        )
        + "\n",
    )
    _write(
        project_root / "frontend/angular.json",
        json.dumps(
            {
                "projects": {
                    "frontend": {
                        "architect": {
                            "build": {"options": {"styles": ["src/styles.scss"]}},
                            "serve": {"options": {}},
                            "test": {"options": {"styles": ["src/styles.scss"]}},
                        }
                    }
                }
            },
            indent=2,
        )
        + "\n",
    )
    _write(project_root / "frontend/src/styles.scss", "/* host styles */\n")
    _write(
        project_root / "frontend/src/app/app.routes.ts",
        "import { Routes } from '@angular/router';\n\n"
        "export const routes: Routes = [\n"
        "  // FILTERX:ROUTES\n"
        "];\n",
    )
    _write(
        project_root / "frontend/src/app/app.config.ts",
        "import { ApplicationConfig } from '@angular/core';\n\n"
        "export const appConfig: ApplicationConfig = {\n"
        "  providers: [\n"
        "    // FILTERX:PROVIDERS\n"
        "  ],\n"
        "};\n",
    )
    _write(project_root / "filterx.yaml", json.dumps(_config(scenario), indent=2) + "\n")
    return project_root / "filterx.yaml"


def command_args(project_root: Path, config_path: Path, **overrides: Any) -> SimpleNamespace:
    values: dict[str, Any] = {
        "project_root": str(project_root),
        "config": str(config_path),
        "dry_run": False,
        "check": False,
        "json": True,
        "verbose": False,
        "yes": True,
        "fail_on_warning": False,
        "entities": None,
        "exclude_entities": None,
        "max_depth": None,
        "mount_file": None,
        "mount_anchor": None,
        "api_prefix": None,
        "force": False,
        "no_mount": False,
        "routes_file": None,
        "routes_anchor": None,
        "app_config_file": None,
        "app_config_anchor": None,
        "style": None,
        "no_route_patch": False,
        "saved_filters": None,
        "shared_filters": None,
        "auditing": None,
        "migration_dir": None,
        "name": None,
        "apply": False,
        "list": False,
        "patch_id": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _run_command(command: Callable[[Any], int], args: SimpleNamespace) -> dict[str, Any]:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        exit_code = command(args)
    return {"exit_code": exit_code, "stdout": output.getvalue()}


def _patch_id_map(project_root: Path) -> dict[str, str]:
    patch_root = project_root / ".filterx/patches"
    if not patch_root.exists():
        return {}
    return {
        path.name: f"<PATCH_{index:03d}>"
        for index, path in enumerate(sorted(path for path in patch_root.iterdir() if path.is_dir()), start=1)
    }


def _normalize(value: str, project_root: Path, patch_ids: dict[str, str]) -> str:
    normalized = value.replace("\\\\", "/").replace("\\", "/")
    normalized = normalized.replace(str(project_root.resolve()).replace("\\", "/"), "<PROJECT_ROOT>")
    for patch_id, replacement in patch_ids.items():
        normalized = normalized.replace(patch_id, replacement)
    normalized = re.sub(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?\+00:00",
        "<TIMESTAMP>",
        normalized,
    )
    normalized = re.sub(
        r"patch-\d{8}T\d{6}\.\d+Z-[0-9a-f]{8}",
        "<PATCH_ID>",
        normalized,
    )
    return normalized


def snapshot_files(project_root: Path, included: tuple[str, ...]) -> dict[str, str]:
    patch_ids = _patch_id_map(project_root)
    snapshot: dict[str, str] = {}
    for path in sorted(project_root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        relative = path.relative_to(project_root).as_posix()
        if relative in {"filterx.yaml", "app/__init__.py", "app/database.py", "app/security.py"}:
            continue
        if relative.startswith("app/models/"):
            continue
        if not any(relative == prefix or relative.startswith(f"{prefix}/") for prefix in included):
            continue
        normalized_path = relative
        for patch_id, replacement in patch_ids.items():
            normalized_path = normalized_path.replace(patch_id, replacement)
        snapshot[normalized_path] = _normalize(path.read_text(encoding="utf-8"), project_root, patch_ids)
    return snapshot


def capture_scenario(project_root: Path, scenario: str) -> dict[str, Any]:
    config_path = build_golden_project(project_root, scenario)
    args = command_args(project_root, config_path)
    result: dict[str, Any] = {"scenario": scenario, "commands": {}, "stages": {}}

    result["commands"]["scan"] = _run_command(scan.run, args)
    result["stages"]["scan"] = snapshot_files(
        project_root,
        (".filterx/scan.json", ".filterx/diagnostics.json", ".filterx/plan.json"),
    )

    result["commands"]["backend_install"] = _run_command(backend.run_install, args)
    result["stages"]["backend_install"] = snapshot_files(
        project_root,
        ("app/main.py", "app/filterx_generated", ".filterx/manifest.json", ".filterx/patches"),
    )

    result["commands"]["frontend_install"] = _run_command(frontend.run_install, args)
    result["stages"]["frontend_install"] = snapshot_files(
        project_root,
        ("frontend", ".filterx/manifest.json", ".filterx/patches"),
    )

    result["commands"]["db_install"] = _run_command(db.run_install, args)
    result["stages"]["db_install"] = snapshot_files(
        project_root,
        ("alembic/versions", ".filterx/manifest.json", ".filterx/patches"),
    )

    result["commands"]["backend_reinstall"] = _run_command(backend.run_install, args)
    result["commands"]["frontend_reinstall"] = _run_command(frontend.run_install, args)
    result["commands"]["db_reinstall"] = _run_command(db.run_install, args)
    result["stages"]["reinstall"] = snapshot_files(
        project_root,
        (".filterx/manifest.json", ".filterx/patches"),
    )

    patch_ids = [path.name for path in sorted((project_root / ".filterx/patches").iterdir()) if path.is_dir()]
    rollback_results: list[dict[str, Any]] = []
    for patch_id in reversed(patch_ids):
        rollback_results.append(
            _run_command(rollback.run, command_args(project_root, config_path, patch_id=patch_id))
        )
    result["commands"]["rollback"] = rollback_results
    result["stages"]["rollback"] = snapshot_files(
        project_root,
        (
            "app/main.py",
            "app/filterx_generated",
            "frontend",
            "alembic/versions",
            ".filterx/manifest.json",
            ".filterx/patches",
        ),
    )

    final_patch_ids = _patch_id_map(project_root)

    def normalize_object(obj: Any) -> Any:
        if isinstance(obj, str):
            return _normalize(obj, project_root, final_patch_ids)
        if isinstance(obj, list):
            return [normalize_object(item) for item in obj]
        if isinstance(obj, dict):
            return {key: normalize_object(item) for key, item in obj.items()}
        return obj

    return normalize_object(result)
