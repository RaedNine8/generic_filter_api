import pytest

from app.enums.filter_operation import FilterOperation
from app.generics.filter_builder import QueryFilterBuilder
from app.models.book import Book


def test_filter_builder_rejects_non_list_for_in_operation(db_session):
    builder = QueryFilterBuilder(db_session.query(Book), Book)

    with pytest.raises(ValueError, match="requires a list value"):
        builder.apply_filter("title", FilterOperation.IN, "Alpha")


def test_filter_builder_rejects_invalid_between_payload(db_session):
    builder = QueryFilterBuilder(db_session.query(Book), Book)

    with pytest.raises(ValueError, match="exactly two values"):
        builder.apply_filter("price", FilterOperation.BETWEEN, [10])


def test_filter_builder_rejects_disallowed_operation_for_field_type(db_session):
    builder = QueryFilterBuilder(db_session.query(Book), Book)

    with pytest.raises(ValueError, match="not permitted"):
        builder.apply_filter("title", FilterOperation.GREATER_THAN, "M")


def test_filter_builder_supports_dot_notation_relationship_fields(db_session):
    builder = QueryFilterBuilder(db_session.query(Book), Book)
    query = (
        builder
        .apply_filter("author.country", FilterOperation.EQUALS, "USA")
        .get_query()
    )

    rows = query.all()
    assert len(rows) == 2
    assert all(row.author.country == "USA" for row in rows)
