from typing import Any, Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field

from app.schema.filter_node import FilterNode


class SavedFilterCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    model_name: str = Field(..., max_length=100)
    filters: Optional[List[Dict[str, Any]]] = None
    filter_tree: Optional[FilterNode] = None
    sort_by: Optional[str] = None
    sort_order: str = "asc"
    page_size: int = 20
    search_query: Optional[str] = None


class SavedFilterUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    filters: Optional[List[Dict[str, Any]]] = None
    filter_tree: Optional[FilterNode] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = None
    page_size: Optional[int] = None
    search_query: Optional[str] = None


class SavedFilterResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    model_name: str
    filters: Optional[List[Dict[str, Any]]] = None
    filter_tree: Optional[FilterNode] = None
    sort_by: Optional[str] = None
    sort_order: str = "asc"
    page_size: int = 20
    search_query: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
