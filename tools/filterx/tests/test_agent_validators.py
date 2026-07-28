from __future__ import annotations

from pathlib import Path

from app.filterx_generated.entities import ENTITIES
from filterx.agent.grounding.schema_repository import SchemaRepository
from filterx.agent.validation import FieldExistsValidator, OperationAllowedValidator, SchemaShapeValidator, ValidationPipeline, ValueTypeValidator


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
