from __future__ import annotations

import asyncio
import importlib
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from filterx.agent.grounding.schema_repository import SchemaRepository
from filterx.agent.pipeline.copilot_graph import CopilotGraph
from filterx.agent.providers import CircuitBreaker, ResilientLLMClient, create_provider
from filterx.agent.providers.base import LLMProviderError
from filterx.agent.validation import FieldExistsValidator, OperationAllowedValidator, SchemaShapeValidator, ValidationPipeline, ValueTypeValidator


class CopilotQueryRequest(BaseModel):
    entity: str
    prompt: str


class CopilotExecuteRequest(BaseModel):
    confirmation_token: str


@dataclass
class PendingFilter:
    entity: str
    filter_tree: dict[str, Any]
    explanation: str
    expires_at: float


def create_copilot_router(
    *,
    api_prefix: str = "/api",
    entities: Iterable[dict[str, Any]],
    scan_file: str | Path,
    agent_config: dict[str, Any],
    session_dependency: Callable[..., Any],
    query_executor_cls: type[Any],
    pagination_cls: type[Any],
    filter_node_cls: type[Any] | None = None,
    model_registry: dict[str, type[Any]] | None = None,
    response_model_registry: dict[str, type[Any]] | None = None,
) -> APIRouter:
    prefix = _normalize_prefix(api_prefix)
    router = APIRouter(prefix=f"{prefix}/filterx/copilot", tags=["filterx-copilot"])
    repository = SchemaRepository(Path(scan_file), entities=entities)
    pipeline = _build_pipeline(repository, agent_config)
    pending: dict[str, PendingFilter] = {}
    ttl_seconds = int(agent_config.get("safety", {}).get("confirmation_ttl_seconds", 600))
    models = model_registry or {}
    response_registry = response_model_registry or {}
    router.state = {"pipeline": pipeline, "pending": pending}

    @router.post("/query")
    async def query_copilot(request: CopilotQueryRequest) -> dict[str, Any]:
        try:
            result = await router.state["pipeline"].run(request.entity, request.prompt)
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
        token = secrets.token_urlsafe(24)
        pending[token] = PendingFilter(result.entity, result.filter_tree, result.explanation, time.time() + ttl_seconds)
        _purge_expired(pending)
        return {"filter_tree": result.filter_tree, "explanation": result.explanation, "confirmation_token": token}

    @router.post("/execute")
    async def execute_copilot(request: CopilotExecuteRequest, db: Any = Depends(session_dependency)) -> dict[str, Any]:
        _purge_expired(pending)
        item = pending.pop(request.confirmation_token, None)
        if item is None:
            raise HTTPException(status_code=404, detail={"error": "confirmation_token_not_found", "detail": "The confirmation token is missing or expired."})
        entity = repository.get_entity(item.entity)
        if entity is None:
            raise HTTPException(status_code=404, detail=f"Unknown FilterX entity: {item.entity}")
        model = models.get(str(entity.get("model"))) or _model_for_entity(entity)
        executor = query_executor_cls(model=model, db=db, searchable_fields=_searchable_fields(entity), sortable_fields=None, default_sort_field=_default_sort_field(entity))
        filter_node = _build_filter_node(item.filter_tree, filter_node_cls)
        pagination = pagination_cls(page=1, size=20)
        rows, total = await asyncio.to_thread(executor.execute, pagination=pagination, filter_tree=filter_node)
        response_model = response_registry.get(str(entity.get("model")))
        data = _serialize_rows(rows, response_model)
        return {"data": data, "meta": {"page": 1, "size": 20, "total_items": total}, "summary": f"Returned {len(data)} of {total} results for {item.entity}.", "explanation": item.explanation}

    return router


def _build_pipeline(repository: SchemaRepository, agent_config: dict[str, Any]) -> CopilotGraph:
    providers_cfg = list(agent_config.get("providers") or [])
    compile_cfg = next((provider for provider in providers_cfg if "compile" in provider.get("roles", [])), None)
    if compile_cfg is None:
        raise RuntimeError("FilterX copilot requires at least one provider with the 'compile' role.")
    fallback_cfgs = [provider for provider in providers_cfg if "fallback" in provider.get("roles", [])]
    primary = create_provider(str(compile_cfg["name"]), api_key_env=str(compile_cfg["api_key_env"]), model=str(compile_cfg["model"]))
    fallbacks = [create_provider(str(cfg["name"]), api_key_env=str(cfg["api_key_env"]), model=str(cfg["model"])) for cfg in fallback_cfgs]
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


def _model_for_entity(entity: dict[str, Any]) -> type[Any]:
    module = importlib.import_module(str(entity["module"]))
    return getattr(module, str(entity["model"]))


def _searchable_fields(entity: dict[str, Any]) -> list[str]:
    return [str(field.get("name")) for field in entity.get("fields", []) if str(field.get("type")) in {"string", "text", "enum"}]


def _default_sort_field(entity: dict[str, Any]) -> str:
    primary_keys = entity.get("primary_keys") or []
    return str(primary_keys[0]) if primary_keys else "id"


def _build_filter_node(filter_tree: dict[str, Any], filter_node_cls: type[Any] | None) -> Any:
    if filter_node_cls is None:
        try:
            from app.schema.filter_node import FilterNode
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("The host app must expose app.schema.filter_node.FilterNode.") from exc
        filter_node_cls = FilterNode
    return filter_node_cls.model_validate(filter_tree)


def _serialize_rows(rows: list[Any], response_model: type[Any] | None) -> list[dict[str, Any]]:
    if response_model is not None:
        return [response_model.model_validate(row).model_dump(mode="json") for row in rows]
    output: list[dict[str, Any]] = []
    for row in rows:
        values = {key: value for key, value in vars(row).items() if not key.startswith("_")}
        output.append(values)
    return output
