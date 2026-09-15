from __future__ import annotations

import os
from typing import Any

from .base import LLMFatalError, LLMProvider, LLMRequest, LLMResponse, LLMRetryableError
from .registry import register_provider


@register_provider("openai")
@register_provider("openai-compatible")
class OpenAICompatibleProvider(LLMProvider):
    """Adapter for OpenAI-compatible chat completion APIs.

    This works with hosted services and local servers such as Ollama, LM Studio,
    LocalAI, and vLLM. Local endpoints can omit ``api_key_env`` entirely.
    """

    def __init__(
        self,
        model: str,
        api_key_env: str = "",
        timeout_seconds: float = 30.0,
        base_url: str = "http://localhost:11434/v1",
        require_api_key: bool = False,
        json_mode: bool = True,
    ) -> None:
        self.name = "openai-compatible"
        self.model = model
        self.api_key_env = api_key_env
        self.timeout_seconds = timeout_seconds
        self.base_url = base_url.rstrip("/")
        self.require_api_key = require_api_key
        self.json_mode = json_mode

    async def complete(self, request: LLMRequest) -> LLMResponse:
        api_key = os.getenv(self.api_key_env) if self.api_key_env else None
        if self.require_api_key and not api_key:
            variable = self.api_key_env or "the configured API key environment variable"
            raise LLMFatalError(f"Missing API key environment variable: {variable}")

        try:
            import httpx
        except ImportError as exc:  # pragma: no cover
            raise LLMFatalError("The 'httpx' package is required for OpenAICompatibleProvider.") from exc

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": list(request.messages),
            "temperature": request.temperature,
        }
        if request.response_format == "json" and self.json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        url = self.base_url if self.base_url.endswith("/chat/completions") else f"{self.base_url}/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            raise LLMRetryableError("OpenAI-compatible request timed out.") from exc
        except httpx.TransportError as exc:
            raise LLMRetryableError(f"OpenAI-compatible transport error: {exc}") from exc

        if response.status_code in {408, 409, 429} or response.status_code >= 500:
            raise LLMRetryableError(f"OpenAI-compatible endpoint returned retryable status {response.status_code}.")
        if response.status_code >= 400:
            raise LLMFatalError(f"OpenAI-compatible endpoint returned fatal status {response.status_code}.")

        try:
            data = response.json()
            content = str(data["choices"][0]["message"]["content"])
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise LLMFatalError("OpenAI-compatible response did not contain chat content.") from exc
        return LLMResponse(content=content, provider=self.name, model=self.model, raw=data)
