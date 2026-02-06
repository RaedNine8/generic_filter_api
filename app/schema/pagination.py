from typing import List, Generic, TypeVar
from pydantic import BaseModel, Field


class GenericPaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    size: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    class Config:
        from_attributes = True


class PaginatedResponseMetadata(BaseModel):
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")
    
    class Config:
        from_attributes = True


T = TypeVar('T')


class GenericPaginatedResponse(BaseModel, Generic[T]):
    data: List[T] = Field(..., description="List of items")
    meta: PaginatedResponseMetadata = Field(..., description="Pagination metadata")
    
    class Config:
        from_attributes = True
