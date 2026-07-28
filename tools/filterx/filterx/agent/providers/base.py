from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


@dataclass
class LLMRequest:
    messages: Sequence[Mapping[str, str]]
    role: str = "compile"
    temperature: float = 0.0
    response_format: str = "json"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    content: str
    provider: str
    model: str
    raw: dict[str, Any] = field(default_factory=dict)


class LLMProviderError(Exception):
    pass


class LLMRetryableError(LLMProviderError):
    pass


class LLMFatalError(LLMProviderError):
    pass


class LLMProvider(ABC):
    name: str
    model: str

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        raise NotImplementedError
