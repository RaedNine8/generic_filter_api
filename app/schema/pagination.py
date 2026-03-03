from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field


class GenericPaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    size: int = Field(default=20, ge=1, le=100, description="Items per page")


class PaginatedResponseMetadata(BaseModel):
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")


T = TypeVar("T")


class GenericPaginatedResponse(BaseModel, Generic[T]):
    data: List[T] = Field(..., description="List of items")
    meta: PaginatedResponseMetadata = Field(..., description="Pagination metadata")
