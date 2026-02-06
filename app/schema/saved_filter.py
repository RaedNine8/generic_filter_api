from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field


class FilterRule(BaseModel):
    field: str
    operation: str
    value: Any


class SavedFilterCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    model_name: str = Field(..., max_length=100)
    filters: List[FilterRule] = []
    sort_by: Optional[str] = None
    sort_order: str = "desc"
    page_size: int = 10
    search_query: Optional[str] = None


class SavedFilterUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    filters: Optional[List[FilterRule]] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = None
    page_size: Optional[int] = None
    search_query: Optional[str] = None


class SavedFilterResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    model_name: str
    filters: List[dict] = []
    sort_by: Optional[str] = None
    sort_order: str = "desc"
    page_size: int = 10
    search_query: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
