from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class AuthorBase(BaseModel):
    name: str = Field(..., max_length=200)
    email: str = Field(..., max_length=200)
    country: Optional[str] = Field(None, max_length=100)
    is_active: bool = Field(default=True)
    birth_year: Optional[int] = None


class AuthorCreate(AuthorBase):
    pass


class AuthorUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    email: Optional[str] = Field(None, max_length=200)
    country: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    birth_year: Optional[int] = None


class AuthorResponse(AuthorBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AuthorWithBooksResponse(AuthorResponse):
    books: List["BookResponse"] = []
    
    class Config:
        from_attributes = True
