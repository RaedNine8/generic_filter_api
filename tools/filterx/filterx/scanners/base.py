from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Protocol, runtime_checkable

from filterx.core.ir import FilterxIR


class ScannerExecutionMode(str, Enum):
    IN_PROCESS = "in-process"
    EXISTING_TOOLCHAIN = "existing-toolchain"
    NEW_TOOLCHAIN = "new-toolchain"


@dataclass(frozen=True)
class ScannerContext:
    project_root: Path
    config: Mapping[str, Any]
    timeout_seconds: float = 30.0


class ScannerError(RuntimeError):
    def __init__(self, code: str, message: str, *, context: Mapping[str, Any] | None = None) -> None:
        self.code = code
        self.context = dict(context or {})
        super().__init__(message)


@runtime_checkable
class ScannerPlugin(Protocol):
    name: str
    version: str
    execution_mode: ScannerExecutionMode

    def scan(self, context: ScannerContext) -> FilterxIR:
        ...
