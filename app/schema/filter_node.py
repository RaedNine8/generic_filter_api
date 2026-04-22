from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from app.enums.filter_operation import FilterOperation


class FilterNode(BaseModel):

    node_type: Literal["operator", "condition"] = Field(
        ..., description="Node kind: 'operator' for AND/OR groups, 'condition' for filter leaves"
    )

    operator: Optional[Literal["AND", "OR"]] = Field(
        default=None, description="Logical operator (only for operator nodes)"
    )
    children: Optional[List["FilterNode"]] = Field(
        default=None, description="Child nodes (only for operator nodes)"
    )

    field: Optional[str] = Field(
        default=None, description="Field path, supports dot notation for relationships (e.g. 'author.country')"
    )
    operation: Optional[FilterOperation] = Field(
        default=None, description="Filter operation to apply"
    )
    value: Optional[Any] = Field(
        default=None, description="Filter value"
    )

    @model_validator(mode="after")
    def validate_node(self) -> "FilterNode":
        if self.node_type == "operator":
            if self.operator is None:
                raise ValueError("Operator nodes must specify 'operator' (AND or OR).")
            if not self.children or len(self.children) < 1:
                raise ValueError("Operator nodes must have at least 1 child.")
        elif self.node_type == "condition":
            if self.field is None:
                raise ValueError("Condition nodes must specify 'field'.")
            if self.operation is None:
                raise ValueError("Condition nodes must specify 'operation'.")
        return self

    model_config = {"from_attributes": True}
