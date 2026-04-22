
from typing import Dict, List, Type

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.types import TypeEngine

from app.enums.filter_operation import FilterOperation

FIELD_TYPE_STRING = "string"
FIELD_TYPE_INTEGER = "integer"
FIELD_TYPE_FLOAT = "float"
FIELD_TYPE_BOOLEAN = "boolean"
FIELD_TYPE_DATE = "date"
FIELD_TYPE_DATETIME = "datetime"
FIELD_TYPE_ENUM = "enum"

PERMITTED_OPS: Dict[str, List[FilterOperation]] = {
    FIELD_TYPE_STRING: [
        FilterOperation.EQUALS,
        FilterOperation.NOT_EQUALS,
        FilterOperation.LIKE,
        FilterOperation.ILIKE,
        FilterOperation.STARTS_WITH,
        FilterOperation.ENDS_WITH,
        FilterOperation.IN,
        FilterOperation.NOT_IN,
        FilterOperation.IS_NULL,
        FilterOperation.IS_NOT_NULL,
    ],
    FIELD_TYPE_INTEGER: [
        FilterOperation.EQUALS,
        FilterOperation.NOT_EQUALS,
        FilterOperation.GREATER_THAN,
        FilterOperation.GREATER_EQUAL,
        FilterOperation.LESS_THAN,
        FilterOperation.LESS_EQUAL,
        FilterOperation.IN,
        FilterOperation.NOT_IN,
        FilterOperation.BETWEEN,
        FilterOperation.IS_NULL,
        FilterOperation.IS_NOT_NULL,
    ],
    FIELD_TYPE_FLOAT: [
        FilterOperation.EQUALS,
        FilterOperation.NOT_EQUALS,
        FilterOperation.GREATER_THAN,
        FilterOperation.GREATER_EQUAL,
        FilterOperation.LESS_THAN,
        FilterOperation.LESS_EQUAL,
        FilterOperation.IN,
        FilterOperation.NOT_IN,
        FilterOperation.BETWEEN,
        FilterOperation.IS_NULL,
        FilterOperation.IS_NOT_NULL,
    ],
    FIELD_TYPE_BOOLEAN: [
        FilterOperation.EQUALS,
        FilterOperation.NOT_EQUALS,
        FilterOperation.IS_NULL,
        FilterOperation.IS_NOT_NULL,
    ],
    FIELD_TYPE_DATE: [
        FilterOperation.EQUALS,
        FilterOperation.NOT_EQUALS,
        FilterOperation.GREATER_THAN,
        FilterOperation.GREATER_EQUAL,
        FilterOperation.LESS_THAN,
        FilterOperation.LESS_EQUAL,
        FilterOperation.BETWEEN,
        FilterOperation.IS_NULL,
        FilterOperation.IS_NOT_NULL,
    ],
    FIELD_TYPE_DATETIME: [
        FilterOperation.EQUALS,
        FilterOperation.NOT_EQUALS,
        FilterOperation.GREATER_THAN,
        FilterOperation.GREATER_EQUAL,
        FilterOperation.LESS_THAN,
        FilterOperation.LESS_EQUAL,
        FilterOperation.BETWEEN,
        FilterOperation.IS_NULL,
        FilterOperation.IS_NOT_NULL,
    ],
    FIELD_TYPE_ENUM: [
        FilterOperation.EQUALS,
        FilterOperation.NOT_EQUALS,
        FilterOperation.IN,
        FilterOperation.NOT_IN,
        FilterOperation.IS_NULL,
        FilterOperation.IS_NOT_NULL,
    ],
}

_SA_TYPE_MAP: List[tuple[Type[TypeEngine], str]] = [
    (Boolean, FIELD_TYPE_BOOLEAN),
    (DateTime, FIELD_TYPE_DATETIME),
    (Date, FIELD_TYPE_DATE),
    (Enum, FIELD_TYPE_ENUM),
    (Float, FIELD_TYPE_FLOAT),
    (Numeric, FIELD_TYPE_FLOAT),
    (Integer, FIELD_TYPE_INTEGER),
    (Text, FIELD_TYPE_STRING),
    (String, FIELD_TYPE_STRING),
]


def get_field_type(sa_type: TypeEngine) -> str:
    for sa_cls, field_type in _SA_TYPE_MAP:
        if isinstance(sa_type, sa_cls):
            return field_type
    return FIELD_TYPE_STRING


def get_permitted_operations(field_type: str) -> List[FilterOperation]:
    return PERMITTED_OPS.get(field_type, list(FilterOperation))


def validate_operation_for_type(field_type: str, operation: FilterOperation) -> bool:
    return operation in get_permitted_operations(field_type)
