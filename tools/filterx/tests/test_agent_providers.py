from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from filterx.agent.providers.base import LLMFatalError, LLMRequest, LLMRetryableError
from filterx.agent.providers.gemini_provider import GeminiProvider
from filterx.agent.providers.groq_provider import GroqProvider
from filterx.agent.providers.registry import create_provider, register_provider


@dataclass
class _FakeResponse:
    status_code: int
    payload: dict[str, Any]
    text: str = ""

    def json(self) -> dict[str, Any]:
        return self.payload


class _FakeAsyncClient:
    response: _FakeResponse

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout

    async def __aenter__(self) -> "_FakeAsyncClient":
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    async def post(self, *args: object, **kwargs: object) -> _FakeResponse:
        return self.response


@pytest.mark.asyncio
async def test_groq_provider_success_and_error_classification(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr(httpx, "AsyncClient", _FakeAsyncClient)
    provider = GroqProvider(api_key_env="GROQ_API_KEY", model="test-model")
    request = LLMRequest(messages=[{"role": "user", "content": "hello"}])

    _FakeAsyncClient.response = _FakeResponse(200, {"choices": [{"message": {"content": "{}"}}]})
    response = await provider.complete(request)
    assert response.content == "{}"
    assert response.provider == "groq"

    _FakeAsyncClient.response = _FakeResponse(429, {}, "rate limited")
    with pytest.raises(LLMRetryableError):
        await provider.complete(request)

    _FakeAsyncClient.response = _FakeResponse(401, {}, "unauthorized")
    with pytest.raises(LLMFatalError):
        await provider.complete(request)


@pytest.mark.asyncio
async def test_gemini_provider_success_and_error_classification(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(httpx, "AsyncClient", _FakeAsyncClient)
    provider = GeminiProvider(api_key_env="GEMINI_API_KEY", model="gemini-test")
    request = LLMRequest(messages=[{"role": "user", "content": "hello"}])

    _FakeAsyncClient.response = _FakeResponse(200, {"candidates": [{"content": {"parts": [{"text": "{}"}]}}]})
    response = await provider.complete(request)
    assert response.content == "{}"
    assert response.provider == "gemini"

    _FakeAsyncClient.response = _FakeResponse(500, {}, "server error")
    with pytest.raises(LLMRetryableError):
        await provider.complete(request)

    _FakeAsyncClient.response = _FakeResponse(400, {}, "bad request")
    with pytest.raises(LLMFatalError):
        await provider.complete(request)


def test_provider_registry_accepts_third_provider_without_pipeline_changes() -> None:
    @register_provider("dummy-third")
    class DummyThirdProvider(GroqProvider):
        pass

    provider = create_provider("dummy-third", api_key_env="DUMMY_KEY", model="dummy-model")
    assert provider.name == "groq"
