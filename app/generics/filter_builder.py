
from typing import Any, Dict, List, Optional, Set, Tuple, Type

from sqlalchemy import and_, or_
from sqlalchemy.orm import Query

from app.enums.filter_operation import FilterOperation
from app.generics.type_registry import (
    get_field_type,
    get_permitted_operations,
    validate_operation_for_type,
)
from app.schema.filter_node import FilterNode

_MAX_TREE_DEPTH = 20


class QueryFilterBuilder:
    FILTER_OPERATIONS = {
        FilterOperation.EQUALS: lambda col, val: col == val,
        FilterOperation.NOT_EQUALS: lambda col, val: col != val,
        FilterOperation.GREATER_THAN: lambda col, val: col > val,
        FilterOperation.GREATER_EQUAL: lambda col, val: col >= val,
        FilterOperation.LESS_THAN: lambda col, val: col < val,
        FilterOperation.LESS_EQUAL: lambda col, val: col <= val,
        FilterOperation.LIKE: lambda col, val: col.like(f"%{val}%"),
        FilterOperation.ILIKE: lambda col, val: col.ilike(f"%{val}%"),
        FilterOperation.IN: lambda col, val: col.in_(val),
        FilterOperation.NOT_IN: lambda col, val: ~col.in_(val),
        FilterOperation.IS_NULL: lambda col, val: col.is_(None),
        FilterOperation.IS_NOT_NULL: lambda col, val: col.isnot(None),
        FilterOperation.BETWEEN: lambda col, val: col.between(val[0], val[1]),
        FilterOperation.STARTS_WITH: lambda col, val: col.like(f"{val}%"),
        FilterOperation.ENDS_WITH: lambda col, val: col.like(f"%{val}"),
    }

    def __init__(self, query: Query, model: Type[Any]):
        self.query = query
        self.model = model
        self._joined: Set[Tuple[Type, str]] = set()


    def apply_tree(self, tree: FilterNode) -> "QueryFilterBuilder":
        clause = self._evaluate_node(tree, depth=0)
        if clause is not None:
            self.query = self.query.filter(clause)
        return self

    def apply_filter(
        self, field: str, operation: FilterOperation, value: Any
    ) -> "QueryFilterBuilder":
        if operation not in (FilterOperation.IS_NULL, FilterOperation.IS_NOT_NULL):
            if value is None or value == "" or value == []:
                return self

        column = self._resolve_field(field, operation=operation)
        self._validate_operation(column, operation)
        self._validate_operation_value(operation, value)
        filter_func = self.FILTER_OPERATIONS.get(operation)
        if filter_func is None:
            raise ValueError(f"Unsupported filter operation: {operation}")
        self.query = self.query.filter(filter_func(column, value))
        return self

    def apply_filters_from_list(
        self, filter_list: List[Dict[str, Any]]
    ) -> "QueryFilterBuilder":
        for f in filter_list:
            field = f.get("field")
            op_str = f.get("operation")
            value = f.get("value")
            if not field or not op_str:
                raise ValueError(f"Invalid filter dict: {f}. Must have 'field' and 'operation'.")
            self.apply_filter(field, FilterOperation(op_str), value)
        return self

    def get_query(self) -> Query:
        return self.query


    def _evaluate_node(self, node: FilterNode, depth: int = 0):
        if depth > _MAX_TREE_DEPTH:
            raise ValueError(
                f"Filter tree exceeds maximum depth of {_MAX_TREE_DEPTH}. "
                "Simplify the filter expression."
            )

        if node.node_type == "condition":
            return self._evaluate_condition(node)

        child_clauses = [
            self._evaluate_node(child, depth + 1) for child in node.children
        ]
        child_clauses = [c for c in child_clauses if c is not None]

        if not child_clauses:
            return None
        if len(child_clauses) == 1:
            return child_clauses[0]

        if node.operator == "AND":
            return and_(*child_clauses)
        elif node.operator == "OR":
            return or_(*child_clauses)
        else:
            raise ValueError(f"Unknown operator: {node.operator}")

    def _evaluate_condition(self, node: FilterNode):
        if node.operation not in (FilterOperation.IS_NULL, FilterOperation.IS_NOT_NULL):
            if node.value is None or node.value == "" or node.value == []:
                return None

        column = self._resolve_field(node.field, operation=node.operation)
        self._validate_operation(column, node.operation)
        self._validate_operation_value(node.operation, node.value)

        filter_func = self.FILTER_OPERATIONS.get(node.operation)
        if filter_func is None:
            raise ValueError(f"Unsupported filter operation: {node.operation}")

        return filter_func(column, node.value)


    def _resolve_field(
        self,
        field: str,
        operation: Optional[FilterOperation] = None,
    ):
        parts = field.split(".")
        current_model = self.model

        use_outer = operation in (
            FilterOperation.IS_NULL,
            FilterOperation.IS_NOT_NULL,
        ) if operation else False

        for part in parts[:-1]:
            if not hasattr(current_model, part):
                raise ValueError(
                    f"Model '{current_model.__name__}' has no relationship '{part}'."
                )
            rel_attr = getattr(current_model, part)
            if not hasattr(rel_attr, "property"):
                raise ValueError(
                    f"Attribute '{part}' on model '{current_model.__name__}' is not a relationship."
                )
            join_key = (current_model, part)
            if join_key not in self._joined:
                if use_outer:
                    self.query = self.query.outerjoin(rel_attr)
                else:
                    self.query = self.query.join(rel_attr)
                self._joined.add(join_key)
            current_model = rel_attr.property.mapper.class_

        col_name = parts[-1]
        if not hasattr(current_model, col_name):
            raise ValueError(
                f"Model '{current_model.__name__}' has no field '{col_name}'."
            )
        return getattr(current_model, col_name)


    def _validate_operation(self, column, operation: FilterOperation):
        try:
            col_type = column.property.columns[0].type
        except AttributeError:
            return
        field_type = get_field_type(col_type)
        if not validate_operation_for_type(field_type, operation):
            allowed = [op.value for op in get_permitted_operations(field_type)]
            raise ValueError(
                f"Operation '{operation.value}' is not permitted for field type "
                f"'{field_type}'. Allowed: {allowed}"
            )

    @staticmethod
    def _validate_operation_value(operation: FilterOperation, value: Any):
        if operation in (FilterOperation.IN, FilterOperation.NOT_IN):
            if not isinstance(value, list):
                raise ValueError(
                    f"Operation '{operation.value}' requires a list value."
                )
            if len(value) == 0:
                raise ValueError(
                    f"Operation '{operation.value}' requires at least one value."
                )
            return

        if operation == FilterOperation.BETWEEN:
            if not isinstance(value, list) or len(value) != 2:
                raise ValueError(
                    "Operation 'between' requires a list with exactly two values."
                )
