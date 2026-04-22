from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from filterx.core.config import load_effective_config
from filterx.core.patcher import PatchOp, apply_patch_operations


def _resolve_dry_run(args: Any, cfg: dict[str, Any]) -> bool:
    dry_run = getattr(args, "dry_run", None)
    if dry_run is None:
        return bool(cfg["safety"].get("dry_run_default", True))
    return bool(dry_run)


def _resolve_features(args: Any, cfg: dict[str, Any]) -> dict[str, bool]:
    features = dict(cfg["database"].get("features", {}))
    for field in ("saved_filters", "shared_filters", "auditing"):
        value = getattr(args, field, None)
        if value is not None:
            features[field] = bool(value)
    return features


def _expected_tables(features: dict[str, bool]) -> list[str]:
    expected: list[str] = []
    if features.get("saved_filters", False):
        expected.append("filterx_saved_filters")
    if features.get("shared_filters", False):
        expected.append("filterx_shared_filters")
    if features.get("auditing", False):
        expected.append("filterx_filter_audit_logs")
    return expected


def _render_upgrade_block(features: dict[str, bool]) -> str:
    statements: list[str] = []

    if features.get("saved_filters", False):
        statements.append(
            """
    op.create_table(
        'filterx_saved_filters',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('model_name', sa.String(length=255), nullable=False),
        sa.Column('filters', sa.JSON(), nullable=True),
        sa.Column('filter_tree', sa.JSON(), nullable=True),
        sa.Column('sort_by', sa.String(length=255), nullable=True),
        sa.Column('sort_order', sa.String(length=16), nullable=True),
        sa.Column('page_size', sa.Integer(), nullable=True),
        sa.Column('search_query', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
            """.strip("\n")
        )

    if features.get("shared_filters", False):
        statements.append(
            """
    op.create_table(
        'filterx_shared_filters',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('saved_filter_id', sa.Integer(), sa.ForeignKey('filterx_saved_filters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('principal_type', sa.String(length=32), nullable=False),
        sa.Column('principal_id', sa.String(length=128), nullable=False),
        sa.Column('permission', sa.String(length=32), nullable=False, server_default=sa.text("'read'")),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_filterx_shared_filters_saved_filter_id', 'filterx_shared_filters', ['saved_filter_id'])
            """.strip("\n")
        )

    if features.get("auditing", False):
        statements.append(
            """
    op.create_table(
        'filterx_filter_audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('action', sa.String(length=64), nullable=False),
        sa.Column('actor', sa.String(length=255), nullable=True),
        sa.Column('model_name', sa.String(length=255), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_filterx_filter_audit_logs_model_name', 'filterx_filter_audit_logs', ['model_name'])
            """.strip("\n")
        )

    if not statements:
        return "    pass"
    return "\n\n".join(statements)


def _render_downgrade_block(features: dict[str, bool]) -> str:
    statements: list[str] = []

    if features.get("auditing", False):
        statements.append("    op.drop_index('ix_filterx_filter_audit_logs_model_name', table_name='filterx_filter_audit_logs')")
        statements.append("    op.drop_table('filterx_filter_audit_logs')")

    if features.get("shared_filters", False):
        statements.append("    op.drop_index('ix_filterx_shared_filters_saved_filter_id', table_name='filterx_shared_filters')")
        statements.append("    op.drop_table('filterx_shared_filters')")

    if features.get("saved_filters", False):
        statements.append("    op.drop_table('filterx_saved_filters')")

    if not statements:
        return "    pass"
    return "\n".join(statements)


def _render_migration(features: dict[str, bool]) -> str:
    upgrade_block = _render_upgrade_block(features)
    downgrade_block = _render_downgrade_block(features)

    return (
        '"""FilterX generated persistence migration.\n\n'
        "This migration is additive and non-destructive by design.\n"
        '"""\n\n'
        "from __future__ import annotations\n\n"
        "import sqlalchemy as sa\n"
        "from alembic import op\n\n"
        "# revision identifiers, used by Alembic.\n"
        "revision = 'filterx_generated_persistence'\n"
        "down_revision = None\n"
        "branch_labels = None\n"
        "depends_on = None\n\n"
        f"# feature_flags = {features}\n\n"
        "\n"
        "def upgrade() -> None:\n"
        f"{upgrade_block}\n\n"
        "\n"
        "def downgrade() -> None:\n"
        f"{downgrade_block}\n"
    )


def run_install(args: Any) -> int:
    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config).resolve() if args.config else None
    effective = load_effective_config(project_root, config_path)
    cfg = effective.raw

    if not cfg["database"].get("enabled", False):
        if args.json:
            print(json.dumps({"skipped": True, "reason": "database disabled in config"}, indent=2))
        else:
            print("FilterX DB install skipped: database.enabled is false.")
        return 0

    dry_run = _resolve_dry_run(args, cfg)
    check_mode = bool(getattr(args, "check", False))
    strict_conflict_mode = bool(cfg["safety"].get("strict_conflict_mode", True))

    migration_dir = str(getattr(args, "migration_dir", None) or cfg["database"].get("migration_dir", "alembic/versions"))
    migration_file = Path(migration_dir).as_posix().rstrip("/") + "/filterx_generated_persistence.py"
    features = _resolve_features(args, cfg)

    result = apply_patch_operations(
        project_root=project_root,
        operations=[
            PatchOp(
                kind="generated_file",
                path=migration_file,
                content=_render_migration(features),
                description="Generate FilterX persistence migration",
            )
        ],
        manifest_path=project_root / cfg["safety"]["idempotency_manifest"],
        patch_dir=project_root / cfg["output"]["patch_dir"],
        dry_run=dry_run,
        check_mode=check_mode,
        strict_conflict_mode=strict_conflict_mode,
        description="db.install",
    )

    payload = {
        "dry_run": result.dry_run,
        "check_mode": check_mode,
        "patch_id": result.patch_id,
        "migration_file": str((project_root / migration_file).resolve()),
        "features": features,
        "applied_ops": result.applied_ops,
        "skipped_ops": result.skipped_ops,
        "issues": [
            {"code": issue.code, "message": issue.message, "context": issue.context}
            for issue in result.issues
        ],
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("FilterX DB install completed.")
        print(f"- Dry run: {payload['dry_run']}")
        print(f"- Migration file: {payload['migration_file']}")

    if result.has_conflicts:
        return 3
    if getattr(args, "fail_on_warning", False) and result.issues:
        return 3
    return 0


def run_validate(args: Any) -> int:
    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config).resolve() if args.config else None
    effective = load_effective_config(project_root, config_path)
    cfg = effective.raw

    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    if cfg["database"].get("enabled", False):
        features = dict(cfg["database"].get("features", {}))
        migration_dir = str(cfg["database"].get("migration_dir", "alembic/versions"))
        migration_file = project_root / Path(migration_dir).as_posix().rstrip("/") / "filterx_generated_persistence.py"
        if not migration_file.exists():
            errors.append({"code": "DB_MIGRATION_FILE_MISSING", "path": str(migration_file)})
        else:
            content = migration_file.read_text(encoding="utf-8")
            for table_name in _expected_tables(features):
                if f"op.create_table(\n        '{table_name}'" not in content:
                    errors.append(
                        {
                            "code": "DB_MIGRATION_EXPECTED_CREATE_TABLE_MISSING",
                            "path": str(migration_file),
                            "table": table_name,
                        }
                    )
                if f"op.drop_table('{table_name}')" not in content:
                    errors.append(
                        {
                            "code": "DB_MIGRATION_EXPECTED_DROP_TABLE_MISSING",
                            "path": str(migration_file),
                            "table": table_name,
                        }
                    )
            if "def downgrade()" not in content:
                warnings.append(
                    {
                        "code": "DB_MIGRATION_DOWNGRADE_MISSING",
                        "path": str(migration_file),
                    }
                )

    payload = {
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings),
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("FilterX DB validation completed.")
        print(f"- Errors: {payload['error_count']}")
        print(f"- Warnings: {payload['warning_count']}")

    if payload["errors"]:
        return 4
    if getattr(args, "fail_on_warning", False) and payload["warnings"]:
        return 3
    return 0
