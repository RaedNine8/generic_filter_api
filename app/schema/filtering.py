from typing import Any
from pydantic import BaseModel, Field, validator
from app.enums.filter_operation import FilterOperation


class FilterParam(BaseModel):
    field: str = Field(..., description="Field name to filter")
    operation: FilterOperation = Field(
        default=FilterOperation.EQUALS,
        description="Filter operation"
    )
    value: Any = Field(..., description="Filter value")
    
    @validator('value')
    def validate_value(cls, v, values):
        operation = values.get('operation')
        
        if operation in [FilterOperation.IN, FilterOperation.NOT_IN]:
            if not isinstance(v, list):
                raise ValueError(
                    f"Value must be a list for {operation} operation."
                )
            if len(v) == 0:
                raise ValueError(
                    f"Value list cannot be empty for {operation} operation."
                )
        
        if operation == FilterOperation.BETWEEN:
            if not isinstance(v, (list, tuple)):
                raise ValueError(
                    "Value must be a list or tuple for BETWEEN operation."
                )
            if len(v) != 2:
                raise ValueError(
                    f"Value must contain exactly 2 elements for BETWEEN operation."
                )
        
        if operation in [FilterOperation.IS_NULL, FilterOperation.IS_NOT_NULL]:
            if v not in [True, False, None]:
                raise ValueError(
                    f"Value must be boolean for {operation} operation."
                )
        
        return v
    
    class Config:
        from_attributes = True
