from typing import Any, Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field

from app.enums.sort_order import SortOrder
from app.schema.filter_node import FilterNode


class SavedFilterCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    model_name: str = Field(..., max_length=100)
    filters: Optional[List[Dict[str, Any]]] = None
    filter_tree: Optional[FilterNode] = None
    sort_by: Optional[str] = None
    sort_order: SortOrder = SortOrder.ASC
    page_size: int = Field(default=20, ge=1, le=100)
    search_query: Optional[str] = None

    model_config = {"protected_namespaces": ()}


class SavedFilterUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    filters: Optional[List[Dict[str, Any]]] = None
    filter_tree: Optional[FilterNode] = None
    sort_by: Optional[str] = None
    sort_order: Optional[SortOrder] = None
    page_size: Optional[int] = Field(default=None, ge=1, le=100)
    search_query: Optional[str] = None


class SavedFilterResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    model_name: str
    filters: Optional[List[Dict[str, Any]]] = None
    filter_tree: Optional[FilterNode] = None
    sort_by: Optional[str] = None
    sort_order: SortOrder = SortOrder.ASC
    page_size: int = Field(default=20, ge=1, le=100)
    search_query: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True, "protected_namespaces": ()}
