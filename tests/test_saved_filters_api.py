def test_saved_filter_crud_and_apply_flow(client):
    create_payload = {
        "name": "USA Books",
        "description": "Books by USA authors",
        "model_name": "Book",
        "filters": [
            {"field": "author.country", "operation": "eq", "value": "USA"}
        ],
        "sort_by": "id",
        "sort_order": "asc",
        "page_size": 20,
    }

    create_response = client.post("/api/saved-filters", json=create_payload)
    assert create_response.status_code == 201
    created = create_response.json()
    filter_id = created["id"]

    update_payload = {
        "name": "USA Books Updated",
        "search_query": "Alpha",
    }
    update_response = client.put(f"/api/saved-filters/{filter_id}", json=update_payload)
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["name"] == "USA Books Updated"
    assert updated["search_query"] == "Alpha"

    apply_response = client.get(f"/api/saved-filters/{filter_id}/apply", params={"page": 1})
    assert apply_response.status_code == 200
    applied = apply_response.json()
    assert applied["meta"]["total_items"] == 1
    assert applied["data"][0]["title"] == "Alpha Filtering"

    delete_response = client.delete(f"/api/saved-filters/{filter_id}")
    assert delete_response.status_code == 204


def test_saved_filter_rejects_unknown_model_name(client):
    payload = {
        "name": "Invalid Model",
        "model_name": "NotRegisteredModel",
        "filters": [{"field": "title", "operation": "eq", "value": "Alpha"}],
    }

    response = client.post("/api/saved-filters", json=payload)
    assert response.status_code == 400
    assert "Unknown model" in response.json()["detail"]


def test_saved_filter_rejects_invalid_sort_order(client):
    payload = {
        "name": "Invalid Sort",
        "model_name": "Book",
        "filters": [{"field": "title", "operation": "eq", "value": "Alpha"}],
        "sort_order": "INVALID",
    }

    response = client.post("/api/saved-filters", json=payload)
    assert response.status_code == 422


def test_saved_filter_update_rejects_invalid_sort_field(client):
    create_payload = {
        "name": "Sortable",
        "model_name": "Book",
        "filters": [{"field": "title", "operation": "eq", "value": "Alpha"}],
        "sort_by": "id",
        "sort_order": "asc",
    }
    create_response = client.post("/api/saved-filters", json=create_payload)
    assert create_response.status_code == 201

    filter_id = create_response.json()["id"]
    response = client.put(
        f"/api/saved-filters/{filter_id}",
        json={"sort_by": "not_a_column"},
    )
    assert response.status_code == 400
    assert "Invalid sort field" in response.json()["detail"]
