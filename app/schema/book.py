from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class BookBase(BaseModel):
    title: str = Field(..., max_length=300)
    isbn: str = Field(..., max_length=20)
    genre: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    price: float = Field(default=0.0, ge=0)
    pages: Optional[int] = Field(None, ge=1)
    published_year: Optional[int] = None
    is_available: bool = Field(default=True)
    rating: Optional[float] = Field(None, ge=0, le=5)
    author_id: int


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=300)
    isbn: Optional[str] = Field(None, max_length=20)
    genre: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    pages: Optional[int] = Field(None, ge=1)
    published_year: Optional[int] = None
    is_available: Optional[bool] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    author_id: Optional[int] = None


class AuthorNestedResponse(BaseModel):
    id: int
    name: str
    email: str
    country: Optional[str] = None
    is_active: bool
    
    class Config:
        from_attributes = True


class BookResponse(BookBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class BookWithAuthorResponse(BookResponse):
    author: AuthorNestedResponse
    
    class Config:
        from_attributes = True
