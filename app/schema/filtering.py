from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.enums.filter_operation import FilterOperation


class FilterParam(BaseModel):
    """Single filter rule — used internally and for URL grammar parsing."""

    field: str = Field(..., description="Field name to filter")
    operation: FilterOperation = Field(
        default=FilterOperation.EQUALS, description="Filter operation"
    )
    value: Any = Field(default=None, description="Filter value")

    @model_validator(mode="after")
    def validate_value(self) -> "FilterParam":
        op = self.operation
        v = self.value

        if op in (FilterOperation.IN, FilterOperation.NOT_IN):
            if not isinstance(v, list):
                raise ValueError(f"Value must be a list for {op} operation.")
            if len(v) == 0:
                raise ValueError(f"Value list cannot be empty for {op} operation.")

        if op == FilterOperation.BETWEEN:
            if not isinstance(v, (list, tuple)):
                raise ValueError("Value must be a list or tuple for BETWEEN operation.")
            if len(v) != 2:
                raise ValueError("Value must contain exactly 2 elements for BETWEEN.")

        if op in (FilterOperation.IS_NULL, FilterOperation.IS_NOT_NULL):
            if v not in (True, False, None):
                raise ValueError(f"Value must be boolean for {op} operation.")

        return self
