from __future__ import annotations

from filterx.core.entity_scope import resolve_entity_scope, select_entity_metadata


def test_resolve_entity_scope_is_deterministic() -> None:
    scope = resolve_entity_scope(
        ["SavedFilter", "Book", "Author", "Book"],
        ["Book", "Author"],
        ["Author"],
    )

    assert scope.available == ("Author", "Book", "SavedFilter")
    assert scope.selected == ("Book",)
    assert scope.requested_and_excluded == ("Author",)


def test_resolve_entity_scope_reports_unknown_names() -> None:
    scope = resolve_entity_scope(
        ["Book", "Author"],
        ["Book", "Missing"],
        ["Ghost"],
    )

    assert scope.has_errors is True
    assert scope.unknown_requested == ("Missing",)
    assert scope.unknown_excluded == ("Ghost",)


def test_select_entity_metadata_preserves_scan_order() -> None:
    entities = [
        {"model": "Book"},
        {"model": "Author"},
        {"model": "SavedFilter"},
    ]

    selected, scope = select_entity_metadata(
        entities,
        requested_names=["SavedFilter", "Book"],
    )

    assert [entity["model"] for entity in selected] == ["Book", "SavedFilter"]
    assert scope.selected == ("Book", "SavedFilter")