def test_books_metadata_endpoint_returns_schema(client):
    response = client.get("/api/books/metadata")
    assert response.status_code == 200

    payload = response.json()
    assert payload["model"] == "Book"
    assert "fields" in payload
    assert "relationships" in payload
    assert any(field["name"] == "title" for field in payload["fields"])


def test_authors_metadata_endpoint_returns_schema(client):
    response = client.get("/api/authors/metadata")
    assert response.status_code == 200

    payload = response.json()
    assert payload["model"] == "Author"
    assert "fields" in payload
    assert "relationships" in payload
    assert any(field["name"] == "name" for field in payload["fields"])


def test_saved_filter_missing_resource_returns_404(client):
    get_response = client.get("/api/saved-filters/9999")
    assert get_response.status_code == 404

    delete_response = client.delete("/api/saved-filters/9999")
    assert delete_response.status_code == 404
