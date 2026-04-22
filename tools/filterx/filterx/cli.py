from __future__ import annotations

import argparse
import sys
from typing import Sequence

from filterx.commands import backend, db, frontend, install, rollback, scan, validate


def _add_global_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project-root", default=".", help="Project root path")
    parser.add_argument("--config", default=None, help="Path to filterx.yaml")
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=None, help="Preview only")
    parser.add_argument("--check", action="store_true", help="Validation mode (no writes)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--verbose", action="store_true", help="Verbose logs")
    parser.add_argument("--yes", action="store_true", help="Non-interactive mode")
    parser.add_argument("--fail-on-warning", action="store_true", help="Treat warnings as errors")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="filterx", description="FilterX smart bootstrap CLI")
    _add_global_options(parser)

    sub = parser.add_subparsers(dest="command", required=True)

    scan_p = sub.add_parser("scan", help="Analyze models/routes and emit scan artifacts")
    _add_global_options(scan_p)
    scan_p.add_argument("--entities", default=None, help="Comma-separated entity allowlist")
    scan_p.add_argument("--exclude-entities", default=None, help="Comma-separated entity denylist")
    scan_p.add_argument("--max-depth", type=int, default=None, help="Max relationship traversal depth")
    scan_p.set_defaults(handler=scan.run)

    backend_p = sub.add_parser("backend", help="Backend integration commands")
    _add_global_options(backend_p)
    backend_sub = backend_p.add_subparsers(dest="backend_command", required=True)
    backend_install = backend_sub.add_parser("install", help="Install backend integration")
    _add_global_options(backend_install)
    backend_install.add_argument("--entities", default=None, help="Comma-separated entity allowlist")
    backend_install.add_argument("--mount-file", default=None, help="Override backend mount file path")
    backend_install.add_argument("--mount-anchor", default=None, help="Override backend mount anchor")
    backend_install.add_argument("--api-prefix", default=None, help="Override backend API prefix")
    backend_install.add_argument("--force", action="store_true", help="Allow overwrite of changed generated files")
    backend_install.add_argument("--no-mount", action="store_true", help="Generate files without patching mount file")
    backend_install.set_defaults(handler=backend.run_install)
    backend_validate = backend_sub.add_parser("validate", help="Validate backend integration")
    _add_global_options(backend_validate)
    backend_validate.set_defaults(handler=backend.run_validate)
    backend_remove = backend_sub.add_parser("remove", help="Remove backend integration")
    _add_global_options(backend_remove)
    backend_remove.set_defaults(handler=backend.run_remove)

    frontend_p = sub.add_parser("frontend", help="Frontend integration commands")
    _add_global_options(frontend_p)
    frontend_sub = frontend_p.add_subparsers(dest="frontend_command", required=True)
    frontend_install = frontend_sub.add_parser("install", help="Install frontend integration")
    _add_global_options(frontend_install)
    frontend_install.add_argument("--entities", default=None, help="Comma-separated entity allowlist")
    frontend_install.add_argument("--routes-file", default=None, help="Override frontend routes file path")
    frontend_install.add_argument("--routes-anchor", default=None, help="Override frontend routes anchor")
    frontend_install.add_argument("--app-config-file", default=None, help="Override frontend app config file path")
    frontend_install.add_argument("--app-config-anchor", default=None, help="Override frontend app config anchor")
    frontend_install.add_argument("--style", default=None, help="Entity naming style: kebab, camel, snake")
    frontend_install.add_argument("--force", action="store_true", help="Allow overwrite of changed generated files")
    frontend_install.add_argument("--no-route-patch", action="store_true", help="Generate files without patching routes file")
    frontend_install.set_defaults(handler=frontend.run_install)
    frontend_validate = frontend_sub.add_parser("validate", help="Validate frontend integration")
    _add_global_options(frontend_validate)
    frontend_validate.set_defaults(handler=frontend.run_validate)
    frontend_remove = frontend_sub.add_parser("remove", help="Remove frontend integration")
    _add_global_options(frontend_remove)
    frontend_remove.add_argument("--list", action="store_true", help="List available frontend install patch bundles")
    frontend_remove.add_argument("--patch-id", default=None, help="Explicit frontend patch id to rollback")
    frontend_remove.set_defaults(handler=frontend.run_remove)

    db_p = sub.add_parser("db", help="Database integration commands")
    _add_global_options(db_p)
    db_sub = db_p.add_subparsers(dest="db_command", required=True)
    db_install = db_sub.add_parser("install", help="Install DB integration")
    _add_global_options(db_install)
    db_install.add_argument("--saved-filters", action=argparse.BooleanOptionalAction, default=None, help="Enable saved filters persistence migration")
    db_install.add_argument("--shared-filters", action=argparse.BooleanOptionalAction, default=None, help="Enable shared filters persistence migration")
    db_install.add_argument("--auditing", action=argparse.BooleanOptionalAction, default=None, help="Enable auditing migration")
    db_install.add_argument("--migration-dir", default=None, help="Override migration directory")
    db_install.add_argument("--name", default=None, help="Optional migration label")
    db_install.add_argument("--apply", action="store_true", help="Apply migration after generation (reserved)")
    db_install.set_defaults(handler=db.run_install)
    db_validate = db_sub.add_parser("validate", help="Validate DB integration")
    _add_global_options(db_validate)
    db_validate.set_defaults(handler=db.run_validate)

    install_p = sub.add_parser("install", help="Orchestrated install")
    _add_global_options(install_p)
    install_p.set_defaults(handler=install.run)

    validate_p = sub.add_parser("validate", help="Cross-layer validate")
    _add_global_options(validate_p)
    validate_p.set_defaults(handler=validate.run)

    rollback_p = sub.add_parser("rollback", help="Rollback latest patch bundle")
    _add_global_options(rollback_p)
    rollback_p.add_argument("--list", action="store_true", help="List available patch bundles")
    rollback_p.add_argument("--patch-id", default=None, help="Explicit patch bundle id")
    rollback_p.set_defaults(handler=rollback.run)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 1
    return int(handler(args) or 0)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
