from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

from filterx.agent.grounding.schema_repository import SchemaRepository

from .base import FilterValidationError, Validator


NULLARY_OPS = {"is_null", "is_not_null"}
LIST_OPS = {"in", "not_in"}


class SchemaShapeValidator(Validator):
    def validate(self, entity_name: str, filter_tree: dict[str, Any]) -> list[FilterValidationError]:
        return list(_validate_node_shape(filter_tree, "$"))


class FieldExistsValidator(Validator):
    def __init__(self, repository: SchemaRepository) -> None:
        self.repository = repository

    def validate(self, entity_name: str, filter_tree: dict[str, Any]) -> list[FilterValidationError]:
        errors: list[FilterValidationError] = []
        if self.repository.get_entity(entity_name) is None:
            return [FilterValidationError("UNKNOWN_ENTITY", f"Unknown entity '{entity_name}'.")]
        for path, node in _condition_nodes(filter_tree):
            field = str(node.get("field") or "")
            if self.repository.get_field(entity_name, field) is None:
                errors.append(FilterValidationError("UNKNOWN_FIELD", f"Unknown field '{field}' for entity '{entity_name}'.", path, {"field": field}))
        return errors


class OperationAllowedValidator(Validator):
    def __init__(self, repository: SchemaRepository) -> None:
        self.repository = repository

    def validate(self, entity_name: str, filter_tree: dict[str, Any]) -> list[FilterValidationError]:
        errors: list[FilterValidationError] = []
        for path, node in _condition_nodes(filter_tree):
            field = str(node.get("field") or "")
            operation = str(node.get("operation") or "")
            allowed_ops = self.repository.allowed_ops(entity_name, field)
            if allowed_ops and operation not in allowed_ops:
                errors.append(
                    FilterValidationError(
                        "OPERATION_NOT_ALLOWED",
                        f"Operation '{operation}' is not allowed for field '{field}'.",
                        path,
                        {"field": field, "operation": operation, "allowed_ops": allowed_ops},
                    )
                )
        return errors


class ValueTypeValidator(Validator):
    def __init__(self, repository: SchemaRepository) -> None:
        self.repository = repository

    def validate(self, entity_name: str, filter_tree: dict[str, Any]) -> list[FilterValidationError]:
        errors: list[FilterValidationError] = []
        for path, node in _condition_nodes(filter_tree):
            field_name = str(node.get("field") or "")
            operation = str(node.get("operation") or "")
            field = self.repository.get_field(entity_name, field_name)
            if field is None:
                continue
            value = node.get("value")
            if operation in NULLARY_OPS:
                continue
            if value in (None, ""):
                errors.append(FilterValidationError("MISSING_VALUE", f"Operation '{operation}' requires a value for field '{field_name}'.", path))
                continue
            field_type = str(field.get("type") or "string")
            if operation == "between":
                if not isinstance(value, list) or len(value) != 2:
                    errors.append(FilterValidationError("INVALID_VALUE_TYPE", f"Operation 'between' requires exactly two values for field '{field_name}'.", path))
                    continue
                values = value
            elif operation in LIST_OPS:
                if not isinstance(value, list) or not value:
                    errors.append(FilterValidationError("INVALID_VALUE_TYPE", f"Operation '{operation}' requires a non-empty list for field '{field_name}'.", path))
                    continue
                values = value
            else:
                values = [value]
            for item in values:
                if not _matches_field_type(field_type, item):
                    errors.append(
                        FilterValidationError(
                            "INVALID_VALUE_TYPE",
                            f"Value for field '{field_name}' must match type '{field_type}'.",
                            path,
                            {"field": field_name, "field_type": field_type, "value": item},
                        )
                    )
        return errors


def _validate_node_shape(node: Any, path: str) -> Iterable[FilterValidationError]:
    if not isinstance(node, dict):
        yield FilterValidationError("INVALID_SCHEMA_SHAPE", "Filter tree node must be an object.", path)
        return
    node_type = node.get("node_type")
    if node_type == "condition":
        if not isinstance(node.get("field"), str) or not node.get("field"):
            yield FilterValidationError("INVALID_SCHEMA_SHAPE", "Condition node requires a non-empty string field.", path)
        if not isinstance(node.get("operation"), str) or not node.get("operation"):
            yield FilterValidationError("INVALID_SCHEMA_SHAPE", "Condition node requires a non-empty string operation.", path)
        return
    if node_type == "operator":
        if node.get("operator") not in {"AND", "OR"}:
            yield FilterValidationError("INVALID_SCHEMA_SHAPE", "Operator node requires operator AND or OR.", path)
        children = node.get("children")
        if not isinstance(children, list) or not children:
            yield FilterValidationError("INVALID_SCHEMA_SHAPE", "Operator node requires at least one child.", path)
            return
        for index, child in enumerate(children):
            yield from _validate_node_shape(child, f"{path}.children[{index}]")
        return
    yield FilterValidationError("INVALID_SCHEMA_SHAPE", "Node type must be 'operator' or 'condition'.", path)


def _condition_nodes(node: dict[str, Any], path: str = "$") -> Iterable[tuple[str, dict[str, Any]]]:
    if node.get("node_type") == "condition":
        yield path, node
        return
    for index, child in enumerate(node.get("children") or []):
        if isinstance(child, dict):
            yield from _condition_nodes(child, f"{path}.children[{index}]")


def _matches_field_type(field_type: str, value: Any) -> bool:
    if field_type in {"integer"}:
        return isinstance(value, int) and not isinstance(value, bool)
    if field_type in {"float", "decimal", "numeric"}:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if field_type == "boolean":
        return isinstance(value, bool)
    if field_type in {"date", "datetime"}:
        if not isinstance(value, str):
            return False
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            return True
        except ValueError:
            return False
    if field_type in {"string", "text", "enum"}:
        return isinstance(value, str)
    return True
