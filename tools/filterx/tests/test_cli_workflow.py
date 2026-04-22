from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from filterx.commands import backend, install, rollback, scan


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_project_files(project_root: Path, include_anchor: bool, add_route_conflict: bool) -> None:
    _write_file(project_root / "app/__init__.py", "")
    _write_file(project_root / "app/models/__init__.py", "")

    _write_file(
        project_root / "app/database.py",
        "from __future__ import annotations\n\n"
        "from sqlalchemy.orm import declarative_base\n\n"
        "Base = declarative_base()\n\n"
        "\n"
        "def get_db():\n"
        "    raise RuntimeError('test stub')\n",
    )

    _write_file(
        project_root / "app/models/author.py",
        "from __future__ import annotations\n\n"
        "from sqlalchemy import Column, Integer, String\n"
        "from sqlalchemy.orm import relationship\n\n"
        "from app.database import Base\n\n"
        "\n"
        "class Author(Base):\n"
        "    __tablename__ = 'authors'\n"
        "\n"
        "    id = Column(Integer, primary_key=True)\n"
        "    name = Column(String, nullable=False)\n"
        "    books = relationship('Book', back_populates='author')\n",
    )

    _write_file(
        project_root / "app/models/book.py",
        "from __future__ import annotations\n\n"
        "from sqlalchemy import Column, ForeignKey, Integer, String\n"
        "from sqlalchemy.orm import relationship\n\n"
        "from app.database import Base\n\n"
        "\n"
        "class Book(Base):\n"
        "    __tablename__ = 'books'\n"
        "\n"
        "    id = Column(Integer, primary_key=True)\n"
        "    title = Column(String, nullable=False)\n"
        "    author_id = Column(Integer, ForeignKey('authors.id'))\n"
        "\n"
        "    author = relationship('Author', back_populates='books')\n",
    )

    route_conflict_block = ""
    if add_route_conflict:
        route_conflict_block = (
            "@app.get('/api/filterx/metadata')\n"
            "def conflicting_metadata_route():\n"
            "    return {'message': 'conflict'}\n\n"
        )

    anchor = "# FILTERX:ROUTER_MOUNT\n" if include_anchor else ""
    _write_file(
        project_root / "app/main.py",
        "from __future__ import annotations\n\n"
        "from fastapi import FastAPI\n\n"
        "app = FastAPI()\n\n"
        "@app.get('/health')\n"
        "def health():\n"
        "    return {'ok': True}\n\n"
        f"{route_conflict_block}"
        f"{anchor}",
    )


def _write_config(project_root: Path) -> Path:
    config_content = (
        "version: 1\n\n"
        "project:\n"
        "  name: synthetic_project\n"
        "  root: .\n"
        "  backend_root: app\n"
        "  frontend_root: frontend\n"
        "  alembic_ini: alembic.ini\n\n"
        "python:\n"
        "  app_import: app.main:app\n"
        "  base_class_import: app.database:Base\n"
        "  models_package: app.models\n"
        "  session_dependency_import: app.database:get_db\n"
        "  sqlalchemy_url_env: DATABASE_URL\n\n"
        "backend:\n"
        "  enabled: true\n"
        "  api_prefix: /api\n"
        "  generated_package: app/filterx_generated\n"
        "  mount_file: app/main.py\n"
        "  mount_anchor: '# FILTERX:ROUTER_MOUNT'\n"
        "  entities: []\n"
        "  exclude_entities: []\n"
        "  global_predicate_hooks: []\n\n"
        "frontend:\n"
        "  enabled: false\n"
        "  workspace_root: frontend\n"
        "  generated_root: frontend/src/app/filterx-generated\n"
        "  routes_file: frontend/src/app/app.routes.ts\n"
        "  routes_anchor: '// FILTERX:ROUTES'\n"
        "  app_config_file: frontend/src/app/app.config.ts\n"
        "  app_config_anchor: '// FILTERX:PROVIDERS'\n"
        "  entity_style: kebab\n\n"
        "database:\n"
        "  enabled: false\n"
        "  provider: alembic\n"
        "  migration_dir: alembic/versions\n"
        "  features:\n"
        "    saved_filters: true\n"
        "    shared_filters: false\n"
        "    auditing: false\n\n"
        "scan:\n"
        "  max_relationship_depth: 3\n"
        "  include_views: false\n"
        "  include_hybrid_properties: false\n"
        "  respect_soft_delete: true\n\n"
        "safety:\n"
        "  dry_run_default: false\n"
        "  require_anchor_comments: true\n"
        "  idempotency_manifest: .filterx/manifest.json\n"
        "  allow_overwrite_generated: true\n"
        "  strict_conflict_mode: true\n\n"
        "output:\n"
        "  scan_file: .filterx/scan.json\n"
        "  plan_file: .filterx/plan.json\n"
        "  diagnostics_file: .filterx/diagnostics.json\n"
        "  patch_dir: .filterx/patches\n"
    )
    config_path = project_root / "filterx.yaml"
    _write_file(config_path, config_content)
    return config_path


def _args(project_root: Path, config_path: Path, **overrides: object) -> SimpleNamespace:
    base: dict[str, object] = {
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
        "list": False,
        "patch_id": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _setup_synthetic_project(tmp_path: Path, include_anchor: bool = True, add_route_conflict: bool = False) -> Path:
    project_root = tmp_path / "synthetic_project"
    project_root.mkdir(parents=True, exist_ok=True)
    _write_project_files(project_root, include_anchor=include_anchor, add_route_conflict=add_route_conflict)
    _write_config(project_root)
    return project_root


def test_full_workflow_scan_install_validate_and_rollback(tmp_path: Path) -> None:
    project_root = _setup_synthetic_project(tmp_path, include_anchor=True, add_route_conflict=False)
    config_path = project_root / "filterx.yaml"

    assert scan.run(_args(project_root, config_path)) == 0
    assert (project_root / ".filterx/scan.json").exists()
    assert (project_root / ".filterx/diagnostics.json").exists()
    assert (project_root / ".filterx/plan.json").exists()

    assert backend.run_install(_args(project_root, config_path)) == 0
    assert backend.run_validate(_args(project_root, config_path)) == 0

    main_content = (project_root / "app/main.py").read_text(encoding="utf-8")
    assert "from app.filterx_generated.router import router as filterx_generated_router" in main_content
    assert "app.include_router(filterx_generated_router)" in main_content

    assert rollback.run(_args(project_root, config_path, list=True)) == 0
    assert rollback.run(_args(project_root, config_path)) == 0

    assert not (project_root / "app/filterx_generated/router.py").exists()
    assert backend.run_validate(_args(project_root, config_path)) == 4


def test_orchestrated_install_runs_scan_backend_and_validate(tmp_path: Path) -> None:
    project_root = _setup_synthetic_project(tmp_path, include_anchor=True, add_route_conflict=False)
    config_path = project_root / "filterx.yaml"

    assert install.run(_args(project_root, config_path)) == 0
    assert (project_root / ".filterx/scan.json").exists()
    assert (project_root / "app/filterx_generated/metadata.py").exists()


def test_backend_install_blocks_on_route_path_conflict(tmp_path: Path) -> None:
    project_root = _setup_synthetic_project(tmp_path, include_anchor=True, add_route_conflict=True)
    config_path = project_root / "filterx.yaml"

    assert scan.run(_args(project_root, config_path)) == 0
    assert backend.run_install(_args(project_root, config_path)) == 3
    assert not (project_root / "app/filterx_generated/router.py").exists()


def test_backend_install_is_idempotent_for_mount_snippet(tmp_path: Path) -> None:
    project_root = _setup_synthetic_project(tmp_path, include_anchor=True, add_route_conflict=False)
    config_path = project_root / "filterx.yaml"

    assert scan.run(_args(project_root, config_path)) == 0
    assert backend.run_install(_args(project_root, config_path)) == 0
    assert backend.run_install(_args(project_root, config_path)) == 0

    main_content = (project_root / "app/main.py").read_text(encoding="utf-8")
    assert main_content.count("from app.filterx_generated.router import router as filterx_generated_router") == 1
    assert main_content.count("app.include_router(filterx_generated_router)") == 1


def test_orchestrated_install_accepts_install_parser_style_namespace(tmp_path: Path) -> None:
    project_root = _setup_synthetic_project(tmp_path, include_anchor=True, add_route_conflict=False)
    config_path = project_root / "filterx.yaml"

    # Simulate install command args that do not include scan-specific options.
    args = SimpleNamespace(
        project_root=str(project_root),
        config=str(config_path),
        dry_run=False,
        check=False,
        json=True,
        verbose=False,
        yes=True,
        fail_on_warning=False,
    )

    assert install.run(args) == 0
    assert (project_root / ".filterx/scan.json").exists()
    assert (project_root / "app/filterx_generated/router.py").exists()
