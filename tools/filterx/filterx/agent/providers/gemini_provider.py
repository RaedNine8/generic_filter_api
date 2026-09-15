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

        system_text = "\n\n".join(
            str(message.get("content", ""))
            for message in request.messages
            if message.get("role") == "system"
        )
        contents = [
            {
                "role": "model" if message.get("role") == "assistant" else "user",
                "parts": [{"text": str(message.get("content", ""))}],
            }
            for message in request.messages
            if message.get("role") != "system"
        ]
        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {"temperature": request.temperature},
        }
        if system_text:
            payload["systemInstruction"] = {"parts": [{"text": system_text}]}
        if request.response_format == "json":
            payload["generationConfig"]["responseMimeType"] = "application/json"

        url = f"{self.base_url}/models/{self.model}:generateContent"
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, headers={"x-goog-api-key": api_key}, json=payload)
        except httpx.TimeoutException as exc:
            raise LLMRetryableError("Gemini request timed out.") from exc
        except httpx.TransportError as exc:
            raise LLMRetryableError(f"Gemini transport error: {exc}") from exc

        if response.status_code in {408, 409, 429} or response.status_code >= 500:
            raise LLMRetryableError(f"Gemini returned retryable status {response.status_code}.")
        if response.status_code >= 400:
            raise LLMFatalError(f"Gemini returned fatal status {response.status_code}.")

        try:
            data = response.json()
            parts = data["candidates"][0]["content"]["parts"]
            content = "".join(str(part.get("text", "")) for part in parts)
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise LLMFatalError("Gemini response did not contain generated content.") from exc
        return LLMResponse(content=content, provider=self.name, model=self.model, raw=data)
