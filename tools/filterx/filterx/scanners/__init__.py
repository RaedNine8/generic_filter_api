from __future__ import annotations

from .base import ScannerContext, ScannerError, ScannerExecutionMode, ScannerPlugin
from .jpa import JPAScannerPlugin
from .prisma import PrismaScannerPlugin
from .registry import ScannerRegistry, scanner_registry
from .sqlalchemy import SQLAlchemyScannerPlugin

scanner_registry.register(SQLAlchemyScannerPlugin())
scanner_registry.register(PrismaScannerPlugin())
scanner_registry.register(JPAScannerPlugin())


def scan_to_ir(context: ScannerContext, scanner_name: str = "sqlalchemy"):
    return scanner_registry.resolve(scanner_name).scan(context)


__all__ = [
    "ScannerContext",
    "ScannerError",
    "ScannerExecutionMode",
    "ScannerPlugin",
    "ScannerRegistry",
    "scan_to_ir",
    "scanner_registry",
]
