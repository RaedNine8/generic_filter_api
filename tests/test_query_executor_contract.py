import pytest

from app.enums.sort_order import SortOrder
from app.generics.query_executor import GenericQueryExecutor
from app.models.author import Author
from app.models.book import Book
from app.schema.pagination import GenericPaginationParams
from app.schema.sorting import GenericSortParams


def test_query_executor_rejects_invalid_sort_field(db_session):
    executor = GenericQueryExecutor(
        model=Book,
        db=db_session,
        sortable_fields=["id", "title", "price"],
        searchable_fields=["title"],
    )

    with pytest.raises(ValueError, match="Invalid sort field"):
        executor.execute(
            pagination=GenericPaginationParams(page=1, size=10),
            sort=GenericSortParams(sort_by="non_existing_field", order=SortOrder.ASC),
        )


def test_query_executor_applies_search_and_pagination(db_session):
    executor = GenericQueryExecutor(
        model=Book,
        db=db_session,
        sortable_fields=["id", "title", "price"],
        searchable_fields=["title"],
    )

    items, total = executor.execute(
        pagination=GenericPaginationParams(page=1, size=1),
        sort=GenericSortParams(sort_by="id", order=SortOrder.ASC),
        search="Gamma",
    )

    assert total == 1
    assert len(items) == 1
    assert items[0].title == "Gamma Search"


def test_query_executor_boolean_search_matches_only_boolean_fields(db_session):
    executor = GenericQueryExecutor(
        model=Book,
        db=db_session,
        sortable_fields=["id", "title", "price"],
        searchable_fields=["is_available"],
    )

    items, total = executor.execute(
        pagination=GenericPaginationParams(page=1, size=10),
        sort=GenericSortParams(sort_by="id", order=SortOrder.ASC),
        search="true",
    )

    assert total == 2
    assert len(items) == 2
    assert all(item.is_available for item in items)


def test_query_executor_sorts_by_any_model_column_without_explicit_list(db_session):
    """When no sortable_fields is passed, all model columns are sortable."""
    executor = GenericQueryExecutor(
        model=Book,
        db=db_session,
        sortable_fields=None,
        searchable_fields=["title"],
    )

    items, total = executor.execute(
        pagination=GenericPaginationParams(page=1, size=10),
        sort=GenericSortParams(sort_by="is_available", order=SortOrder.ASC),
    )

    assert total == 3
    flags = [item.is_available for item in items]
    assert flags == sorted(flags)


def test_query_executor_sorts_genre_via_db_order_by(db_session):
    """genre is a string column; must sort via DB ORDER BY, not Python."""
    executor = GenericQueryExecutor(
        model=Book,
        db=db_session,
        sortable_fields=["id", "title", "genre"],
        searchable_fields=["title"],
    )

    items, total = executor.execute(
        pagination=GenericPaginationParams(page=1, size=10),
        sort=GenericSortParams(sort_by="genre", order=SortOrder.ASC),
    )

    assert total == 3
    genres = [item.genre for item in items]
    assert genres == sorted(genres)


def test_query_executor_explicit_list_restricts_sorting(db_session):
    """When sortable_fields is provided, only those fields are allowed."""
    executor = GenericQueryExecutor(
        model=Book,
        db=db_session,
        sortable_fields=["id", "title"],
        searchable_fields=["title"],
    )

    with pytest.raises(ValueError, match="Sorting by 'genre' is not allowed"):
        executor.execute(
            pagination=GenericPaginationParams(page=1, size=10),
            sort=GenericSortParams(sort_by="genre", order=SortOrder.ASC),
        )


def test_query_executor_rejects_nonexistent_column(db_session):
    """A field that doesn't exist on the model is rejected with a clear message."""
    executor = GenericQueryExecutor(
        model=Book,
        db=db_session,
        sortable_fields=None,
        searchable_fields=["title"],
    )

    with pytest.raises(ValueError, match="not a column on model"):
        executor.execute(
            pagination=GenericPaginationParams(page=1, size=10),
            sort=GenericSortParams(sort_by="nonexistent_field", order=SortOrder.ASC),
        )


def test_query_executor_supports_relationship_sorting(db_session):
    executor = GenericQueryExecutor(
        model=Book,
        db=db_session,
        sortable_fields=None,
        searchable_fields=["title", "author.name"],
    )

    items, total = executor.execute(
        pagination=GenericPaginationParams(page=1, size=10),
        sort=GenericSortParams(sort_by="author.name", order=SortOrder.ASC),
    )

    assert total == 3
    author_names = [item.author.name for item in items]
    assert author_names == sorted(author_names)


def test_query_executor_counts_distinct_root_entities_for_joined_search(db_session):
    executor = GenericQueryExecutor(
        model=Author,
        db=db_session,
        sortable_fields=None,
        searchable_fields=["books.title"],
    )

    _, total = executor.execute(
        pagination=GenericPaginationParams(page=1, size=10),
        sort=GenericSortParams(sort_by="id", order=SortOrder.ASC),
        search="a",
    )

    assert total == 2
