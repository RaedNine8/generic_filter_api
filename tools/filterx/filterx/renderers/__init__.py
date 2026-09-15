from __future__ import annotations

from .base import RendererPlugin, RendererTarget
from .builtin import AngularRenderer, FastAPISQLAlchemyRenderer
from .express_prisma import ExpressPrismaRenderer
from .registry import RendererRegistry, renderer_registry
from .spring_boot_jpa import SpringBootJPARenderer
from .web_frontends import NextjsRenderer, ReactViteRenderer, VueRenderer

renderer_registry.register(FastAPISQLAlchemyRenderer())
renderer_registry.register(AngularRenderer())
renderer_registry.register(ExpressPrismaRenderer())
renderer_registry.register(SpringBootJPARenderer())
renderer_registry.register(ReactViteRenderer())
renderer_registry.register(NextjsRenderer())
renderer_registry.register(VueRenderer())

__all__ = [
    "RendererPlugin",
    "RendererRegistry",
    "RendererTarget",
    "renderer_registry",
]
