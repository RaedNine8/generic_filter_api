from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from filterx.agent.api import create_copilot_router
from filterx.agent.providers.base import LLMRequest, LLMResponse


ENTITIES = [
    {
        "model": "Book",
        "table": "books",
        "fields": [
            {"name": "rating", "type": "float", "ops": ["eq", "gt", "gte", "lt", "lte"]},
            {"name": "secret_note", "type": "string", "ops": ["eq", "ilike"]},
        ],
        "relationships": [],
    }
]


def _agent_config() -> dict[str, object]:
    return {
        "providers": [
            {
                "name": "openai-compatible",
                "model": "local-test",
                "roles": ["compile"],
                "base_url": "http://localhost:11434/v1",
            }
        ],
        "safety": {
            "max_validation_retries": 0,
            "max_provider_retries": 1,
            "confirmation_ttl_seconds": 60,
            "max_pending_confirmations": 10,
        },
    }


def _principal(request: Request) -> dict[str, str]:
    return {"sub": request.headers.get("x-user", "anonymous")}


def _make_client(*, field_visibility_hook=None) -> tuple[TestClient, object]:
    router = create_copilot_router(
        entities=ENTITIES,
        scan_file=Path("missing-scan.json"),
        agent_config=_agent_config(),
        auth_dependency=_principal,
        field_visibility_hook=field_visibility_hook,
    )
    app = FastAPI()
    app.include_router(router)
    return TestClient(app), router


def test_confirmation_token_is_bound_to_principal_and_single_use() -> None:
    client, router = _make_client()

    async def fake_complete(request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            content='{"filter_tree":{"node_type":"condition","field":"rating","operation":"gt","value":4.0},"explanation":"High-rated books."}',
            provider="fake",
            model="fake",
        )

    router.state["pipeline"].provider.complete = fake_complete
    preview = client.post(
        "/api/filterx/copilot/query",
        headers={"x-user": "alice"},
        json={"entity": "Book", "prompt": "books rated above four"},
    )
    assert preview.status_code == 200
    token = preview.json()["confirmation_token"]

    wrong_user = client.post(
        "/api/filterx/copilot/execute",
        headers={"x-user": "bob"},
        json={"confirmation_token": token},
    )
    assert wrong_user.status_code == 403

    confirmed = client.post(
        "/api/filterx/copilot/execute",
        headers={"x-user": "alice"},
        json={"confirmation_token": token},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["filter_tree"]["field"] == "rating"

    replay = client.post(
        "/api/filterx/copilot/execute",
        headers={"x-user": "alice"},
        json={"confirmation_token": token},
    )
    assert replay.status_code == 404


def test_hidden_fields_are_not_available_to_copilot_validation() -> None:
    def visibility_hook(**kwargs: object) -> bool:
        return kwargs["field"] != "secret_note"

    client, router = _make_client(field_visibility_hook=visibility_hook)

    async def fake_complete(request: LLMRequest) -> LLMResponse:
        grounded_request = json.loads(request.messages[1]["content"])
        assert {field["name"] for field in grounded_request["entity"]["fields"]} == {"rating"}
        return LLMResponse(
            content='{"filter_tree":{"node_type":"condition","field":"secret_note","operation":"eq","value":"x"}}',
            provider="fake",
            model="fake",
        )

    router.state["pipeline"].provider.complete = fake_complete
    response = client.post(
        "/api/filterx/copilot/query",
        headers={"x-user": "alice"},
        json={"entity": "Book", "prompt": "filter by secret note"},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["issues"][0]["code"] == "UNKNOWN_FIELD"
