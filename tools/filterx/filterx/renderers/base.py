from __future__ import annotations

from enum import Enum
from typing import Any, Protocol, runtime_checkable


class RendererTarget(str, Enum):
    BACKEND = "backend"
    FRONTEND = "frontend"


@runtime_checkable
class RendererPlugin(Protocol):
    name: str
    version: str
    target: RendererTarget

    def install(self, args: Any) -> int:
        ...

    def validate(self, args: Any) -> int:
        ...

    def remove(self, args: Any) -> int:
        ...
