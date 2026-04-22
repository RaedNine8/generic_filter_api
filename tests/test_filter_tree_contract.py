import pytest

from app.enums.filter_operation import FilterOperation
from app.generics.filter_builder import QueryFilterBuilder
from app.models.author import Author
from app.models.book import Book
from app.schema.filter_node import FilterNode


def _condition(field: str, operation: FilterOperation, value):
    return FilterNode(
        node_type="condition",
        field=field,
        operation=operation,
        value=value,
    )


def _operator(operator: str, *children: FilterNode):
    return FilterNode(
        node_type="operator",
        operator=operator,
        children=list(children),
    )


def test_tree_nested_and_or_with_relationship_conditions(db_session):
    tree = _operator(
        "OR",
        _operator(
            "AND",
            _condition("price", FilterOperation.GREATER_THAN, 30),
            _condition("author.country", FilterOperation.EQUALS, "USA"),
        ),
        _operator(
            "AND",
            _condition("is_available", FilterOperation.EQUALS, False),
            _condition("author.country", FilterOperation.EQUALS, "France"),
        ),
    )

    rows = (
        QueryFilterBuilder(db_session.query(Book), Book)
        .apply_tree(tree)
        .get_query()
        .order_by(Book.id.asc())
        .all()
    )

    assert [row.title for row in rows] == ["Beta Pagination", "Gamma Search"]


def test_tree_ignores_empty_condition_and_preserves_valid_sibling(db_session):
    tree = _operator(
        "OR",
        _condition("title", FilterOperation.ILIKE, ""),
        _condition("genre", FilterOperation.EQUALS, "Mystery"),
    )

    rows = (
        QueryFilterBuilder(db_session.query(Book), Book)
        .apply_tree(tree)
        .get_query()
        .all()
    )

    assert [row.title for row in rows] == ["Gamma Search"]


def test_tree_with_only_empty_conditions_is_a_noop(db_session):
    tree = _operator(
        "AND",
        _condition("title", FilterOperation.ILIKE, ""),
        _condition("price", FilterOperation.EQUALS, None),
    )

    rows = (
        QueryFilterBuilder(db_session.query(Book), Book)
        .apply_tree(tree)
        .get_query()
        .order_by(Book.id.asc())
        .all()
    )

    assert len(rows) == 3


def test_tree_relationship_is_null_uses_outer_join_semantics(db_session):
    orphan = Author(
        name="No Books",
        email="nobooks@example.com",
        country="Morocco",
        is_active=True,
        birth_year=1990,
    )
    db_session.add(orphan)
    db_session.commit()

    tree = _condition("books.id", FilterOperation.IS_NULL, True)

    rows = (
        QueryFilterBuilder(db_session.query(Author), Author)
        .apply_tree(tree)
        .get_query()
        .order_by(Author.id.asc())
        .all()
    )

    assert [row.email for row in rows] == ["nobooks@example.com"]


def test_tree_or_combines_is_null_relationship_and_regular_condition(db_session):
    orphan = Author(
        name="No Books",
        email="nobooks2@example.com",
        country="Morocco",
        is_active=True,
        birth_year=1991,
    )
    db_session.add(orphan)
    db_session.commit()

    tree = _operator(
        "OR",
        _condition("books.id", FilterOperation.IS_NULL, True),
        _condition("country", FilterOperation.EQUALS, "France"),
    )

    rows = (
        QueryFilterBuilder(db_session.query(Author), Author)
        .apply_tree(tree)
        .get_query()
        .order_by(Author.email.asc())
        .all()
    )

    assert [row.email for row in rows] == ["bruno.martin@example.com", "nobooks2@example.com"]


def test_tree_between_and_in_operations_work_together(db_session):
    tree = _operator(
        "AND",
        _condition("price", FilterOperation.BETWEEN, [12.5, 26.0]),
        _condition("genre", FilterOperation.IN, ["Fiction", "Non-Fiction"]),
    )

    rows = (
        QueryFilterBuilder(db_session.query(Book), Book)
        .apply_tree(tree)
        .get_query()
        .order_by(Book.id.asc())
        .all()
    )

    assert [row.title for row in rows] == ["Alpha Filtering", "Beta Pagination"]


def test_tree_depth_guard_rejects_overly_deep_trees(db_session):
    node = _condition("title", FilterOperation.ILIKE, "Alpha")

    for _ in range(21):
        node = _operator("AND", node)

    builder = QueryFilterBuilder(db_session.query(Book), Book)
    with pytest.raises(ValueError, match="maximum depth"):
        builder.apply_tree(node)