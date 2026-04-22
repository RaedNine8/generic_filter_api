from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.generics.dependencies import create_url_grammar_filter_dependency


def _make_test_app(max_filters: int) -> FastAPI:
    app = FastAPI()

    @app.get("/filters")
    def read_filters(filters=Depends(create_url_grammar_filter_dependency(max_filters=max_filters))):
        return filters

    return app


def test_reserved_query_keys_are_not_treated_as_filters():
    app = _make_test_app(max_filters=10)
    with TestClient(app) as client:
        response = client.get(
            "/filters",
            params={
                "page": 1,
                "size": 20,
                "sort_by": "id",
                "order": "asc",
                "title_ilike": "alpha",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload == [{"field": "title", "operation": "ilike", "value": "alpha"}]


def test_max_filters_guard_rejects_oversized_query():
    app = _make_test_app(max_filters=1)
    with TestClient(app) as client:
        response = client.get(
            "/filters",
            params={"title_ilike": "a", "genre_eq": "Fiction"},
        )

    assert response.status_code == 400
    assert "Too many filter parameters" in response.json()["detail"]
