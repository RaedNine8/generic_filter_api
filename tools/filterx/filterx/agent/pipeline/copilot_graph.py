from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, TypedDict

from filterx.agent.grounding.schema_repository import SchemaRepository
from filterx.agent.providers.base import LLMProvider, LLMRequest
from filterx.agent.validation.base import FilterValidationError, ValidationPipeline


class CopilotState(TypedDict, total=False):
    entity: str
    prompt: str
    canonical_entity: str
    filter_tree: dict[str, Any]
    explanation: str
    validation_errors: list[FilterValidationError]
    attempts: int


@dataclass
class CopilotResult:
    entity: str
    filter_tree: dict[str, Any]
    explanation: str
    valid: bool
    validation_errors: list[FilterValidationError] = field(default_factory=list)


class CopilotGraph:
    def __init__(
        self,
        repository: SchemaRepository,
        provider: LLMProvider,
        validation_pipeline: ValidationPipeline,
        *,
        max_validation_retries: int = 3,
    ) -> None:
        self.repository = repository
        self.provider = provider
        self.validation_pipeline = validation_pipeline
        self.max_validation_retries = max(0, max_validation_retries)
        self._compiled_graph = self._build_graph()

    async def run(self, entity: str, prompt: str) -> CopilotResult:
        initial: CopilotState = {"entity": entity, "prompt": prompt, "attempts": 0, "validation_errors": []}
        final_state = await self._compiled_graph.ainvoke(initial)
        return CopilotResult(
            entity=str(final_state.get("canonical_entity") or entity),
            filter_tree=dict(final_state.get("filter_tree") or {}),
            explanation=str(final_state.get("explanation") or ""),
            valid=not bool(final_state.get("validation_errors")),
            validation_errors=list(final_state.get("validation_errors") or []),
        )

    def _build_graph(self) -> Any:
        try:
            from langgraph.graph import END, StateGraph
        except ImportError:
            return _FallbackGraph(self)

        graph = StateGraph(CopilotState)
        graph.add_node("resolve_entity", self._resolve_entity)
        graph.add_node("compile_filter", self._compile_filter)
        graph.add_node("validate_filter", self._validate_filter)
        graph.add_node("preview", self._preview)
        graph.set_entry_point("resolve_entity")
        graph.add_edge("resolve_entity", "compile_filter")
        graph.add_edge("compile_filter", "validate_filter")
        graph.add_conditional_edges("validate_filter", self._route_after_validation, {"retry": "compile_filter", "preview": "preview"})
        graph.add_edge("preview", END)
        return graph.compile()

    def _resolve_entity(self, state: CopilotState) -> CopilotState:
        requested = state["entity"]
        entity = self.repository.get_entity(requested)
        if entity is None:
            state["canonical_entity"] = requested
            state["validation_errors"] = [FilterValidationError("UNKNOWN_ENTITY", f"Unknown entity '{requested}'.")]
            return state
        state["canonical_entity"] = str(entity.get("model") or requested)
        return state

    async def _compile_filter(self, state: CopilotState) -> CopilotState:
        if state.get("validation_errors") and state.get("canonical_entity") == state.get("entity") and not self.repository.get_entity(state["entity"]):
            state["attempts"] = self.max_validation_retries + 1
            return state
        state["attempts"] = int(state.get("attempts") or 0) + 1
        request = LLMRequest(messages=self._messages_for_state(state), role="compile", response_format="json")
        response = await self.provider.complete(request)
        payload = _parse_json_response(response.content)
        state["filter_tree"] = dict(payload.get("filter_tree") or {})
        state["explanation"] = str(payload.get("explanation") or _default_explanation(state))
        return state

    def _validate_filter(self, state: CopilotState) -> CopilotState:
        if state.get("validation_errors") and not state.get("filter_tree"):
            return state
        state["validation_errors"] = self.validation_pipeline.validate(str(state.get("canonical_entity") or state["entity"]), dict(state.get("filter_tree") or {}))
        return state

    def _route_after_validation(self, state: CopilotState) -> str:
        if state.get("validation_errors") and int(state.get("attempts") or 0) <= self.max_validation_retries:
            return "retry"
        return "preview"

    def _preview(self, state: CopilotState) -> CopilotState:
        if not state.get("explanation"):
            state["explanation"] = _default_explanation(state)
        return state

    def _messages_for_state(self, state: CopilotState) -> list[dict[str, str]]:
        entity_name = str(state.get("canonical_entity") or state["entity"])
        entity = self.repository.get_entity(entity_name) or {}
        feedback = ""
        if state.get("validation_errors"):
            feedback = "\nFix these validation errors: " + json.dumps([error.__dict__ for error in state["validation_errors"]], default=str)
        return [
            {
                "role": "system",
                "content": (
                    "You convert a user's plain English request into FilterX FilterTreeNode JSON. "
                    "Return only JSON with keys filter_tree and explanation. Use only fields and operations from the entity metadata."
                ),
            },
            {
                "role": "user",
                "content": json.dumps({"entity": entity, "prompt": state["prompt"], "feedback": feedback}, default=str),
            },
        ]


class _FallbackGraph:
    def __init__(self, owner: CopilotGraph) -> None:
        self.owner = owner

    async def ainvoke(self, state: CopilotState) -> CopilotState:
        state = self.owner._resolve_entity(state)
        while True:
            state = await self.owner._compile_filter(state)
            state = self.owner._validate_filter(state)
            if self.owner._route_after_validation(state) != "retry":
                break
        return self.owner._preview(state)


def _parse_json_response(content: str) -> dict[str, Any]:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
    data = json.loads(cleaned)
    if not isinstance(data, dict):
        raise ValueError("LLM response must be a JSON object.")
    return data


def _default_explanation(state: CopilotState) -> str:
    return f"Filtering {state.get('canonical_entity') or state.get('entity')} results for: {state.get('prompt')}"
