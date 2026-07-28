from __future__ import annotations

from filterx.agent.providers.base import LLMRequest, LLMResponse


def test_copilot_preview_and_execute_flow(client, monkeypatch):
    from app.filterx_generated import copilot_router

    async def fake_complete(request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            content='{"filter_tree":{"node_type":"condition","field":"rating","operation":"gt","value":4.0},"explanation":"Books with rating greater than 4."}',
            provider="fake",
            model="fake-model",
        )

    monkeypatch.setattr(copilot_router.router.state["pipeline"].provider, "complete", fake_complete)

    preview_response = client.post("/api/filterx/copilot/query", json={"entity": "Book", "prompt": "books rated above four"})
    assert preview_response.status_code == 200
    preview = preview_response.json()
    assert preview["filter_tree"]["field"] == "rating"
    assert preview["confirmation_token"]

    execute_response = client.post("/api/filterx/copilot/execute", json={"confirmation_token": preview["confirmation_token"]})
    assert execute_response.status_code == 200
    payload = execute_response.json()
    assert payload["meta"]["total_items"] == 2
    assert {row["title"] for row in payload["data"]} == {"Alpha Filtering", "Gamma Search"}
    assert "Returned 2 of 2" in payload["summary"]
