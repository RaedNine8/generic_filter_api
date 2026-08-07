from __future__ import annotations

import json
import subprocess
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, Mapping

from filterx.core.ir import FilterxIR, IRValidationError

from .base import ScannerContext, ScannerError, ScannerExecutionMode


class SubprocessScannerPlugin(ABC):
    name: str
    version: str
    execution_mode: ScannerExecutionMode

    @abstractmethod
    def command(self, context: ScannerContext) -> Sequence[str]:
        ...

    @abstractmethod
    def decode_ir(self, payload: Mapping[str, Any]) -> FilterxIR:
        ...

    def scan(self, context: ScannerContext) -> FilterxIR:
        command = tuple(self.command(context))
        if not command:
            raise ScannerError("SCANNER_COMMAND_EMPTY", f"Scanner '{self.name}' did not provide a command.")
        try:
            result = subprocess.run(
                command,
                cwd=context.project_root,
                capture_output=True,
                text=True,
                timeout=context.timeout_seconds,
                check=False,
            )
        except FileNotFoundError as exc:
            runtime = command[0]
            mode = self.execution_mode.value
            raise ScannerError(
                "SCANNER_RUNTIME_MISSING",
                f"Scanner '{self.name}' requires '{runtime}', but it was not found. "
                f"Install the required {mode} runtime and retry.",
                context={"runtime": runtime, "execution_mode": mode},
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise ScannerError(
                "SCANNER_TIMEOUT",
                f"Scanner '{self.name}' exceeded the {context.timeout_seconds:g}-second timeout.",
                context={"timeout_seconds": context.timeout_seconds},
            ) from exc

        if result.returncode != 0:
            raise ScannerError(
                "SCANNER_PROCESS_FAILED",
                f"Scanner '{self.name}' exited with status {result.returncode}. "
                "Resolve the reported toolchain or project error and retry.",
                context={"exit_code": result.returncode, "stderr": result.stderr.strip()},
            )
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise ScannerError(
                "SCANNER_OUTPUT_INVALID",
                f"Scanner '{self.name}' did not return valid FilterX IR JSON.",
                context={"error": str(exc)},
            ) from exc
        try:
            return self.decode_ir(payload)
        except (KeyError, TypeError, ValueError, IRValidationError) as exc:
            raise ScannerError(
                "SCANNER_IR_INVALID",
                f"Scanner '{self.name}' returned an invalid FilterX IR document.",
                context={"error": str(exc)},
            ) from exc
