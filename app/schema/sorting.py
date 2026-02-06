from typing import Optional
from pydantic import BaseModel, Field
from app.enums.sort_order import SortOrder


class GenericSortParams(BaseModel):
    sort_by: Optional[str] = Field(default=None, description="Field to sort by")
    order: SortOrder = Field(default=SortOrder.ASC, description="Sort order (asc/desc)")
    
    class Config:
        from_attributes = True
