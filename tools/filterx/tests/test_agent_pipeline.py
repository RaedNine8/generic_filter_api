from __future__ import annotations

from pathlib import Path

import pytest

from app.filterx_generated.entities import ENTITIES
from filterx.agent.grounding.schema_repository import SchemaRepository
from filterx.agent.pipeline import CopilotGraph
from filterx.agent.providers.base import LLMProvider, LLMRequest, LLMResponse
from filterx.agent.validation import FieldExistsValidator, OperationAllowedValidator, SchemaShapeValidator, ValidationPipeline, ValueTypeValidator


class ScriptedProvider(LLMProvider):
    def __init__(self, responses: list[str]) -> None:
        self.name = "scripted"
        self.model = "scripted-model"
        self.responses = responses
        self.requests: list[LLMRequest] = []

    async def complete(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        return LLMResponse(content=self.responses.pop(0), provider=self.name, model=self.model)


@pytest.mark.asyncio
async def test_copilot_graph_retries_after_validation_error() -> None:
    repository = SchemaRepository(Path(".filterx/scan.json"), entities=ENTITIES)
    pipeline = ValidationPipeline([
        SchemaShapeValidator(),
        FieldExistsValidator(repository),
        OperationAllowedValidator(repository),
        ValueTypeValidator(repository),
    ])
    provider = ScriptedProvider([
        '{"filter_tree":{"node_type":"condition","field":"unknown","operation":"eq","value":"x"},"explanation":"bad"}',
        '{"filter_tree":{"node_type":"condition","field":"rating","operation":"gt","value":4.0},"explanation":"Books rated above 4."}',
    ])
    graph = CopilotGraph(repository, provider, pipeline, max_validation_retries=3)

    result = await graph.run("Book", "books rated above four")

    assert result.valid is True
    assert result.filter_tree["field"] == "rating"
    assert len(provider.requests) == 2
