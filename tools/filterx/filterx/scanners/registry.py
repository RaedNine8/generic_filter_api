from __future__ import annotations

from collections.abc import Iterable

from .base import ScannerPlugin


class ScannerRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, ScannerPlugin] = {}

    def register(self, plugin: ScannerPlugin, *, replace: bool = False) -> None:
        key = plugin.name.strip().lower()
        if not key:
            raise ValueError("Scanner plugin name cannot be empty.")
        if key in self._plugins and not replace:
            raise ValueError(f"Scanner plugin '{key}' is already registered.")
        self._plugins[key] = plugin

    def resolve(self, name: str) -> ScannerPlugin:
        key = name.strip().lower()
        try:
            return self._plugins[key]
        except KeyError as exc:
            available = ", ".join(sorted(self._plugins)) or "none"
            raise ValueError(
                f"Unknown FilterX scanner '{name}'. Registered scanners: {available}. "
                "Install or register the scanner plugin, then set scan.framework to its registered name."
            ) from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._plugins))

    def plugins(self) -> Iterable[ScannerPlugin]:
        return tuple(self._plugins[name] for name in sorted(self._plugins))


scanner_registry = ScannerRegistry()
