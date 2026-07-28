from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Sequence

from .base import LLMFatalError, LLMProvider, LLMProviderError, LLMRequest, LLMResponse, LLMRetryableError

logger = logging.getLogger(__name__)


@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    reset_seconds: int = 60

    def __post_init__(self) -> None:
        self._failures: dict[str, int] = {}
        self._opened_at: dict[str, float] = {}

    def is_open(self, provider_name: str) -> bool:
        opened_at = self._opened_at.get(provider_name)
        if opened_at is None:
            return False
        if time.monotonic() - opened_at >= self.reset_seconds:
            logger.info("Circuit breaker reset for provider %s.", provider_name)
            self._opened_at.pop(provider_name, None)
            self._failures[provider_name] = 0
            return False
        return True

    def record_success(self, provider_name: str) -> None:
        self._failures[provider_name] = 0
        if provider_name in self._opened_at:
            logger.info("Circuit breaker closed for provider %s after successful request.", provider_name)
        self._opened_at.pop(provider_name, None)

    def record_failure(self, provider_name: str) -> None:
        failures = self._failures.get(provider_name, 0) + 1
        self._failures[provider_name] = failures
        if failures >= self.failure_threshold and provider_name not in self._opened_at:
            logger.info("Circuit breaker opened for provider %s after %s failures.", provider_name, failures)
            self._opened_at[provider_name] = time.monotonic()


class ResilientLLMClient(LLMProvider):
    def __init__(
        self,
        provider: LLMProvider,
        *,
        fallbacks: Sequence[LLMProvider] | None = None,
        max_retries: int = 3,
        circuit_breaker: CircuitBreaker | None = None,
    ) -> None:
        self.provider = provider
        self.fallbacks = list(fallbacks or [])
        self.max_retries = max(1, max_retries)
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.name = provider.name
        self.model = provider.model

    async def complete(self, request: LLMRequest) -> LLMResponse:
        errors: list[str] = []
        for provider in [self.provider, *self.fallbacks]:
            if self.circuit_breaker.is_open(provider.name):
                logger.info("Skipping provider %s because circuit is open.", provider.name)
                errors.append(f"{provider.name}: circuit open")
                continue
            try:
                return await self._complete_with_retries(provider, request)
            except LLMFatalError as exc:
                errors.append(f"{provider.name}: {exc}")
                self.circuit_breaker.record_failure(provider.name)
                logger.info("Provider %s failed fatally: %s", provider.name, exc)
            except LLMRetryableError as exc:
                errors.append(f"{provider.name}: {exc}")
                self.circuit_breaker.record_failure(provider.name)
                logger.info("Provider %s exhausted retryable attempts: %s", provider.name, exc)
        detail = "; ".join(errors) if errors else "no providers configured"
        raise LLMRetryableError(f"All configured LLM providers failed after retries ({detail}).")

    async def _complete_with_retries(self, provider: LLMProvider, request: LLMRequest) -> LLMResponse:
        try:
            from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter
        except ImportError as exc:  # pragma: no cover
            raise LLMFatalError("The 'tenacity' package is required for resilient LLM calls.") from exc

        last_error: LLMRetryableError | None = None
        async for attempt in AsyncRetrying(
            retry=retry_if_exception_type(LLMRetryableError),
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential_jitter(initial=0.25, max=2.0),
            reraise=True,
        ):
            with attempt:
                logger.info("Calling provider %s attempt %s.", provider.name, attempt.retry_state.attempt_number)
                try:
                    response = await provider.complete(request)
                except LLMRetryableError as exc:
                    last_error = exc
                    logger.info("Retryable provider failure from %s: %s", provider.name, exc)
                    raise
                except LLMProviderError:
                    raise
                self.circuit_breaker.record_success(provider.name)
                return response
        if last_error is not None:
            raise last_error
        raise LLMRetryableError(f"Provider {provider.name} did not return a response.")
