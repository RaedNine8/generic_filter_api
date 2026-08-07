from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping, Sequence

from filterx.core.ir import FilterxIR, SecurityHooksIR, ir_from_dict, validate_ir

from .base import ScannerContext, ScannerError, ScannerExecutionMode
from .subprocess import SubprocessScannerPlugin


class PrismaScannerPlugin(SubprocessScannerPlugin):
    name = "prisma"
    version = "1.0.0"
    execution_mode = ScannerExecutionMode.EXISTING_TOOLCHAIN

    def _settings(self, context: ScannerContext) -> Mapping[str, Any]:
        return context.config.get("scan", {}).get("prisma", {})

    def _schema_path(self, context: ScannerContext) -> Path:
        configured = str(self._settings(context).get("schema", "prisma/schema.prisma"))
        return (context.project_root / configured).resolve()

    def _package_path(self, context: ScannerContext) -> Path:
        configured = str(self._settings(context).get("package_json", "package.json"))
        return (context.project_root / configured).resolve()

    def _client_marker(self, context: ScannerContext) -> Path:
        configured = self._settings(context).get("client_marker")
        if configured:
            return (context.project_root / str(configured)).resolve()
        candidates = (
            context.project_root / "node_modules/.prisma/client/index.js",
            context.project_root / "node_modules/.prisma/client/default.js",
        )
        return next((candidate.resolve() for candidate in candidates if candidate.exists()), candidates[0].resolve())

    def command(self, context: ScannerContext) -> Sequence[str]:
        schema_path = self._schema_path(context)
        package_path = self._package_path(context)
        if not schema_path.exists():
            raise ScannerError(
                "PRISMA_SCHEMA_MISSING",
                f"Prisma schema was not found at '{schema_path}'. Set scan.prisma.schema to the correct path.",
                context={"path": str(schema_path)},
            )
        if not package_path.exists():
            raise ScannerError(
                "PRISMA_PACKAGE_MISSING",
                f"Prisma project package.json was not found at '{package_path}'.",
                context={"path": str(package_path)},
            )
        marker = self._client_marker(context)
        allow_stale = bool(self._settings(context).get("allow_stale_client", False))
        if not marker.exists() and not allow_stale:
            raise ScannerError(
                "PRISMA_CLIENT_MISSING",
                "The generated Prisma client was not found. Run 'npx prisma generate' and retry, "
                "or set scan.prisma.allow_stale_client only for schema-only inspection.",
                context={"expected_marker": str(marker)},
            )
        if marker.exists() and schema_path.stat().st_mtime > marker.stat().st_mtime and not allow_stale:
            raise ScannerError(
                "PRISMA_CLIENT_STALE",
                "schema.prisma is newer than the generated Prisma client. Run 'npx prisma generate' and retry.",
                context={"schema": str(schema_path), "client_marker": str(marker)},
            )
        helper = Path(__file__).parents[1] / "reference_runtime/scanners/prisma_scanner.mjs"
        node = str(self._settings(context).get("node_command", "node"))
        return (node, str(helper), str(schema_path), str(package_path))

    def decode_ir(self, payload: Mapping[str, Any]) -> FilterxIR:
        return ir_from_dict(payload)

    def scan(self, context: ScannerContext) -> FilterxIR:
        ir = super().scan(context)
        backend = context.config.get("backend", {})
        security = SecurityHooksIR(
            identity=backend.get("identity_middleware_import"),
            row_predicates=tuple(str(item) for item in backend.get("global_predicate_hooks") or []),
            entity_row_predicates=tuple(
                (str(name), tuple(str(item) for item in hooks))
                for name, hooks in sorted((backend.get("entity_predicate_hooks") or {}).items())
            ),
            field_visibility=backend.get("field_visibility_hook_import"),
        )
        respect_soft_delete = bool(context.config.get("scan", {}).get("respect_soft_delete", False))
        entities = tuple(
            replace(
                entity,
                soft_delete=replace(
                    entity.soft_delete,
                    respected=respect_soft_delete and entity.soft_delete.field is not None,
                ),
            )
            for entity in ir.entities
        )
        resolved = replace(ir, entities=entities, security=security)
        validate_ir(resolved)
        return resolved
