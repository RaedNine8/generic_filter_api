from __future__ import annotations

import os
from typing import Any

from .base import LLMFatalError, LLMProvider, LLMRequest, LLMResponse, LLMRetryableError
from .registry import register_provider


@register_provider("groq")
class GroqProvider(LLMProvider):
    def __init__(self, api_key_env: str, model: str, timeout_seconds: float = 30.0, base_url: str = "https://api.groq.com/openai/v1/chat/completions") -> None:
        self.name = "groq"
        self.model = model
        self.api_key_env = api_key_env
        self.timeout_seconds = timeout_seconds
        self.base_url = base_url

    async def complete(self, request: LLMRequest) -> LLMResponse:
        api_key = os.getenv(self.api_key_env)
        if not api_key:
            raise LLMFatalError(f"Missing API key environment variable: {self.api_key_env}")

        try:
            import httpx
        except ImportError as exc:  # pragma: no cover
            raise LLMFatalError("The 'httpx' package is required for GroqProvider.") from exc

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": list(request.messages),
            "temperature": request.temperature,
        }
        if request.response_format == "json":
            payload["response_format"] = {"type": "json_object"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    self.base_url,
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json=payload,
                )
        except httpx.TimeoutException as exc:
            raise LLMRetryableError("Groq request timed out.") from exc
        except httpx.TransportError as exc:
            raise LLMRetryableError(f"Groq transport error: {exc}") from exc

        if response.status_code in {408, 409, 429} or response.status_code >= 500:
            raise LLMRetryableError(f"Groq returned retryable status {response.status_code}.")
        if response.status_code >= 400:
            raise LLMFatalError(f"Groq returned fatal status {response.status_code}: {response.text}")

        data = response.json()
        try:
            content = str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMFatalError("Groq response did not contain chat content.") from exc
        return LLMResponse(content=content, provider=self.name, model=self.model, raw=data)
