from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from filterx.agent.providers.base import LLMFatalError, LLMProvider, LLMRequest, LLMResponse, LLMRetryableError
from filterx.agent.providers.gemini_provider import GeminiProvider
from filterx.agent.providers.groq_provider import GroqProvider
from filterx.agent.providers.openai_compatible_provider import OpenAICompatibleProvider
from filterx.agent.providers.registry import create_provider, register_provider
from filterx.agent.providers.resilient import ResilientLLMClient


@dataclass
class _FakeResponse:
    status_code: int
    payload: dict[str, Any]
    text: str = ""

    def json(self) -> dict[str, Any]:
        return self.payload


class _FakeAsyncClient:
    response: _FakeResponse
    last_args: tuple[object, ...] = ()
    last_kwargs: dict[str, object] = {}

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout

    async def __aenter__(self) -> "_FakeAsyncClient":
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    async def post(self, *args: object, **kwargs: object) -> _FakeResponse:
        type(self).last_args = args
        type(self).last_kwargs = kwargs
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
    assert "test-key" not in str(_FakeAsyncClient.last_args[0])
    assert _FakeAsyncClient.last_kwargs["headers"] == {"x-goog-api-key": "test-key"}

    request_with_system = LLMRequest(messages=[
        {"role": "system", "content": "Return only JSON."},
        {"role": "user", "content": "hello"},
    ])
    await provider.complete(request_with_system)
    payload = _FakeAsyncClient.last_kwargs["json"]
    assert payload["systemInstruction"]["parts"][0]["text"] == "Return only JSON."

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


@pytest.mark.asyncio
async def test_openai_compatible_provider_supports_keyless_local_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx

    monkeypatch.setattr(httpx, "AsyncClient", _FakeAsyncClient)
    _FakeAsyncClient.response = _FakeResponse(200, {"choices": [{"message": {"content": "{}"}}]})
    provider = OpenAICompatibleProvider(model="qwen2.5:7b", base_url="http://localhost:11434/v1")

    response = await provider.complete(LLMRequest(messages=[{"role": "user", "content": "hello"}]))

    assert response.provider == "openai-compatible"
    assert _FakeAsyncClient.last_args[0] == "http://localhost:11434/v1/chat/completions"
    assert "Authorization" not in _FakeAsyncClient.last_kwargs["headers"]


class _FailingProvider(LLMProvider):
    def __init__(self, error: Exception, name: str) -> None:
        self.error = error
        self.name = name
        self.model = "test"

    async def complete(self, request: LLMRequest) -> LLMResponse:
        raise self.error


@pytest.mark.asyncio
async def test_resilient_client_preserves_all_fatal_failures() -> None:
    client = ResilientLLMClient(_FailingProvider(LLMFatalError("bad key"), "fatal"), max_retries=1)
    with pytest.raises(LLMFatalError, match="bad key"):
        await client.complete(LLMRequest(messages=[]))


@pytest.mark.asyncio
async def test_resilient_client_uses_fallback_after_fatal_primary() -> None:
    class _SuccessProvider(LLMProvider):
        name = "success"
        model = "test"

        async def complete(self, request: LLMRequest) -> LLMResponse:
            return LLMResponse(content="{}", provider=self.name, model=self.model)

    client = ResilientLLMClient(
        _FailingProvider(LLMFatalError("bad key"), "fatal"),
        fallbacks=[_SuccessProvider()],
        max_retries=1,
    )
    response = await client.complete(LLMRequest(messages=[]))
    assert response.provider == "success"
