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
                    {"name": "is_active", "type": "boolean", "ops": ["eq", "ne"]},
                    {"name": "published_on", "type": "date", "ops": ["eq", "gt", "gte", "lt", "lte"]},
                    {
                        "name": "status",
                        "type": "enum",
                        "ops": ["eq", "ne", "like", "ilike"],
                        "enum_values": ["draft", "published"],
                    },
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
        "from sqlalchemy import Boolean, Column, Date, Enum, Float, ForeignKey, Integer, String\n"
        "from sqlalchemy.orm import relationship\n"
        "from app.database import Base\n\n"
        "class Book(Base):\n"
        "    __tablename__ = 'books'\n"
        "    id = Column(Integer, primary_key=True)\n"
        "    title = Column(String, nullable=False)\n"
        "    genre = Column(String, nullable=False)\n"
        "    price = Column(Float, nullable=False)\n"
        "    is_active = Column(Boolean, nullable=False, default=True)\n"
        "    published_on = Column(Date, nullable=True)\n"
        "    status = Column(Enum('draft', 'published', name='book_status'), nullable=False, default='draft')\n"
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
                Book(title="Beta Search", genre="Tech", price=30.0, status="published", author=bob),
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

            repeated_relationship_response = client.post(
                "/api/filterx/books/filter",
                json=[
                    {"field": "author.name", "operation": "eq", "value": "Bob"},
                    {"field": "author.name", "operation": "ilike", "value": "b"},
                ],
                params={"sort_by": "author.name", "order": "asc"},
            )
            assert repeated_relationship_response.status_code == 200
            repeated_payload = repeated_relationship_response.json()
            assert repeated_payload["meta"]["total_items"] == 2

            group_response = client.get("/api/filterx/books/group-by/genre")
            assert group_response.status_code == 200
            assert {row["key"]: row["count"] for row in group_response.json()} == {"Tech": 2, "Business": 1}

            enum_text_response = client.get(
                "/api/filterx/books",
                params={"status_ilike": "publish"},
            )
            assert enum_text_response.status_code == 200
            assert [row["title"] for row in enum_text_response.json()["data"]] == ["Beta Search"]

            boolean_response = client.get(
                "/api/filterx/books",
                params={"is_active_eq": "yes"},
            )
            assert boolean_response.status_code == 200
            assert boolean_response.json()["meta"]["total_items"] == 3

            invalid_boolean = client.get(
                "/api/filterx/books",
                params={"is_active_eq": "sometimes"},
            )
            assert invalid_boolean.status_code == 400
            assert "expected a boolean" in invalid_boolean.json()["detail"]
    finally:
        _purge_app_modules()
        if str(project_root) in sys.path:
            sys.path.remove(str(project_root))


def test_generated_backend_router_applies_security_and_row_predicates(tmp_path: Path) -> None:
    project_root = tmp_path / "secured_runtime_project"
    project_root.mkdir()
    config_path = _write_runtime_project(project_root)

    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["backend"].update(
        {
            "auth_dependency_import": "app.security:get_principal",
            "permission_hook_import": "app.security:check_permission",
            "global_predicate_hooks": ["app.security:tenant_predicate"],
            "entity_predicate_hooks": {},
        }
    )
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    _write_file(
        project_root / "app/security.py",
        "from fastapi import Header\n\n"
        "def get_principal(x_tenant: str = Header(...)):\n"
        "    return x_tenant\n\n"
        "def check_permission(*, principal, request, entity, action):\n"
        "    return principal != 'blocked'\n\n"
        "def tenant_predicate(*, principal, request, entity, model, action):\n"
        "    if entity.get('model') == 'Book':\n"
        "        return model.genre == principal\n"
        "    return None\n",
    )

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
        author = Author(name="Ada")
        session.add_all(
            [
                author,
                Book(title="Tech One", genre="Tech", price=10.0, author=author),
                Book(title="Tech Two", genre="Tech", price=20.0, author=author),
                Book(title="Business One", genre="Business", price=30.0, author=author),
            ]
        )
        session.commit()
        session.close()

        app = importlib.import_module("app.main").app
        with TestClient(app) as client:
            missing_auth = client.get("/api/filterx/books")
            assert missing_auth.status_code == 422

            denied = client.get(
                "/api/filterx/metadata",
                headers={"x-tenant": "blocked"},
            )
            assert denied.status_code == 403

            query_response = client.get(
                "/api/filterx/books",
                headers={"x-tenant": "Tech"},
            )
            assert query_response.status_code == 200
            assert query_response.json()["meta"]["total_items"] == 2

            filter_response = client.post(
                "/api/filterx/books/filter",
                headers={"x-tenant": "Tech"},
                json={
                    "node_type": "condition",
                    "field": "price",
                    "operation": "gt",
                    "value": 15,
                },
            )
            assert filter_response.status_code == 200
            assert [row["title"] for row in filter_response.json()["data"]] == ["Tech Two"]

            group_response = client.get(
                "/api/filterx/books/group-by/genre",
                headers={"x-tenant": "Tech"},
            )
            assert group_response.status_code == 200
            assert group_response.json() == [{"key": "Tech", "count": 2}]
    finally:
        _purge_app_modules()
        if str(project_root) in sys.path:
            sys.path.remove(str(project_root))
