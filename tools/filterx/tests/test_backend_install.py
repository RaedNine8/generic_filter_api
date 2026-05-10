from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

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
                "module": "app.models.book",
                "table": "books",
                "primary_keys": ["id"],
                "fields": [
                    {"name": "id", "type": "integer", "primary_key": True, "ops": ["eq", "gt", "lt"]},
                    {"name": "title", "type": "string", "ops": ["eq", "like", "ilike"]},
                    {"name": "genre", "type": "string", "ops": ["eq", "like", "ilike"]},
                    {"name": "price", "type": "float", "ops": ["eq", "gt", "gte", "lt", "lte"]},
                ],
                "relationships": [
                    {
                        "name": "author",
                        "related_model": "Author",
                        "related_table": "authors",
                        "cardinality": "m2o",
                        "uselist": False,
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


def _purge_app_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            sys.modules.pop(module_name, None)


def _write_runtime_project(project_root: Path) -> Path:
    config_path = _write_config(project_root)
    _write_scan(project_root)
    db_url = f"sqlite:///{(project_root / 'filterx_runtime.db').as_posix()}"
    _write_file(project_root / "app/__init__.py", "")
    _write_file(project_root / "app/models/__init__.py", "")
    _write_file(
        project_root / "app/database.py",
        "from sqlalchemy import create_engine\n"
        "from sqlalchemy.orm import declarative_base, sessionmaker\n\n"
        f"engine = create_engine('{db_url}', connect_args={{'check_same_thread': False}})\n"
        "SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)\n"
        "Base = declarative_base()\n\n"
        "def get_db():\n"
        "    db = SessionLocal()\n"
        "    try:\n"
        "        yield db\n"
        "    finally:\n"
        "        db.close()\n",
    )
    _write_file(
        project_root / "app/models/author.py",
        "from sqlalchemy import Column, Integer, String\n"
        "from sqlalchemy.orm import relationship\n"
        "from app.database import Base\n\n"
        "class Author(Base):\n"
        "    __tablename__ = 'authors'\n"
        "    id = Column(Integer, primary_key=True)\n"
        "    name = Column(String, nullable=False)\n"
        "    books = relationship('Book', back_populates='author')\n",
    )
    _write_file(
        project_root / "app/models/book.py",
        "from sqlalchemy import Column, Float, ForeignKey, Integer, String\n"
        "from sqlalchemy.orm import relationship\n"
        "from app.database import Base\n\n"
        "class Book(Base):\n"
        "    __tablename__ = 'books'\n"
        "    id = Column(Integer, primary_key=True)\n"
        "    title = Column(String, nullable=False)\n"
        "    genre = Column(String, nullable=False)\n"
        "    price = Column(Float, nullable=False)\n"
        "    author_id = Column(Integer, ForeignKey('authors.id'))\n"
        "    author = relationship('Author', back_populates='books')\n",
    )
    _write_file(
        project_root / "app/main.py",
        "from fastapi import FastAPI\n\n"
        "app = FastAPI()\n"
        "# FILTERX:ROUTER_MOUNT\n",
    )
    return config_path


def test_generated_backend_router_exposes_query_filter_and_group_endpoints(tmp_path: Path) -> None:
    project_root = tmp_path / "runtime_project"
    project_root.mkdir()
    config_path = _write_runtime_project(project_root)

    assert backend.run_install(_args(project_root, config_path)) == 0

    sys.path.insert(0, str(project_root))
    _purge_app_modules()
    try:
        database = importlib.import_module("app.database")
        importlib.import_module("app.models.author")
        importlib.import_module("app.models.book")
        database.Base.metadata.create_all(bind=database.engine)

        Author = importlib.import_module("app.models.author").Author
        Book = importlib.import_module("app.models.book").Book
        session = database.SessionLocal()
        ada = Author(name="Ada")
        bob = Author(name="Bob")
        session.add_all(
            [
                ada,
                bob,
                Book(title="Alpha Filtering", genre="Tech", price=10.0, author=ada),
                Book(title="Beta Search", genre="Tech", price=30.0, author=bob),
                Book(title="Gamma Grouping", genre="Business", price=40.0, author=bob),
            ]
        )
        session.commit()
        session.close()

        app = importlib.import_module("app.main").app
        with TestClient(app) as client:
            query_response = client.get(
                "/api/filterx/books/query",
                params={"title_ilike": "alpha", "sort_by": "id", "order": "asc"},
            )
            assert query_response.status_code == 200
            query_payload = query_response.json()
            assert query_payload["meta"]["total_items"] == 1
            assert query_payload["data"][0]["title"] == "Alpha Filtering"
            assert query_payload["data"][0]["author"]["name"] == "Ada"

            tree_response = client.post(
                "/api/filterx/books/filter",
                json={
                    "node_type": "condition",
                    "field": "author.name",
                    "operation": "eq",
                    "value": "Bob",
                },
                params={"sort_by": "price", "order": "asc"},
            )
            assert tree_response.status_code == 200
            tree_payload = tree_response.json()
            assert tree_payload["meta"]["total_items"] == 2
            assert [row["title"] for row in tree_payload["data"]] == ["Beta Search", "Gamma Grouping"]

            group_response = client.get("/api/filterx/books/group-by/genre")
            assert group_response.status_code == 200
            assert {row["key"]: row["count"] for row in group_response.json()} == {"Tech": 2, "Business": 1}
    finally:
        _purge_app_modules()
        if str(project_root) in sys.path:
            sys.path.remove(str(project_root))
