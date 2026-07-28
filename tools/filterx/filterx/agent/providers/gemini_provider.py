from __future__ import annotations

import os
from typing import Any

from .base import LLMFatalError, LLMProvider, LLMRequest, LLMResponse, LLMRetryableError
from .registry import register_provider


@register_provider("gemini")
class GeminiProvider(LLMProvider):
    def __init__(self, api_key_env: str, model: str, timeout_seconds: float = 30.0, base_url: str = "https://generativelanguage.googleapis.com/v1beta") -> None:
        self.name = "gemini"
        self.model = model
        self.api_key_env = api_key_env
        self.timeout_seconds = timeout_seconds
        self.base_url = base_url.rstrip("/")

    async def complete(self, request: LLMRequest) -> LLMResponse:
        api_key = os.getenv(self.api_key_env)
        if not api_key:
            raise LLMFatalError(f"Missing API key environment variable: {self.api_key_env}")

        try:
            import httpx
        except ImportError as exc:  # pragma: no cover
            raise LLMFatalError("The 'httpx' package is required for GeminiProvider.") from exc

        prompt = "\n\n".join(f"{message.get('role', 'user')}: {message.get('content', '')}" for message in request.messages)
        payload: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": request.temperature},
        }
        if request.response_format == "json":
            payload["generationConfig"]["responseMimeType"] = "application/json"

        url = f"{self.base_url}/models/{self.model}:generateContent?key={api_key}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, json=payload)
        except httpx.TimeoutException as exc:
            raise LLMRetryableError("Gemini request timed out.") from exc
        except httpx.TransportError as exc:
            raise LLMRetryableError(f"Gemini transport error: {exc}") from exc

        if response.status_code in {408, 409, 429} or response.status_code >= 500:
            raise LLMRetryableError(f"Gemini returned retryable status {response.status_code}.")
        if response.status_code >= 400:
            raise LLMFatalError(f"Gemini returned fatal status {response.status_code}: {response.text}")

        data = response.json()
        try:
            parts = data["candidates"][0]["content"]["parts"]
            content = "".join(str(part.get("text", "")) for part in parts)
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMFatalError("Gemini response did not contain generated content.") from exc
        return LLMResponse(content=content, provider=self.name, model=self.model, raw=data)
