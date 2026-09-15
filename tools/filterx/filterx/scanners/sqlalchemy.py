from __future__ import annotations

from filterx.core.ir import FilterxIR

from .base import ScannerContext, ScannerExecutionMode


class SQLAlchemyScannerPlugin:
    name = "sqlalchemy"
    version = "1.0.0"
    execution_mode = ScannerExecutionMode.IN_PROCESS

    def scan(self, context: ScannerContext) -> FilterxIR:
        # Imported lazily to keep the public registry independent from the
        # legacy scanner module while that compatibility path remains active.
        from filterx.core.scanner import run_scan

        result = run_scan(dict(context.config), context.project_root)
        if result.ir is None:  # pragma: no cover - defensive contract check
            raise RuntimeError("The SQLAlchemy scanner did not produce FilterX IR.")
        return result.ir
