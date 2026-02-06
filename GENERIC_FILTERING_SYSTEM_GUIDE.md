# Generic Filtering System - Complete Integration Guide

A comprehensive, portable filtering, sorting, pagination, and search system for FastAPI (backend) + Angular (frontend) applications.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Backend Setup (FastAPI + SQLAlchemy)](#backend-setup-fastapi--sqlalchemy)
   - [Required Files](#backend-required-files)
   - [Database Migration](#database-migration)
   - [Creating Entity Endpoints](#creating-entity-endpoints)
5. [Frontend Setup (Angular)](#frontend-setup-angular)
   - [Required Files](#frontend-required-files)
   - [Creating Entity Configurations](#creating-entity-configurations)
   - [Using the Generic Components](#using-the-generic-components)
6. [URL Grammar Reference](#url-grammar-reference)
7. [Filter Operations Reference](#filter-operations-reference)
8. [Complete Code Files](#complete-code-files)
9. [Step-by-Step Integration Checklist](#step-by-step-integration-checklist)

---

## Overview

This system provides a **fully generic, reusable filtering mechanism** that can be applied to any entity in any project. The key principle is **configuration over code** - you define your entity's fields, columns, and filter presets in configuration files, and the generic components handle everything else.

### What Makes This Portable?

- **Backend**: Generic `QueryFilterBuilder` and `GenericQueryExecutor` classes work with ANY SQLAlchemy model
- **Frontend**: Generic `EntityListComponent` works with ANY entity - just provide a configuration object
- **URL Grammar**: Standard query parameter format (`field_operation=value`) works universally
- **Saved Filters**: Stored in database with `model_name` field to support multiple entities

---

## Features

| Feature                    | Description                                                                  |
| -------------------------- | ---------------------------------------------------------------------------- |
| **Dynamic Filtering**      | 15+ filter operations (equals, contains, greater than, in list, etc.)        |
| **Relationship Filtering** | Filter by related entity fields using dot notation (`author.country_eq=USA`) |
| **Sorting**                | Sort by any field, ascending or descending                                   |
| **Pagination**             | Configurable page sizes with metadata (total items, pages, has_next, etc.)   |
| **Full-Text Search**       | Search across multiple fields simultaneously                                 |
| **Quick Filters**          | Predefined filter presets (e.g., "Available Books", "High Rated")            |
| **Saved Filters**          | Persist filter configurations to database for reuse                          |
| **Group By**               | Group results by field (UI support)                                          |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Angular)                       │
├─────────────────────────────────────────────────────────────────┤
│  EntityConfig (book.config.ts)                                   │
│       ↓                                                          │
│  EntityListComponent ←→ AdvancedSearchPanelComponent             │
│       ↓                                                          │
│  HTTP Request: GET /api/books?price_gte=10&sort_by=rating       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND (FastAPI)                        │
├─────────────────────────────────────────────────────────────────┤
│  URL Grammar Parser (dependencies.py)                            │
│       ↓                                                          │
│  GenericQueryExecutor                                            │
│       ↓                                                          │
│  QueryFilterBuilder → SQLAlchemy Query → Database                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Backend Setup (FastAPI + SQLAlchemy)

### Backend Required Files

Create the following directory structure:

```
your_project/
├── app/
│   ├── __init__.py
│   ├── database.py          # SQLAlchemy setup
│   ├── main.py              # FastAPI app
│   ├── enums/
│   │   ├── __init__.py
│   │   ├── filter_operation.py
│   │   └── sort_order.py
│   ├── generics/
│   │   ├── __init__.py
│   │   ├── filter_builder.py
│   │   ├── query_executor.py
│   │   └── dependencies.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── saved_filter.py   # Required for saved filters feature
│   │   └── your_entity.py
│   ├── schema/
│   │   ├── __init__.py
│   │   ├── filtering.py
│   │   ├── pagination.py
│   │   ├── sorting.py
│   │   └── saved_filter.py
│   └── routers/
│       ├── __init__.py
│       └── your_router.py
├── alembic/                   # Database migrations
│   └── versions/
└── alembic.ini
```

---

### File 1: `app/enums/filter_operation.py`

```python
from enum import Enum


class FilterOperation(str, Enum):
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_EQUAL = "lte"
    LIKE = "like"
    ILIKE = "ilike"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IN = "in"
    NOT_IN = "not_in"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    BETWEEN = "between"
```

---

### File 2: `app/enums/sort_order.py`

```python
from enum import Enum


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"
```

---

### File 3: `app/schema/pagination.py`

```python
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
```

---

### File 4: `app/schema/sorting.py`

```python
from typing import Optional
from pydantic import BaseModel, Field
from app.enums.sort_order import SortOrder


class GenericSortParams(BaseModel):
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    order: SortOrder = Field(default=SortOrder.ASC, description="Sort order")

    class Config:
        from_attributes = True
```

---

### File 5: `app/schema/filtering.py`

```python
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
                raise ValueError(f"Value must be a list for {operation} operation.")
            if len(v) == 0:
                raise ValueError(f"Value list cannot be empty for {operation} operation.")

        if operation == FilterOperation.BETWEEN:
            if not isinstance(v, (list, tuple)):
                raise ValueError("Value must be a list or tuple for BETWEEN operation.")
            if len(v) != 2:
                raise ValueError("Value must contain exactly 2 elements for BETWEEN operation.")

        if operation in [FilterOperation.IS_NULL, FilterOperation.IS_NOT_NULL]:
            if v not in [True, False, None]:
                raise ValueError(f"Value must be boolean for {operation} operation.")

        return v

    class Config:
        from_attributes = True
```

---

### File 6: `app/generics/filter_builder.py`

```python
from typing import Dict, Any, List, Type
from sqlalchemy.orm import Query
from app.enums.filter_operation import FilterOperation
from app.schema.filtering import FilterParam


class QueryFilterBuilder:
    """
    Generic filter builder that applies filters to SQLAlchemy queries.
    Supports relationship filtering via dot notation (e.g., 'author.country').
    """

    FILTER_OPERATIONS = {
        FilterOperation.EQUALS: lambda col, val: col == val,
        FilterOperation.NOT_EQUALS: lambda col, val: col != val,
        FilterOperation.GREATER_THAN: lambda col, val: col > val,
        FilterOperation.GREATER_EQUAL: lambda col, val: col >= val,
        FilterOperation.LESS_THAN: lambda col, val: col < val,
        FilterOperation.LESS_EQUAL: lambda col, val: col <= val,
        FilterOperation.LIKE: lambda col, val: col.like(f"%{val}%"),
        FilterOperation.ILIKE: lambda col, val: col.ilike(f"%{val}%"),
        FilterOperation.IN: lambda col, val: col.in_(val),
        FilterOperation.NOT_IN: lambda col, val: ~col.in_(val),
        FilterOperation.IS_NULL: lambda col, val: col.is_(None) if val else col.isnot(None),
        FilterOperation.IS_NOT_NULL: lambda col, val: col.isnot(None) if val else col.is_(None),
        FilterOperation.BETWEEN: lambda col, val: col.between(val[0], val[1]),
        FilterOperation.STARTS_WITH: lambda col, val: col.like(f"{val}%"),
        FilterOperation.ENDS_WITH: lambda col, val: col.like(f"%{val}"),
    }

    def __init__(self, query: Query, model: Type[Any]):
        self.query = query
        self.model = model

    def apply_filter(self, field: str, operation: FilterOperation, value: Any) -> 'QueryFilterBuilder':
        """Apply a single filter. Supports dot notation for relationships."""

        if '.' in field:
            # Relationship filter (e.g., 'author.country')
            parts = field.split('.', 1)
            relationship_name = parts[0]
            related_field = parts[1]

            if not hasattr(self.model, relationship_name):
                raise ValueError(f"Model '{self.model.__name__}' has no relationship '{relationship_name}'.")

            relationship_attr = getattr(self.model, relationship_name)

            if not hasattr(relationship_attr, 'property'):
                raise ValueError(f"Attribute '{relationship_name}' on model '{self.model.__name__}' is not a relationship")

            related_model = relationship_attr.property.mapper.class_

            if not hasattr(related_model, related_field):
                raise ValueError(f"Related model '{related_model.__name__}' has no field '{related_field}'.")

            column = getattr(related_model, related_field)
            self.query = self.query.join(relationship_attr)
        else:
            # Direct field filter
            if not hasattr(self.model, field):
                raise ValueError(f"Model '{self.model.__name__}' has no field '{field}'.")
            column = getattr(self.model, field)

        filter_func = self.FILTER_OPERATIONS.get(operation)

        if filter_func is None:
            raise ValueError(f"Unsupported filter operation: {operation}")

        try:
            filter_condition = filter_func(column, value)
            self.query = self.query.filter(filter_condition)
        except Exception as e:
            raise ValueError(f"Failed to apply filter on field '{field}' with operation '{operation}': {str(e)}")

        return self

    def apply_filters_from_dict(self, filters: Dict[str, Any]) -> 'QueryFilterBuilder':
        """Apply filters from a dictionary format."""
        for field, filter_value in filters.items():
            if isinstance(filter_value, dict) and "operation" in filter_value:
                operation = FilterOperation(filter_value["operation"])
                value = filter_value["value"]
                self.apply_filter(field, operation, value)
            else:
                self.apply_filter(field, FilterOperation.EQUALS, filter_value)
        return self

    def apply_filters_from_list(self, filter_list: List[Dict[str, Any]]) -> 'QueryFilterBuilder':
        """Apply filters from a list of filter dictionaries."""
        for filter_dict in filter_list:
            field = filter_dict.get("field")
            operation_str = filter_dict.get("operation")
            value = filter_dict.get("value")

            if not field or not operation_str:
                raise ValueError(f"Invalid filter dict: {filter_dict}. Must have 'field' and 'operation'.")

            operation = FilterOperation(operation_str)
            self.apply_filter(field, operation, value)
        return self

    def apply_filters_from_params(self, filter_params: List[FilterParam]) -> 'QueryFilterBuilder':
        """Apply filters from FilterParam objects."""
        for param in filter_params:
            self.apply_filter(param.field, param.operation, param.value)
        return self

    def get_query(self) -> Query:
        """Return the modified query."""
        return self.query
```

---

### File 7: `app/generics/query_executor.py`

```python
from typing import Dict, Any, Optional, List, Tuple, Type
from sqlalchemy import String, cast, or_, desc, asc
from sqlalchemy.orm import Session, Query
from pydantic import BaseModel
from app.enums.sort_order import SortOrder
from app.schema.pagination import GenericPaginationParams, PaginatedResponseMetadata
from app.schema.sorting import GenericSortParams
from app.schema.filtering import FilterParam
from app.generics.filter_builder import QueryFilterBuilder


class GenericQueryExecutor:
    """
    Generic query executor that handles filtering, sorting, pagination, and search
    for any SQLAlchemy model.
    """

    def __init__(
        self,
        model: Type[Any],
        db: Session,
        sortable_fields: Optional[List[str]] = None,
        searchable_fields: Optional[List[str]] = None,
        default_sort_field: str = "id",
        default_sort_order: SortOrder = SortOrder.DESC
    ):
        self.model = model
        self.db = db
        self.sortable_fields = sortable_fields or []
        self.searchable_fields = searchable_fields or []
        self.default_sort_field = default_sort_field
        self.default_sort_order = default_sort_order

    def execute(
        self,
        pagination: GenericPaginationParams,
        sort: Optional[GenericSortParams] = None,
        filters: Optional[Any] = None,
        filter_params: Optional[List[FilterParam]] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Any], int]:
        """Execute the query with all parameters applied."""
        query = self.db.query(self.model)

        # Apply filters
        if filters:
            if isinstance(filters, list):
                query = self._apply_list_filters(query, filters)
            elif isinstance(filters, dict):
                query = self._apply_dict_filters(query, filters)

        if filter_params:
            query = self._apply_param_filters(query, filter_params)

        # Apply search
        if search and self.searchable_fields:
            query = self._apply_search(query, search)

        # Get total count before pagination
        total_count = query.count()

        # Apply sorting and pagination
        query = self._apply_sorting(query, sort)
        query = self._apply_pagination(query, pagination)

        items = query.all()

        return items, total_count

    def _apply_dict_filters(self, query: Query, filters: Dict[str, Any]) -> Query:
        filter_builder = QueryFilterBuilder(query, self.model)
        filter_builder.apply_filters_from_dict(filters)
        return filter_builder.get_query()

    def _apply_list_filters(self, query: Query, filter_list: List[Dict[str, Any]]) -> Query:
        filter_builder = QueryFilterBuilder(query, self.model)
        filter_builder.apply_filters_from_list(filter_list)
        return filter_builder.get_query()

    def _apply_param_filters(self, query: Query, filter_params: List[FilterParam]) -> Query:
        filter_builder = QueryFilterBuilder(query, self.model)
        filter_builder.apply_filters_from_params(filter_params)
        return filter_builder.get_query()

    def _apply_search(self, query: Query, search: str) -> Query:
        """Apply full-text search across searchable fields."""
        search_conditions = []
        for field_name in self.searchable_fields:
            if hasattr(self.model, field_name):
                column = getattr(self.model, field_name)
                search_conditions.append(cast(column, String).ilike(f"%{search}%"))
        if search_conditions:
            query = query.filter(or_(*search_conditions))
        return query

    def _apply_sorting(self, query: Query, sort: Optional[GenericSortParams]) -> Query:
        """Apply sorting to the query."""
        if sort and sort.sort_by:
            if self.sortable_fields and sort.sort_by not in self.sortable_fields:
                raise ValueError(f"Invalid sort field '{sort.sort_by}'.")
            if hasattr(self.model, sort.sort_by):
                column = getattr(self.model, sort.sort_by)
                if sort.order == SortOrder.DESC:
                    query = query.order_by(desc(column))
                else:
                    query = query.order_by(asc(column))
        else:
            # Apply default sorting
            if hasattr(self.model, self.default_sort_field):
                column = getattr(self.model, self.default_sort_field)
                if self.default_sort_order == SortOrder.DESC:
                    query = query.order_by(desc(column))
                else:
                    query = query.order_by(asc(column))
        return query

    def _apply_pagination(self, query: Query, pagination: GenericPaginationParams) -> Query:
        """Apply pagination to the query."""
        skip = (pagination.page - 1) * pagination.size
        return query.offset(skip).limit(pagination.size)

    def create_paginated_response(
        self,
        items: List[Any],
        total_count: int,
        pagination: GenericPaginationParams,
        response_model: Type[BaseModel]
    ) -> Dict[str, Any]:
        """Create a standardized paginated response."""
        total_pages = (total_count + pagination.size - 1) // pagination.size if total_count > 0 else 0
        has_next = pagination.page < total_pages
        has_previous = pagination.page > 1

        # Convert SQLAlchemy models to Pydantic
        data = [response_model.model_validate(item) for item in items]

        metadata = PaginatedResponseMetadata(
            page=pagination.page,
            size=pagination.size,
            total_items=total_count,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous
        )

        return {"data": data, "meta": metadata}
```

---

### File 8: `app/generics/dependencies.py`

```python
from typing import Optional, List, Type, Any
from fastapi import Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from app.enums.sort_order import SortOrder
from app.schema.pagination import GenericPaginationParams
from app.schema.sorting import GenericSortParams
from app.generics.query_executor import GenericQueryExecutor
from app.database import get_db


def create_query_executor_dependency(
    model: Type[Any],
    sortable_fields: Optional[List[str]] = None,
    searchable_fields: Optional[List[str]] = None,
    default_sort_field: str = "id",
    default_sort_order: SortOrder = SortOrder.DESC
):
    """Factory to create a query executor dependency for a specific model."""
    def query_executor_dependency(db: Session = Depends(get_db)) -> GenericQueryExecutor:
        return GenericQueryExecutor(
            model=model,
            db=db,
            sortable_fields=sortable_fields,
            searchable_fields=searchable_fields,
            default_sort_field=default_sort_field,
            default_sort_order=default_sort_order
        )
    return query_executor_dependency


def create_pagination_dependency(
    default_page: int = 1,
    default_size: int = 20,
    max_size: int = 100
):
    """Factory to create a pagination dependency with custom defaults."""
    def pagination_dependency(
        page: int = Query(default_page, ge=1, description="Page number (1-indexed)"),
        size: int = Query(default_size, ge=1, description="Items per page")
    ) -> GenericPaginationParams:
        if size > max_size:
            size = max_size
        return GenericPaginationParams(page=page, size=size)
    return pagination_dependency


def create_sort_dependency(
    sortable_fields: Optional[List[str]] = None,
    default_sort_by: Optional[str] = None,
    default_order: SortOrder = SortOrder.ASC
):
    """Factory to create a sort dependency with field validation."""
    def sort_dependency(
        sort_by: Optional[str] = Query(default_sort_by, description="Field to sort by"),
        order: SortOrder = Query(default_order, description="Sort order (asc/desc)")
    ) -> GenericSortParams:
        if sort_by and sortable_fields and sort_by not in sortable_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sort field '{sort_by}'. Allowed fields: {', '.join(sortable_fields)}"
            )
        return GenericSortParams(sort_by=sort_by, order=order)
    return sort_dependency


def create_search_dependency(min_length: int = 2, max_length: int = 100):
    """Factory to create a search dependency with validation."""
    def search_dependency(
        search: Optional[str] = Query(None, description=f"Search string ({min_length}-{max_length} chars)")
    ) -> Optional[str]:
        if search is not None:
            if len(search) < min_length:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Search string must be at least {min_length} characters."
                )
            if len(search) > max_length:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Search string must be at most {max_length} characters."
                )
        return search
    return search_dependency


# ============================================================================
# URL GRAMMAR FILTER PARSING
# ============================================================================

URL_GRAMMAR_OPERATIONS = {
    "eq": "eq", "ne": "ne", "gt": "gt", "gte": "gte", "lt": "lt", "lte": "lte",
    "like": "like", "ilike": "ilike", "in": "in", "not_in": "not_in",
    "is_null": "is_null", "is_not_null": "is_not_null", "between": "between",
    "starts_with": "starts_with", "ends_with": "ends_with",
}


def parse_url_filter_param(key: str, value: str) -> Optional[dict]:
    """
    Parse a URL query parameter into a filter rule.

    Examples:
        - price_gte=100 → {"field": "price", "operation": "gte", "value": 100}
        - author.country_eq=USA → {"field": "author.country", "operation": "eq", "value": "USA"}
        - status_in=active,pending → {"field": "status", "operation": "in", "value": ["active", "pending"]}
    """
    sorted_ops = sorted(URL_GRAMMAR_OPERATIONS.keys(), key=len, reverse=True)

    for op_suffix in sorted_ops:
        suffix = f"_{op_suffix}"
        if key.endswith(suffix):
            field_name = key[:-len(suffix)]
            if field_name:
                parsed_value = _parse_filter_value(value, op_suffix)
                return {"field": field_name, "operation": op_suffix, "value": parsed_value}

    # Default to equals if no operation suffix found
    return {"field": key, "operation": "eq", "value": _parse_filter_value(value, "eq")}


def _parse_filter_value(value: str, operation: str):
    """Parse and convert filter values based on operation type."""
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    if value.lower() == 'null':
        return None

    if operation in ['in', 'not_in']:
        items = [item.strip() for item in value.split(',')]
        return [_convert_scalar_value(item) for item in items]

    if operation == 'between':
        parts = [part.strip() for part in value.split(',')]
        if len(parts) == 2:
            return [_convert_scalar_value(parts[0]), _convert_scalar_value(parts[1])]
        return value

    return _convert_scalar_value(value)


def _convert_scalar_value(value: str):
    """Convert string value to appropriate Python type."""
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    if value.lower() == 'null':
        return None

    # Try integer
    try:
        return int(value)
    except ValueError:
        pass

    # Try float
    try:
        return float(value)
    except ValueError:
        pass

    return value


def create_url_grammar_filter_dependency(
    reserved_keys: Optional[List[str]] = None,
    max_filters: int = 50
):
    """
    Factory to create a URL grammar filter parsing dependency.

    Reserved keys (page, size, sort_by, etc.) are automatically excluded.
    All other query parameters are parsed as filters.
    """
    default_reserved = ['page', 'size', 'page_size', 'sort_by', 'order', 'sort_order', 'search', 'filter_id']
    all_reserved = set(default_reserved + (reserved_keys or []))

    def url_grammar_filter_dependency(request: Request) -> List[dict]:
        filters = []
        for key, value in request.query_params.items():
            if key in all_reserved:
                continue
            if not value:
                continue
            filter_rule = parse_url_filter_param(key, value)
            if filter_rule:
                filters.append(filter_rule)

        if len(filters) > max_filters:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Too many filter parameters. Maximum allowed: {max_filters}"
            )
        return filters

    return url_grammar_filter_dependency
```

---

### File 9: `app/models/saved_filter.py`

```python
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from datetime import datetime
from app.database import Base


class SavedFilter(Base):
    """
    Model for storing saved filter configurations.
    Allows users to save and reuse filter presets.
    """
    __tablename__ = "saved_filters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    model_name = Column(String(100), nullable=False, index=True)  # e.g., 'Book', 'User', 'Order'
    filters = Column(JSON, nullable=False, default=list)  # List of filter rules
    sort_by = Column(String(100), nullable=True)
    sort_order = Column(String(4), default="desc")  # 'asc' or 'desc'
    page_size = Column(Integer, default=20)
    search_query = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)
```

---

### File 10: `app/schema/saved_filter.py`

```python
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
    page_size: int = 20
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
    page_size: int = 20
    search_query: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
```

---

### Database Migration

Create a migration for the `saved_filters` table:

```bash
# Generate migration
alembic revision --autogenerate -m "Add saved_filters table"

# Apply migration
alembic upgrade head
```

**Migration file content** (auto-generated, but ensure it includes):

```python
def upgrade() -> None:
    op.create_table('saved_filters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('filters', sa.JSON(), nullable=False),
        sa.Column('sort_by', sa.String(length=100), nullable=True),
        sa.Column('sort_order', sa.String(length=4), nullable=True),
        sa.Column('page_size', sa.Integer(), nullable=True),
        sa.Column('search_query', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_saved_filters_id', 'saved_filters', ['id'], unique=False)
    op.create_index('ix_saved_filters_model_name', 'saved_filters', ['model_name'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_saved_filters_model_name', table_name='saved_filters')
    op.drop_index('ix_saved_filters_id', table_name='saved_filters')
    op.drop_table('saved_filters')
```

---

### Creating Entity Endpoints

For each entity, create a router with the generic filtering support:

```python
# app/routers/your_entity.py

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query, Request, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.your_entity import YourEntity
from app.models.saved_filter import SavedFilter
from app.schema.your_entity import YourEntityResponse
from app.schema.saved_filter import SavedFilterCreate, SavedFilterResponse
from app.schema.pagination import GenericPaginationParams
from app.schema.sorting import GenericSortParams
from app.enums.sort_order import SortOrder
from app.generics.query_executor import GenericQueryExecutor
from app.generics.dependencies import create_url_grammar_filter_dependency

router = APIRouter(prefix="/api", tags=["YourEntity"])


@router.get("/your-entities", response_model=Dict[str, Any])
def list_entities(
    request: Request,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query("id"),
    order: SortOrder = Query(SortOrder.DESC),
    search: Optional[str] = Query(None),
    url_filters: List[dict] = Depends(create_url_grammar_filter_dependency()),
    db: Session = Depends(get_db)
):
    pagination = GenericPaginationParams(page=page, size=size)
    sort_params = GenericSortParams(sort_by=sort_by, order=order)

    executor = GenericQueryExecutor(
        model=YourEntity,
        db=db,
        sortable_fields=["id", "name", "created_at"],  # Customize for your entity
        searchable_fields=["name", "description"],      # Customize for your entity
        default_sort_field="id",
        default_sort_order=SortOrder.DESC
    )

    items, total = executor.execute(
        pagination=pagination,
        sort=sort_params,
        filters=url_filters,
        search=search
    )

    return executor.create_paginated_response(
        items=items,
        total_count=total,
        pagination=pagination,
        response_model=YourEntityResponse
    )


# ============ SAVED FILTERS ENDPOINTS (Add once, reuse for all entities) ============

@router.get("/saved-filters", response_model=List[SavedFilterResponse])
def list_saved_filters(model_name: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(SavedFilter)
    if model_name:
        query = query.filter(SavedFilter.model_name == model_name)
    return query.order_by(SavedFilter.created_at.desc()).all()


@router.post("/saved-filters", response_model=SavedFilterResponse, status_code=status.HTTP_201_CREATED)
def create_saved_filter(data: SavedFilterCreate, db: Session = Depends(get_db)):
    sf = SavedFilter(
        name=data.name,
        description=data.description,
        model_name=data.model_name,
        filters=[f.dict() for f in data.filters],
        sort_by=data.sort_by,
        sort_order=data.sort_order,
        page_size=data.page_size,
        search_query=data.search_query
    )
    db.add(sf)
    db.commit()
    db.refresh(sf)
    return sf


@router.get("/saved-filters/{filter_id}", response_model=SavedFilterResponse)
def get_saved_filter(filter_id: int, db: Session = Depends(get_db)):
    sf = db.query(SavedFilter).filter(SavedFilter.id == filter_id).first()
    if not sf:
        raise HTTPException(status_code=404, detail="Saved filter not found")
    return sf


@router.delete("/saved-filters/{filter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_filter(filter_id: int, db: Session = Depends(get_db)):
    sf = db.query(SavedFilter).filter(SavedFilter.id == filter_id).first()
    if not sf:
        raise HTTPException(status_code=404, detail="Saved filter not found")
    db.delete(sf)
    db.commit()
    return None
```

---

## Frontend Setup (Angular)

### Frontend Required Files

Create the following directory structure:

```
frontend/src/app/
├── core/
│   ├── enums/
│   │   ├── index.ts
│   │   ├── filter-operation.enum.ts
│   │   └── sort-order.enum.ts
│   ├── interfaces/
│   │   ├── index.ts
│   │   ├── filter.interface.ts
│   │   ├── pagination.interface.ts
│   │   ├── saved-filter.interface.ts
│   │   └── entity-config.interface.ts
│   └── services/
│       ├── index.ts
│       └── saved-filter.service.ts
├── shared/
│   └── components/
│       ├── advanced-search-panel/
│       │   ├── advanced-search-panel.component.ts
│       │   ├── advanced-search-panel.component.html
│       │   └── advanced-search-panel.component.scss
│       ├── data-table/
│       │   ├── data-table.component.ts
│       │   ├── data-table.component.html
│       │   └── data-table.component.scss
│       └── entity-list/
│           └── entity-list.component.ts
├── config/
│   ├── index.ts
│   └── entities/
│       ├── index.ts
│       └── your-entity.config.ts
└── features/
    └── your-entity/
        ├── your-entity-list.component.ts
        └── index.ts
```

---

### File 1: `core/enums/filter-operation.enum.ts`

```typescript
/**
 * Filter Operations Enum
 * Must match backend FilterOperation enum values exactly
 */
export enum FilterOperation {
  EQUALS = "eq",
  NOT_EQUALS = "ne",
  GREATER_THAN = "gt",
  GREATER_EQUAL = "gte",
  LESS_THAN = "lt",
  LESS_EQUAL = "lte",
  LIKE = "like",
  ILIKE = "ilike",
  STARTS_WITH = "starts_with",
  ENDS_WITH = "ends_with",
  IN = "in",
  NOT_IN = "not_in",
  IS_NULL = "is_null",
  IS_NOT_NULL = "is_not_null",
  BETWEEN = "between",
}

/**
 * Human-readable labels for filter operations
 */
export const FILTER_OPERATION_LABELS: Record<FilterOperation, string> = {
  [FilterOperation.EQUALS]: "Equals",
  [FilterOperation.NOT_EQUALS]: "Not Equals",
  [FilterOperation.GREATER_THAN]: "Greater Than",
  [FilterOperation.GREATER_EQUAL]: "Greater or Equal",
  [FilterOperation.LESS_THAN]: "Less Than",
  [FilterOperation.LESS_EQUAL]: "Less or Equal",
  [FilterOperation.LIKE]: "Contains (case-sensitive)",
  [FilterOperation.ILIKE]: "Contains",
  [FilterOperation.STARTS_WITH]: "Starts With",
  [FilterOperation.ENDS_WITH]: "Ends With",
  [FilterOperation.IN]: "In List",
  [FilterOperation.NOT_IN]: "Not In List",
  [FilterOperation.IS_NULL]: "Is Empty",
  [FilterOperation.IS_NOT_NULL]: "Is Not Empty",
  [FilterOperation.BETWEEN]: "Between",
};

export function operationNeedsValue(operation: FilterOperation): boolean {
  return ![FilterOperation.IS_NULL, FilterOperation.IS_NOT_NULL].includes(
    operation,
  );
}
```

---

### File 2: `core/enums/sort-order.enum.ts`

```typescript
export enum SortOrder {
  ASC = "asc",
  DESC = "desc",
}
```

---

### File 3: `core/interfaces/filter.interface.ts`

```typescript
import { FilterOperation } from "../enums/filter-operation.enum";

export interface FilterRule {
  field: string;
  operation: FilterOperation | string;
  value: any;
}
```

---

### File 4: `core/interfaces/pagination.interface.ts`

```typescript
import { SortOrder } from "../enums/sort-order.enum";

export interface PaginationParams {
  page: number;
  size: number;
}

export interface PaginationMeta {
  page: number;
  size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface SortParams {
  sort_by: string | null;
  order: SortOrder;
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: PaginationMeta;
}
```

---

### File 5: `core/interfaces/saved-filter.interface.ts`

```typescript
import { FilterRule } from "./filter.interface";
import { SortOrder } from "../enums/sort-order.enum";

export interface SavedFilter {
  id: number;
  name: string;
  description?: string | null;
  model_name: string;
  filters: FilterRule[];
  sort_by?: string | null;
  sort_order: SortOrder | string;
  page_size: number;
  search_query?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface SavedFilterCreate {
  name: string;
  description?: string;
  model_name: string;
  filters: FilterRule[];
  sort_by?: string;
  sort_order?: SortOrder | string;
  page_size?: number;
  search_query?: string;
}

export interface SavedFilterUpdate {
  name?: string;
  description?: string;
  filters?: FilterRule[];
  sort_by?: string;
  sort_order?: SortOrder | string;
  page_size?: number;
  search_query?: string;
}
```

---

### File 6: `core/interfaces/entity-config.interface.ts`

```typescript
import { FilterRule } from "./filter.interface";
import { FilterOperation } from "../enums/filter-operation.enum";
import { SortOrder } from "../enums/sort-order.enum";

export type FieldType =
  | "text"
  | "number"
  | "boolean"
  | "date"
  | "datetime"
  | "select";

export interface SelectOption {
  label: string;
  value: string | number | boolean;
}

export interface FieldConfig {
  name: string;
  label: string;
  type: FieldType;
  sortable?: boolean;
  searchable?: boolean;
  defaultOperation?: FilterOperation;
  options?: SelectOption[];
}

export interface ColumnConfig<T = unknown> {
  field: string;
  header: string;
  sortable?: boolean;
  type?:
    | "text"
    | "number"
    | "currency"
    | "date"
    | "datetime"
    | "boolean"
    | "custom";
  width?: string;
}

export interface QuickFilterConfig {
  id: string;
  label: string;
  icon?: string;
  category?: string;
  filters: FilterRule[];
  isHeader?: boolean;
}

export interface GroupByConfig {
  field: string;
  label: string;
  icon?: string;
}

export interface DefaultsConfig {
  pageSize?: number;
  sortField?: string | null;
  sortOrder?: SortOrder;
  pageSizeOptions?: number[];
}

/**
 * Complete entity configuration - define one per entity
 */
export interface EntityConfig<T = unknown> {
  name: string;
  pluralLabel: string;
  singularLabel: string;
  apiEndpoint: string;
  searchPlaceholder?: string;
  emptyMessage?: string;
  fields: FieldConfig[];
  columns: ColumnConfig<T>[];
  quickFilters?: QuickFilterConfig[];
  groupByOptions?: GroupByConfig[];
  defaults?: DefaultsConfig;
}

// Helper functions
export function createFieldConfig(
  name: string,
  label: string,
  type: FieldType,
  options?: Partial<FieldConfig>,
): FieldConfig {
  return {
    name,
    label,
    type,
    sortable: true,
    searchable: type === "text",
    defaultOperation:
      type === "text" ? FilterOperation.ILIKE : FilterOperation.EQUALS,
    ...options,
  };
}

export function createColumnConfig<T>(
  field: string,
  header: string,
  options?: Partial<ColumnConfig<T>>,
): ColumnConfig<T> {
  return { field, header, sortable: true, ...options };
}

export function createQuickFilter(
  id: string,
  label: string,
  filters: FilterRule[],
  options?: Partial<QuickFilterConfig>,
): QuickFilterConfig {
  return { id, label, filters, ...options };
}
```

---

### File 7: `core/services/saved-filter.service.ts`

```typescript
import { Injectable } from "@angular/core";
import {
  HttpClient,
  HttpParams,
  HttpErrorResponse,
} from "@angular/common/http";
import { Observable, throwError } from "rxjs";
import { catchError } from "rxjs/operators";
import {
  SavedFilter,
  SavedFilterCreate,
  SavedFilterUpdate,
} from "../interfaces/saved-filter.interface";

@Injectable({
  providedIn: "root",
})
export class SavedFilterService {
  private readonly baseUrl = "/api/saved-filters";

  constructor(private http: HttpClient) {}

  createFilter(filter: SavedFilterCreate): Observable<SavedFilter> {
    return this.http
      .post<SavedFilter>(this.baseUrl, filter)
      .pipe(catchError(this.handleError));
  }

  getFilters(modelName?: string): Observable<SavedFilter[]> {
    let params = new HttpParams();
    if (modelName) {
      params = params.set("model_name", modelName);
    }
    return this.http
      .get<SavedFilter[]>(this.baseUrl, { params })
      .pipe(catchError(this.handleError));
  }

  getFilterById(filterId: number): Observable<SavedFilter> {
    return this.http
      .get<SavedFilter>(`${this.baseUrl}/${filterId}`)
      .pipe(catchError(this.handleError));
  }

  updateFilter(
    filterId: number,
    update: SavedFilterUpdate,
  ): Observable<SavedFilter> {
    return this.http
      .put<SavedFilter>(`${this.baseUrl}/${filterId}`, update)
      .pipe(catchError(this.handleError));
  }

  deleteFilter(filterId: number): Observable<void> {
    return this.http
      .delete<void>(`${this.baseUrl}/${filterId}`)
      .pipe(catchError(this.handleError));
  }

  private handleError = (error: HttpErrorResponse): Observable<never> => {
    console.error("SavedFilterService Error:", error);
    return throwError(() => error);
  };
}
```

---

### File 8: `shared/components/entity-list/entity-list.component.ts`

This is the **main generic component**. See the full implementation in the project files. Key features:

- Takes `EntityConfig` as input
- Handles all filtering, sorting, pagination automatically
- Integrates with `AdvancedSearchPanelComponent` and `DataTableComponent`
- Manages saved filters via `SavedFilterService`

```typescript
import { Component, Input, OnInit, OnDestroy, inject } from "@angular/core";
import { CommonModule } from "@angular/common";
import { HttpClient, HttpParams } from "@angular/common/http";
import { Subject } from "rxjs";
import { takeUntil, finalize } from "rxjs/operators";

import {
  EntityConfig,
  FieldConfig,
  ColumnConfig,
  QuickFilterConfig,
  GroupByConfig,
} from "../../../core/interfaces/entity-config.interface";
import { FilterRule } from "../../../core/interfaces/filter.interface";
import {
  SavedFilter,
  SavedFilterCreate,
} from "../../../core/interfaces/saved-filter.interface";
import { PaginatedResponse } from "../../../core/interfaces/pagination.interface";
import { SortOrder } from "../../../core/enums/sort-order.enum";
import { SavedFilterService } from "../../../core/services/saved-filter.service";

import { AdvancedSearchPanelComponent } from "../advanced-search-panel/advanced-search-panel.component";
import { DataTableComponent } from "../data-table/data-table.component";

@Component({
  selector: "app-entity-list",
  standalone: true,
  imports: [CommonModule, AdvancedSearchPanelComponent, DataTableComponent],
  template: `
    <div class="entity-list-container">
      <header class="page-header" *ngIf="showHeader">
        <h1 class="page-title">{{ config?.pluralLabel }}</h1>
      </header>

      <app-advanced-search-panel
        [modelName]="config?.name || ''"
        [fields]="fields"
        [quickFilters]="quickFilters"
        [groupByOptions]="groupByOptions"
        [activeFilters]="filters"
        [searchQuery]="search"
        [sortBy]="sortField"
        [sortOrder]="sortOrder"
        [savedFilters]="savedFilters"
        [placeholder]="config?.searchPlaceholder || 'Search...'"
        (filtersChange)="onFiltersChange($event)"
        (searchChange)="onSearchChange($event)"
        (groupByChange)="onGroupByChange($event)"
        (saveFilter)="onSaveFilter($event)"
        (applySavedFilter)="onApplySavedFilter($event)"
        (deleteSavedFilter)="onDeleteSavedFilter($event)"
      ></app-advanced-search-panel>

      <app-data-table
        [data]="data"
        [columns]="columns"
        [loading]="loading"
        [pagination]="pagination"
        [sortField]="sortField"
        [sortOrder]="sortOrder"
        [pageSizeOptions]="pageSizeOptions"
        [emptyMessage]="config?.emptyMessage || 'No items found'"
        (sortChange)="onSortChange($event)"
        (pageChange)="onPageChange($event)"
        (pageSizeChange)="onPageSizeChange($event)"
        (rowClick)="onRowClick($event)"
      ></app-data-table>
    </div>
  `,
})
export class EntityListComponent<T = unknown> implements OnInit, OnDestroy {
  @Input() config!: EntityConfig<T>;
  @Input() showHeader = true;

  protected http = inject(HttpClient);
  protected savedFilterService = inject(SavedFilterService);

  data: T[] = [];
  pagination: PaginatedResponse<T>["meta"] | null = null;
  loading = false;
  filters: FilterRule[] = [];
  search = "";
  sortField: string | null = null;
  sortOrder: SortOrder = SortOrder.DESC;
  savedFilters: SavedFilter[] = [];
  protected destroy$ = new Subject<void>();
  protected currentPage = 1;
  protected currentPageSize = 20;

  get fields(): FieldConfig[] {
    return this.config?.fields || [];
  }
  get columns(): ColumnConfig<T>[] {
    return this.config?.columns || [];
  }
  get quickFilters(): QuickFilterConfig[] {
    return this.config?.quickFilters || [];
  }
  get groupByOptions(): GroupByConfig[] {
    return this.config?.groupByOptions || [];
  }
  get pageSizeOptions(): number[] {
    return this.config?.defaults?.pageSizeOptions || [10, 20, 50, 100];
  }

  ngOnInit(): void {
    this.initializeDefaults();
    this.loadData();
    this.loadSavedFilters();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  protected initializeDefaults(): void {
    if (this.config?.defaults) {
      this.sortField = this.config.defaults.sortField ?? null;
      this.sortOrder = this.config.defaults.sortOrder ?? SortOrder.DESC;
      this.currentPageSize = this.config.defaults.pageSize ?? 20;
    }
  }

  loadData(): void {
    if (!this.config?.apiEndpoint) return;
    this.loading = true;
    const params = this.buildQueryParams();

    this.http
      .get<PaginatedResponse<T>>(this.config.apiEndpoint, { params })
      .pipe(
        takeUntil(this.destroy$),
        finalize(() => (this.loading = false)),
      )
      .subscribe({
        next: (response) => {
          this.data = response.data;
          this.pagination = response.meta;
        },
        error: (error) => console.error("Error loading data:", error),
      });
  }

  protected buildQueryParams(): HttpParams {
    let params = new HttpParams()
      .set("page", this.currentPage.toString())
      .set("size", this.currentPageSize.toString());

    if (this.sortField) {
      params = params
        .set("sort_by", this.sortField)
        .set("order", this.sortOrder);
    }
    if (this.search) {
      params = params.set("search", this.search);
    }

    // Filters in URL grammar format: field_operation=value
    for (const filter of this.filters) {
      const paramName = `${filter.field}_${filter.operation}`;
      const value = Array.isArray(filter.value)
        ? filter.value.join(",")
        : String(filter.value);
      params = params.set(paramName, value);
    }

    return params;
  }

  // ... event handlers (see full implementation)
}
```

---

### Creating Entity Configurations

For each entity, create a config file:

```typescript
// config/entities/product.config.ts

import { FilterOperation } from "../../core/enums/filter-operation.enum";
import { SortOrder } from "../../core/enums/sort-order.enum";
import {
  EntityConfig,
  createFieldConfig,
  createColumnConfig,
  createQuickFilter,
} from "../../core/interfaces/entity-config.interface";

export interface Product {
  id: number;
  name: string;
  category: string;
  price: number;
  stock: number;
  is_active: boolean;
  created_at: string;
}

export const PRODUCT_CONFIG: EntityConfig<Product> = {
  // Metadata
  name: "Product", // MUST match backend model_name for saved filters
  pluralLabel: "Products",
  singularLabel: "Product",
  apiEndpoint: "/api/products",
  searchPlaceholder: "Search products...",
  emptyMessage: "No products found",

  // Defaults
  defaults: {
    pageSize: 20,
    sortField: "id",
    sortOrder: SortOrder.DESC,
    pageSizeOptions: [10, 20, 50, 100],
  },

  // Filterable fields
  fields: [
    createFieldConfig("name", "Name", "text", { searchable: true }),
    createFieldConfig("category", "Category", "select", {
      options: [
        { label: "Electronics", value: "Electronics" },
        { label: "Clothing", value: "Clothing" },
        { label: "Books", value: "Books" },
      ],
    }),
    createFieldConfig("price", "Price", "number"),
    createFieldConfig("stock", "Stock", "number"),
    createFieldConfig("is_active", "Active", "boolean"),
    createFieldConfig("created_at", "Created", "date"),
  ],

  // Table columns
  columns: [
    createColumnConfig<Product>("id", "ID", { width: "60px" }),
    createColumnConfig<Product>("name", "Name"),
    createColumnConfig<Product>("category", "Category", { width: "120px" }),
    createColumnConfig<Product>("price", "Price", {
      type: "currency",
      width: "100px",
    }),
    createColumnConfig<Product>("stock", "Stock", {
      type: "number",
      width: "80px",
    }),
    createColumnConfig<Product>("is_active", "Active", {
      type: "boolean",
      width: "80px",
    }),
  ],

  // Quick filters (optional)
  quickFilters: [
    createQuickFilter(
      "in-stock",
      "In Stock",
      [{ field: "stock", operation: FilterOperation.GREATER_THAN, value: 0 }],
      { icon: "📦" },
    ),
    createQuickFilter(
      "active",
      "Active Products",
      [{ field: "is_active", operation: FilterOperation.EQUALS, value: true }],
      { icon: "✅" },
    ),
    createQuickFilter(
      "expensive",
      "Over $100",
      [
        {
          field: "price",
          operation: FilterOperation.GREATER_EQUAL,
          value: 100,
        },
      ],
      { icon: "💰" },
    ),
  ],

  // Group by options (optional)
  groupByOptions: [
    { field: "category", label: "Category", icon: "📁" },
    { field: "is_active", label: "Status", icon: "✅" },
  ],
};
```

---

### Using the Generic Components

**Option 1: Use EntityListComponent directly in routes**

```typescript
// app.routes.ts
import { Routes } from "@angular/router";
import { PRODUCT_CONFIG } from "./config/entities/product.config";

export const routes: Routes = [
  {
    path: "products",
    loadComponent: () =>
      import("./shared/components/entity-list/entity-list.component").then(
        (m) => m.EntityListComponent,
      ),
    data: { config: PRODUCT_CONFIG },
  },
];

// In the component, use ActivatedRoute to get config from route data
```

**Option 2: Create a thin wrapper component (Recommended)**

```typescript
// features/products/product-list.component.ts

import { Component } from "@angular/core";
import { EntityListComponent } from "../../shared/components/entity-list/entity-list.component";
import { PRODUCT_CONFIG, Product } from "../../config/entities/product.config";

@Component({
  selector: "app-product-list",
  standalone: true,
  imports: [EntityListComponent],
  template: `<app-entity-list [config]="config"></app-entity-list>`,
})
export class ProductListComponent {
  config = PRODUCT_CONFIG;
}
```

**Option 3: Extend EntityListComponent for custom behavior**

```typescript
// features/products/product-list.component.ts

import { Component } from "@angular/core";
import { Router } from "@angular/router";
import { EntityListComponent } from "../../shared/components/entity-list/entity-list.component";
import { PRODUCT_CONFIG, Product } from "../../config/entities/product.config";

@Component({
  selector: "app-product-list",
  standalone: true,
  imports: [EntityListComponent],
  template: `
    <app-entity-list
      [config]="config"
      [onRowClicked]="handleRowClick"
    ></app-entity-list>
  `,
})
export class ProductListComponent {
  config = PRODUCT_CONFIG;

  constructor(private router: Router) {}

  handleRowClick = (product: Product) => {
    this.router.navigate(["/products", product.id]);
  };
}
```

---

## URL Grammar Reference

The filter system uses a URL grammar format for query parameters:

| Pattern                   | Example                    | Description                 |
| ------------------------- | -------------------------- | --------------------------- |
| `field_eq=value`          | `status_eq=active`         | Equals                      |
| `field_ne=value`          | `status_ne=deleted`        | Not equals                  |
| `field_gt=value`          | `price_gt=100`             | Greater than                |
| `field_gte=value`         | `price_gte=100`            | Greater than or equal       |
| `field_lt=value`          | `price_lt=50`              | Less than                   |
| `field_lte=value`         | `price_lte=50`             | Less than or equal          |
| `field_like=value`        | `name_like=phone`          | Contains (case-sensitive)   |
| `field_ilike=value`       | `name_ilike=phone`         | Contains (case-insensitive) |
| `field_starts_with=value` | `name_starts_with=i`       | Starts with                 |
| `field_ends_with=value`   | `name_ends_with=pro`       | Ends with                   |
| `field_in=v1,v2,v3`       | `status_in=active,pending` | In list                     |
| `field_not_in=v1,v2`      | `status_not_in=deleted`    | Not in list                 |
| `field_is_null=true`      | `deleted_at_is_null=true`  | Is null                     |
| `field_is_not_null=true`  | `email_is_not_null=true`   | Is not null                 |
| `field_between=v1,v2`     | `price_between=10,100`     | Between two values          |

**Relationship filtering** (dot notation):

```
author.country_eq=USA
category.parent.name_ilike=electronics
```

**Complete example URL**:

```
GET /api/products?page=1&size=20&sort_by=price&order=desc&search=phone&price_gte=100&category_eq=Electronics&is_active_eq=true
```

---

## Filter Operations Reference

| Operation        | Backend Value | Frontend Enum                   | Description                 |
| ---------------- | ------------- | ------------------------------- | --------------------------- |
| Equals           | `eq`          | `FilterOperation.EQUALS`        | Exact match                 |
| Not Equals       | `ne`          | `FilterOperation.NOT_EQUALS`    | Not equal to                |
| Greater Than     | `gt`          | `FilterOperation.GREATER_THAN`  | Greater than                |
| Greater or Equal | `gte`         | `FilterOperation.GREATER_EQUAL` | Greater than or equal       |
| Less Than        | `lt`          | `FilterOperation.LESS_THAN`     | Less than                   |
| Less or Equal    | `lte`         | `FilterOperation.LESS_EQUAL`    | Less than or equal          |
| Like             | `like`        | `FilterOperation.LIKE`          | Contains (case-sensitive)   |
| ILike            | `ilike`       | `FilterOperation.ILIKE`         | Contains (case-insensitive) |
| Starts With      | `starts_with` | `FilterOperation.STARTS_WITH`   | Starts with                 |
| Ends With        | `ends_with`   | `FilterOperation.ENDS_WITH`     | Ends with                   |
| In               | `in`          | `FilterOperation.IN`            | In list of values           |
| Not In           | `not_in`      | `FilterOperation.NOT_IN`        | Not in list                 |
| Is Null          | `is_null`     | `FilterOperation.IS_NULL`       | Is null/empty               |
| Is Not Null      | `is_not_null` | `FilterOperation.IS_NOT_NULL`   | Is not null                 |
| Between          | `between`     | `FilterOperation.BETWEEN`       | Between two values          |

---

## Step-by-Step Integration Checklist

### Backend Checklist

- [ ] 1. Copy `app/enums/filter_operation.py` and `sort_order.py`
- [ ] 2. Copy `app/schema/` files (pagination, sorting, filtering, saved_filter)
- [ ] 3. Copy `app/generics/` files (filter_builder, query_executor, dependencies)
- [ ] 4. Copy `app/models/saved_filter.py`
- [ ] 5. Run migration for `saved_filters` table: `alembic upgrade head`
- [ ] 6. For each entity, create a router endpoint using `GenericQueryExecutor`
- [ ] 7. Add saved filter CRUD endpoints (can be shared across all entities)

### Frontend Checklist

- [ ] 1. Copy `core/enums/` files
- [ ] 2. Copy `core/interfaces/` files
- [ ] 3. Copy `core/services/saved-filter.service.ts`
- [ ] 4. Copy `shared/components/` (entity-list, advanced-search-panel, data-table)
- [ ] 5. Configure proxy for API calls (`proxy.conf.json`)
- [ ] 6. For each entity:
  - [ ] Create interface in config file
  - [ ] Create `EntityConfig` with fields, columns, quickFilters
  - [ ] Create list component (wrapper or extended)
  - [ ] Add route

### Important Notes

1. **Model Name Consistency**: The `name` field in `EntityConfig` MUST match the `model_name` stored in saved filters database
2. **API Endpoint Format**: Must return `{ data: T[], meta: PaginationMeta }` format
3. **Relationship Fields**: Use dot notation both in frontend config and URL params (e.g., `author.country`)
4. **Proxy Configuration**: Ensure Angular dev server proxies `/api` to your backend

---

## Summary

This filtering system provides:

1. **Backend**: Reusable `QueryFilterBuilder` and `GenericQueryExecutor` that work with any SQLAlchemy model
2. **Frontend**: Generic `EntityListComponent` configured via `EntityConfig` objects
3. **Saved Filters**: Persistent storage in database, retrieved by `model_name`
4. **URL Grammar**: Standard query parameter format for all filter operations

To add a new entity:

1. **Backend**: Create model, schema, and router using `GenericQueryExecutor`
2. **Frontend**: Create `EntityConfig` and thin wrapper component
3. That's it! No other code changes needed.
