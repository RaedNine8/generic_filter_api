from tests.helpers.request_builders import and_tree, condition_node


def test_health_endpoint_is_healthy(client):
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"


def test_books_list_returns_paginated_shape(client):
    response = client.get("/api/books", params={"page": 1, "size": 2, "sort_by": "id", "order": "asc"})
    assert response.status_code == 200

    payload = response.json()
    assert "data" in payload
    assert "meta" in payload
    assert payload["meta"]["page"] == 1
    assert payload["meta"]["size"] == 2
    assert payload["meta"]["total_items"] == 3
    assert len(payload["data"]) == 2


def test_url_grammar_relationship_filter_returns_expected_rows(client):
    response = client.get("/api/books", params={"author.country_eq": "USA", "sort_by": "id", "order": "asc"})
    assert response.status_code == 200

    payload = response.json()
    assert payload["meta"]["total_items"] == 2
    assert all(row["author"]["country"] == "USA" for row in payload["data"])


def test_filter_tree_endpoint_supports_and_conditions(client):
    tree = and_tree(
        condition_node("price", "gte", 20),
        condition_node("is_available", "eq", True),
    )

    response = client.post("/api/books/filter", json=tree, params={"sort_by": "id", "order": "asc"})
    assert response.status_code == 200

    payload = response.json()
    assert payload["meta"]["total_items"] == 1
    assert payload["data"][0]["title"] == "Gamma Search"


def test_books_sort_by_genre_is_supported(client):
    response = client.get(
        "/api/books",
        params={"page": 1, "size": 20, "sort_by": "genre", "order": "asc"},
    )
    assert response.status_code == 200

    payload = response.json()
    genres = [row["genre"] for row in payload["data"]]
    assert genres == sorted(genres)


def test_books_sort_by_available_is_supported(client):
    response = client.get(
        "/api/books",
        params={"page": 1, "size": 20, "sort_by": "is_available", "order": "asc"},
    )
    assert response.status_code == 200

    payload = response.json()
    flags = [row["is_available"] for row in payload["data"]]
    assert flags == sorted(flags)


def test_books_invalid_sort_returns_400_with_detail(client):
    response = client.get(
        "/api/books",
        params={"page": 1, "size": 20, "sort_by": "not_a_field", "order": "asc"},
    )
    assert response.status_code == 400
    assert "Invalid sort field" in response.json()["detail"]


def test_books_sort_by_relationship_field_is_supported(client):
    response = client.get(
        "/api/books",
        params={"page": 1, "size": 20, "sort_by": "author.name", "order": "asc"},
    )
    assert response.status_code == 200

    payload = response.json()
    names = [row["author"]["name"] for row in payload["data"]]
    assert names == sorted(names)


def test_group_by_endpoint_supports_url_filters(client):
    response = client.get(
        "/api/books/group-by/genre",
        params={"author.country_eq": "USA", "search": "a"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert all("key" in row and "count" in row for row in payload)


def test_group_by_endpoint_supports_filter_tree(client):
    tree = and_tree(condition_node("author.country", "eq", "USA"))
    response = client.post(
        "/api/books/group-by/genre/filter",
        json=tree,
        params={"search": "a"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert all("key" in row and "count" in row for row in payload)
