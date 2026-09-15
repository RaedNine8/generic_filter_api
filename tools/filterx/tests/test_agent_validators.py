from __future__ import annotations

from pathlib import Path

from filterx.agent.grounding.schema_repository import SchemaRepository
from filterx.agent.validation import FieldExistsValidator, OperationAllowedValidator, SchemaShapeValidator, ValidationPipeline, ValueTypeValidator


ENTITIES = [
    {
        "model": "Book",
        "table": "books",
        "fields": [
            {"name": "published_year", "type": "integer", "ops": ["eq", "gte", "lte"]},
            {"name": "rating", "type": "float", "ops": ["eq", "gt", "gte", "lt", "lte"]},
            {"name": "is_available", "type": "boolean", "ops": ["eq"]},
            {"name": "created_at", "type": "datetime", "ops": ["eq", "gte", "lte"]},
            {"name": "status", "type": "enum", "ops": ["eq", "in"], "enum_values": ["draft", "published"]},
        ],
        "relationships": [],
    }
]


def _repository() -> SchemaRepository:
    return SchemaRepository(Path(".filterx/scan.json"), entities=ENTITIES)


def test_validation_pipeline_accepts_valid_book_filter() -> None:
    repository = _repository()
    pipeline = ValidationPipeline([
        SchemaShapeValidator(),
        FieldExistsValidator(repository),
        OperationAllowedValidator(repository),
        ValueTypeValidator(repository),
    ])
    tree = {
        "node_type": "operator",
        "operator": "AND",
        "children": [
            {"node_type": "condition", "field": "published_year", "operation": "gte", "value": 2015},
            {"node_type": "condition", "field": "rating", "operation": "gt", "value": 4.0},
            {"node_type": "condition", "field": "is_available", "operation": "eq", "value": True},
            {"node_type": "condition", "field": "created_at", "operation": "gte", "value": "2024-01-01T00:00:00"},
        ],
    }
    assert pipeline.validate("Book", tree) == []


def test_validators_collect_unknown_field_bad_operation_and_bad_type() -> None:
    repository = _repository()
    pipeline = ValidationPipeline([
        SchemaShapeValidator(),
        FieldExistsValidator(repository),
        OperationAllowedValidator(repository),
        ValueTypeValidator(repository),
    ])
    tree = {
        "node_type": "operator",
        "operator": "AND",
        "children": [
            {"node_type": "condition", "field": "missing", "operation": "eq", "value": "x"},
            {"node_type": "condition", "field": "is_available", "operation": "ilike", "value": "yes"},
            {"node_type": "condition", "field": "published_year", "operation": "gte", "value": "2015"},
            {"node_type": "condition", "field": "created_at", "operation": "gte", "value": "not-a-date"},
        ],
    }
    codes = [error.code for error in pipeline.validate("Book", tree)]
    assert "UNKNOWN_FIELD" in codes
    assert "OPERATION_NOT_ALLOWED" in codes
    assert codes.count("INVALID_VALUE_TYPE") == 3


def test_schema_shape_validator_stops_pipeline_on_garbage_shape() -> None:
    repository = _repository()
    pipeline = ValidationPipeline([SchemaShapeValidator(), FieldExistsValidator(repository)])
    errors = pipeline.validate("Book", {"node_type": "condition", "operation": "eq"})
    assert [error.code for error in errors] == ["INVALID_SCHEMA_SHAPE"]


def test_validator_rejects_unknown_operation_and_enum_value() -> None:
    repository = _repository()
    pipeline = ValidationPipeline([
        SchemaShapeValidator(),
        FieldExistsValidator(repository),
        OperationAllowedValidator(repository),
        ValueTypeValidator(repository),
    ])
    tree = {
        "node_type": "operator",
        "operator": "AND",
        "children": [
            {"node_type": "condition", "field": "rating", "operation": "delete", "value": 4.0},
            {"node_type": "condition", "field": "status", "operation": "eq", "value": "private"},
        ],
    }
    codes = [error.code for error in pipeline.validate("Book", tree)]
    assert "OPERATION_NOT_ALLOWED" in codes
    assert "INVALID_ENUM_VALUE" in codes


def test_schema_shape_validator_limits_tree_depth() -> None:
    tree: dict[str, object] = {"node_type": "condition", "field": "rating", "operation": "eq", "value": 4.0}
    for _ in range(22):
        tree = {"node_type": "operator", "operator": "AND", "children": [tree]}
    errors = SchemaShapeValidator().validate("Book", tree)
    assert any(error.code == "FILTER_TREE_TOO_DEEP" for error in errors)

    repository = _repository()
    pipeline = ValidationPipeline([SchemaShapeValidator(), FieldExistsValidator(repository)])
    pipeline_errors = pipeline.validate("Book", tree)
    assert [error.code for error in pipeline_errors] == ["FILTER_TREE_TOO_DEEP"]
