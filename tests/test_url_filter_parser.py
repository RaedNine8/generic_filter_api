import pytest

from app.generics.dependencies import parse_url_filter_param


def test_parse_defaults_to_eq_when_no_suffix_is_used():
    parsed = parse_url_filter_param("title", "alpha")
    assert parsed == {"field": "title", "operation": "eq", "value": "alpha"}


def test_parse_in_operation_as_list_and_scalar_coercion():
    parsed = parse_url_filter_param("pages_in", "100,200,300")
    assert parsed == {
        "field": "pages",
        "operation": "in",
        "value": [100, 200, 300],
    }


def test_parse_between_operation_with_numeric_values():
    parsed = parse_url_filter_param("price_between", "10.5,42")
    assert parsed == {
        "field": "price",
        "operation": "between",
        "value": [10.5, 42],
    }


def test_parse_bool_and_null_values():
    assert parse_url_filter_param("is_available_eq", "true")["value"] is True
    assert parse_url_filter_param("is_available_eq", "false")["value"] is False
    assert parse_url_filter_param("description_eq", "null")["value"] is None


@pytest.mark.parametrize(
    ("key", "value", "expected_operation", "expected_value"),
    [
        ("title_eq", "Alpha", "eq", "Alpha"),
        ("title_ne", "Alpha", "ne", "Alpha"),
        ("price_gt", "10", "gt", 10),
        ("price_gte", "10", "gte", 10),
        ("price_lt", "99", "lt", 99),
        ("price_lte", "99", "lte", 99),
        ("title_like", "al", "like", "al"),
        ("title_ilike", "al", "ilike", "al"),
        ("genre_in", "Fiction,Mystery", "in", ["Fiction", "Mystery"]),
        ("genre_not_in", "Fiction,Mystery", "not_in", ["Fiction", "Mystery"]),
        ("price_between", "1,9", "between", [1, 9]),
        ("description_is_null", "true", "is_null", True),
        ("description_is_not_null", "true", "is_not_null", True),
        ("title_starts_with", "Al", "starts_with", "Al"),
        ("title_ends_with", "ha", "ends_with", "ha"),
    ],
)
def test_parse_all_supported_operation_suffixes(
    key: str,
    value,
    expected_operation: str,
    expected_value,
):
    parsed = parse_url_filter_param(key, value)
    assert parsed["operation"] == expected_operation
    assert parsed["value"] == expected_value
