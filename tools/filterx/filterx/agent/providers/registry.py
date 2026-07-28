from __future__ import annotations

from typing import Callable, Type

from .base import LLMFatalError, LLMProvider


_PROVIDERS: dict[str, Type[LLMProvider]] = {}


def register_provider(name: str) -> Callable[[Type[LLMProvider]], Type[LLMProvider]]:
    normalized = name.strip().lower()

    def decorator(provider_cls: Type[LLMProvider]) -> Type[LLMProvider]:
        _PROVIDERS[normalized] = provider_cls
        return provider_cls

    return decorator


def create_provider(name: str, **kwargs: object) -> LLMProvider:
    normalized = name.strip().lower()
    provider_cls = _PROVIDERS.get(normalized)
    if provider_cls is None:
        known = ", ".join(sorted(_PROVIDERS)) or "none"
        raise LLMFatalError(f"Unknown LLM provider '{name}'. Registered providers: {known}.")
    return provider_cls(**kwargs)


def registered_provider_names() -> list[str]:
    return sorted(_PROVIDERS)
