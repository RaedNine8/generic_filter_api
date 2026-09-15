from __future__ import annotations

import hashlib
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from filterx.agent.grounding.schema_repository import SchemaRepository
from filterx.agent.pipeline.copilot_graph import CopilotGraph
from filterx.agent.providers import CircuitBreaker, ResilientLLMClient, create_provider
from filterx.agent.providers.base import LLMProviderError
from filterx.agent.validation import FieldExistsValidator, OperationAllowedValidator, SchemaShapeValidator, ValidationPipeline, ValueTypeValidator


class CopilotQueryRequest(BaseModel):
    entity: str = Field(min_length=1, max_length=120)
    prompt: str = Field(min_length=1, max_length=4000)


class CopilotExecuteRequest(BaseModel):
    confirmation_token: str = Field(min_length=16, max_length=256)


@dataclass
class PendingFilter:
    entity: str
    filter_tree: dict[str, Any]
    explanation: str
    principal_key: str
    expires_at: float


def create_copilot_router(
    *,
    api_prefix: str = "/api",
    entities: Iterable[dict[str, Any]],
    scan_file: str | Path,
    agent_config: dict[str, Any],
    auth_dependency: Callable[..., Any] | None = None,
    permission_hook: Callable[..., Any] | None = None,
    field_visibility_hook: Callable[..., Any] | None = None,
) -> APIRouter:
    prefix = _normalize_prefix(api_prefix)
    router = APIRouter(prefix=f"{prefix}/filterx/copilot", tags=["filterx-copilot"])
    repository = SchemaRepository(Path(scan_file), entities=entities)
    pipeline = _build_pipeline(repository, agent_config)
    pending: dict[str, PendingFilter] = {}
    ttl_seconds = max(1, int(agent_config.get("safety", {}).get("confirmation_ttl_seconds", 600)))
    max_pending = max(1, int(agent_config.get("safety", {}).get("max_pending_confirmations", 1000)))
    get_principal = auth_dependency or _anonymous_principal
    router.state = {"pipeline": pipeline, "pending": pending}

    @router.post("/query")
    async def query_copilot(
        body: CopilotQueryRequest,
        request: Request,
        principal: Any = Depends(get_principal),
    ) -> dict[str, Any]:
        entity_name = body.entity.strip()
        prompt = body.prompt.strip()
        if not entity_name or not prompt:
            raise HTTPException(status_code=422, detail={"error": "copilot_request_empty", "detail": "Entity and prompt must not be blank."})
        _authorize(permission_hook, principal=principal, request=request, entity=repository.get_entity(entity_name), action="copilot.preview")
        request_repository = repository
        request_pipeline = router.state["pipeline"]
        if field_visibility_hook is not None:
            visible_entities = _visible_entities(repository.list_entities(), field_visibility_hook, principal, request)
            request_repository = SchemaRepository(Path(scan_file), entities=visible_entities)
            request_pipeline = _pipeline_with_repository(request_pipeline, request_repository)
        try:
            result = await request_pipeline.run(entity_name, prompt)
        except LLMProviderError as exc:
            raise HTTPException(
                status_code=503,
                detail={"error": "copilot_unavailable", "detail": "All configured LLM providers failed after retries."},
            ) from exc
        if not result.valid:
            raise HTTPException(
                status_code=422,
                detail={"error": "copilot_validation_failed", "issues": [error.__dict__ for error in result.validation_errors]},
            )
        _purge_expired(pending)
        while len(pending) >= max_pending:
            oldest_token = min(pending, key=lambda key: pending[key].expires_at)
            pending.pop(oldest_token, None)
        token = secrets.token_urlsafe(32)
        pending[token] = PendingFilter(
            result.entity,
            result.filter_tree,
            result.explanation,
            _principal_key(principal),
            time.time() + ttl_seconds,
        )
        return {"filter_tree": result.filter_tree, "explanation": result.explanation, "confirmation_token": token}

    @router.post("/execute")
    async def execute_copilot(
        body: CopilotExecuteRequest,
        request: Request,
        principal: Any = Depends(get_principal),
    ) -> dict[str, Any]:
        _purge_expired(pending)
        item = pending.get(body.confirmation_token)
        if item is None:
            raise HTTPException(status_code=404, detail={"error": "confirmation_token_not_found", "detail": "The confirmation token is missing or expired."})
        if not secrets.compare_digest(item.principal_key, _principal_key(principal)):
            raise HTTPException(status_code=403, detail={"error": "confirmation_token_owner_mismatch", "detail": "The confirmation token belongs to another principal."})
        entity = repository.get_entity(item.entity)
        _authorize(permission_hook, principal=principal, request=request, entity=entity, action="copilot.confirm")
        pending.pop(body.confirmation_token, None)
        if entity is None:
            raise HTTPException(status_code=404, detail=f"Unknown FilterX entity: {item.entity}")
        return {
            "entity": item.entity,
            "filter_tree": item.filter_tree,
            "summary": f"Confirmed filter for {item.entity}.",
            "explanation": item.explanation,
        }

    return router


def _build_pipeline(repository: SchemaRepository, agent_config: dict[str, Any]) -> CopilotGraph:
    providers_cfg = list(agent_config.get("providers") or [])
    compile_cfg = next((provider for provider in providers_cfg if "compile" in provider.get("roles", [])), None)
    if compile_cfg is None:
        raise RuntimeError("FilterX copilot requires at least one provider with the 'compile' role.")
    fallback_cfgs = [provider for provider in providers_cfg if "fallback" in provider.get("roles", [])]
    primary = create_provider(str(compile_cfg["name"]), **_provider_kwargs(compile_cfg))
    fallbacks = [create_provider(str(cfg["name"]), **_provider_kwargs(cfg)) for cfg in fallback_cfgs]
    safety = agent_config.get("safety", {})
    provider = ResilientLLMClient(
        primary,
        fallbacks=fallbacks,
        max_retries=int(safety.get("max_provider_retries", 3)),
        circuit_breaker=CircuitBreaker(
            failure_threshold=int(safety.get("circuit_breaker_failure_threshold", 5)),
            reset_seconds=int(safety.get("circuit_breaker_reset_seconds", 60)),
        ),
    )
    validation_pipeline = ValidationPipeline([
        SchemaShapeValidator(),
        FieldExistsValidator(repository),
        OperationAllowedValidator(repository),
        ValueTypeValidator(repository),
    ])
    return CopilotGraph(repository, provider, validation_pipeline, max_validation_retries=int(safety.get("max_validation_retries", 3)))


def _provider_kwargs(config: Mapping[str, Any]) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"model": str(config["model"])}
    for key in ("api_key_env", "base_url", "timeout_seconds"):
        if key in config and config[key] is not None:
            kwargs[key] = config[key]
    if str(config.get("name", "")).strip().lower() in {"openai", "openai-compatible"}:
        for key in ("require_api_key", "json_mode"):
            if key in config and config[key] is not None:
                kwargs[key] = config[key]
    return kwargs


def _pipeline_with_repository(pipeline: CopilotGraph, repository: SchemaRepository) -> CopilotGraph:
    validation_pipeline = ValidationPipeline([
        SchemaShapeValidator(),
        FieldExistsValidator(repository),
        OperationAllowedValidator(repository),
        ValueTypeValidator(repository),
    ])
    return CopilotGraph(
        repository,
        pipeline.provider,
        validation_pipeline,
        max_validation_retries=pipeline.max_validation_retries,
    )


def _normalize_prefix(api_prefix: str) -> str:
    prefix = api_prefix.strip() or "/api"
    if not prefix.startswith("/"):
        prefix = f"/{prefix}"
    return prefix.rstrip("/") if prefix != "/" else ""


def _purge_expired(pending: dict[str, PendingFilter]) -> None:
    now = time.time()
    for token, item in list(pending.items()):
        if item.expires_at <= now:
            pending.pop(token, None)


def _anonymous_principal() -> None:
    return None


def _principal_key(principal: Any) -> str:
    identity: str
    if principal is None:
        identity = "anonymous"
    elif isinstance(principal, Mapping):
        for field in ("sub", "id", "user_id", "username", "email"):
            if principal.get(field) is not None:
                identity = f"{field}:{principal[field]}"
                break
        else:
            identity = f"mapping:{sorted((str(key), str(value)) for key, value in principal.items())}"
    else:
        identity = ""
        for field in ("sub", "id", "user_id", "username", "email"):
            value = getattr(principal, field, None)
            if value is not None:
                identity = f"{field}:{value}"
                break
        if not identity:
            identity = f"{type(principal).__module__}.{type(principal).__qualname__}:{principal}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _authorize(
    permission_hook: Callable[..., Any] | None,
    *,
    principal: Any,
    request: Request,
    entity: dict[str, Any] | None,
    action: str,
) -> None:
    if permission_hook is None:
        return
    allowed = permission_hook(principal=principal, request=request, entity=entity, action=action)
    if allowed is False:
        raise HTTPException(status_code=403, detail="FilterX copilot action is not permitted.")


def _visible_entities(
    entities: Iterable[dict[str, Any]],
    hook: Callable[..., Any],
    principal: Any,
    request: Request,
) -> list[dict[str, Any]]:
    visible_entities: list[dict[str, Any]] = []
    for entity in entities:
        visible = dict(entity)
        visible["fields"] = [
            field
            for field in entity.get("fields", [])
            if hook(
                principal=principal,
                request=request,
                entity=entity,
                field=str(field.get("name", "")),
                action="copilot.preview",
            )
        ]
        relationships: list[dict[str, Any]] = []
        for relationship in entity.get("relationships", []):
            relation = dict(relationship)
            relation_name = str(relation.get("name", ""))
            relation["related_fields"] = [
                field
                for field in relation.get("related_fields", [])
                if hook(
                    principal=principal,
                    request=request,
                    entity=entity,
                    field=f"{relation_name}.{field.get('name', '')}",
                    action="copilot.preview",
                )
            ]
            relationships.append(relation)
        visible["relationships"] = relationships
        visible_entities.append(visible)
    return visible_entities
