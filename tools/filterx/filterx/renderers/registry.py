from __future__ import annotations

from .base import RendererPlugin, RendererTarget


class RendererRegistry:
    def __init__(self) -> None:
        self._plugins: dict[tuple[RendererTarget, str], RendererPlugin] = {}

    def register(self, plugin: RendererPlugin, *, replace: bool = False) -> None:
        name = plugin.name.strip().lower()
        if not name:
            raise ValueError("Renderer plugin name cannot be empty.")
        key = (plugin.target, name)
        if key in self._plugins and not replace:
            raise ValueError(f"{plugin.target.value.title()} renderer '{name}' is already registered.")
        self._plugins[key] = plugin

    def resolve(self, target: RendererTarget | str, name: str) -> RendererPlugin:
        normalized_target = RendererTarget(target)
        normalized_name = name.strip().lower()
        key = (normalized_target, normalized_name)
        try:
            return self._plugins[key]
        except KeyError as exc:
            available = ", ".join(self.names(normalized_target)) or "none"
            raise ValueError(
                f"Unknown FilterX {normalized_target.value} renderer '{name}'. "
                f"Registered {normalized_target.value} renderers: {available}. "
                f"Install or register the renderer plugin, then set "
                f"{normalized_target.value}.framework to its registered name."
            ) from exc

    def names(self, target: RendererTarget | str) -> tuple[str, ...]:
        normalized_target = RendererTarget(target)
        return tuple(sorted(name for plugin_target, name in self._plugins if plugin_target == normalized_target))


renderer_registry = RendererRegistry()
