"""
API routes for Books, Authors, Metadata, and Saved Filters.

Demonstrates both URL-grammar flat filters (GET) and tree-based filters (POST).
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.enums.sort_order import SortOrder
from app.generics.dependencies import (
    create_url_grammar_filter_dependency,
)
from app.generics.introspection import get_model_metadata
from app.generics.query_executor import GenericQueryExecutor
from app.models.author import Author
from app.models.book import Book
from app.models.saved_filter import SavedFilter
from app.schema.author import AuthorResponse
from app.schema.book import BookResponse, BookWithAuthorResponse
from app.schema.filter_node import FilterNode
from app.schema.pagination import GenericPaginationParams
from app.schema.saved_filter import SavedFilterCreate, SavedFilterResponse
from app.schema.sorting import GenericSortParams

router = APIRouter(prefix="/api", tags=["API"])

MODEL_REGISTRY = {"Book": Book, "Author": Author}
RESPONSE_MODEL_REGISTRY = {"Book": BookWithAuthorResponse, "Author": AuthorResponse}
SEARCHABLE_FIELDS = {
    "Book": ["title", "genre", "author.name"],
    "Author": ["name", "email", "country"],
}
SORTABLE_FIELDS = {
    "Book": ["id", "title", "price", "pages", "published_year", "rating", "created_at"],
    "Author": ["id", "name", "email", "country", "birth_year", "created_at"],
}


def _get_executor(model_name: str, db: Session) -> GenericQueryExecutor:
    model_class = MODEL_REGISTRY.get(model_name)
    if not model_class:
        raise HTTPException(status_code=400, detail=f"Unknown model: {model_name}")
    return GenericQueryExecutor(
        model=model_class,
        db=db,
        sortable_fields=SORTABLE_FIELDS.get(model_name, []),
        searchable_fields=SEARCHABLE_FIELDS.get(model_name, []),
    )


# ──────────────────────────────────────────────────────────────────
# BOOKS (URL grammar — GET)
# ──────────────────────────────────────────────────────────────────

@router.get("/books", response_model=Dict[str, Any])
def list_books(
    request: Request,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query("created_at"),
    order: SortOrder = Query(SortOrder.ASC),
    search: Optional[str] = Query(None),
    url_filters: List[dict] = Depends(create_url_grammar_filter_dependency()),
    db: Session = Depends(get_db),
):
    pagination = GenericPaginationParams(page=page, size=size)
    sort_params = GenericSortParams(sort_by=sort_by, order=order)
    executor = _get_executor("Book", db)
    items, total = executor.execute(
        pagination=pagination, sort=sort_params, filters=url_filters, search=search,
    )
    return executor.create_paginated_response(
        items=items, total_count=total, pagination=pagination, response_model=BookWithAuthorResponse,
    )


# ──────────────────────────────────────────────────────────────────
# BOOKS (Tree filter — POST)
# ──────────────────────────────────────────────────────────────────

@router.post("/books/filter", response_model=Dict[str, Any])
def filter_books(
    filter_tree: FilterNode = Body(...),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query("created_at"),
    order: SortOrder = Query(SortOrder.ASC),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Filter books using a boolean expression tree (AND/OR with nested conditions)."""
    pagination = GenericPaginationParams(page=page, size=size)
    sort_params = GenericSortParams(sort_by=sort_by, order=order)
    executor = _get_executor("Book", db)
    items, total = executor.execute(
        pagination=pagination, sort=sort_params, filter_tree=filter_tree, search=search,
    )
    return executor.create_paginated_response(
        items=items, total_count=total, pagination=pagination, response_model=BookWithAuthorResponse,
    )


# ──────────────────────────────────────────────────────────────────
# AUTHORS (URL grammar — GET)
# ──────────────────────────────────────────────────────────────────

@router.get("/authors", response_model=Dict[str, Any])
def list_authors(
    request: Request,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query("created_at"),
    order: SortOrder = Query(SortOrder.ASC),
    search: Optional[str] = Query(None),
    url_filters: List[dict] = Depends(create_url_grammar_filter_dependency()),
    db: Session = Depends(get_db),
):
    pagination = GenericPaginationParams(page=page, size=size)
    sort_params = GenericSortParams(sort_by=sort_by, order=order)
    executor = _get_executor("Author", db)
    items, total = executor.execute(
        pagination=pagination, sort=sort_params, filters=url_filters, search=search,
    )
    return executor.create_paginated_response(
        items=items, total_count=total, pagination=pagination, response_model=AuthorResponse,
    )


# ──────────────────────────────────────────────────────────────────
# AUTHORS (Tree filter — POST)
# ──────────────────────────────────────────────────────────────────

@router.post("/authors/filter", response_model=Dict[str, Any])
def filter_authors(
    filter_tree: FilterNode = Body(...),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query("created_at"),
    order: SortOrder = Query(SortOrder.ASC),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Filter authors using a boolean expression tree."""
    pagination = GenericPaginationParams(page=page, size=size)
    sort_params = GenericSortParams(sort_by=sort_by, order=order)
    executor = _get_executor("Author", db)
    items, total = executor.execute(
        pagination=pagination, sort=sort_params, filter_tree=filter_tree, search=search,
    )
    return executor.create_paginated_response(
        items=items, total_count=total, pagination=pagination, response_model=AuthorResponse,
    )


# ──────────────────────────────────────────────────────────────────
# GROUP BY
# ──────────────────────────────────────────────────────────────────

@router.get("/books/group-by/{field}", response_model=List[Dict[str, Any]])
def group_books(field: str, search: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """Group books by a field and return counts."""
    executor = _get_executor("Book", db)
    return executor.execute_grouped(group_by=field, search=search)


@router.get("/authors/group-by/{field}", response_model=List[Dict[str, Any]])
def group_authors(field: str, search: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """Group authors by a field and return counts."""
    executor = _get_executor("Author", db)
    return executor.execute_grouped(group_by=field, search=search)


# ──────────────────────────────────────────────────────────────────
# METADATA (introspection)
# ──────────────────────────────────────────────────────────────────

@router.get("/books/metadata")
def books_metadata():
    return get_model_metadata(Book)


@router.get("/authors/metadata")
def authors_metadata():
    return get_model_metadata(Author)


# ──────────────────────────────────────────────────────────────────
# SAVED FILTERS
# ──────────────────────────────────────────────────────────────────

@router.get("/saved-filters", response_model=List[SavedFilterResponse])
def list_saved_filters(
    model_name: Optional[str] = None, db: Session = Depends(get_db),
):
    query = db.query(SavedFilter)
    if model_name:
        query = query.filter(SavedFilter.model_name == model_name)
    return query.order_by(SavedFilter.created_at.desc()).all()


@router.post(
    "/saved-filters",
    response_model=SavedFilterResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_saved_filter(data: SavedFilterCreate, db: Session = Depends(get_db)):
    sf = SavedFilter(
        name=data.name,
        description=data.description,
        model_name=data.model_name,
        filters=data.filters if data.filters else [],
        filter_tree=data.filter_tree.model_dump() if data.filter_tree else None,
        sort_by=data.sort_by,
        sort_order=data.sort_order,
        page_size=data.page_size,
        search_query=data.search_query,
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


@router.get("/saved-filters/{filter_id}/apply", response_model=Dict[str, Any])
def apply_saved_filter(
    filter_id: int,
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    sf = db.query(SavedFilter).filter(SavedFilter.id == filter_id).first()
    if not sf:
        raise HTTPException(status_code=404, detail="Saved filter not found")

    model_name = sf.model_name
    response_model = RESPONSE_MODEL_REGISTRY.get(model_name)
    if not response_model:
        raise HTTPException(status_code=400, detail=f"Unknown model: {model_name}")

    executor = _get_executor(model_name, db)
    pagination = GenericPaginationParams(page=page, size=sf.page_size or 20)
    sort_params = GenericSortParams(
        sort_by=sf.sort_by,
        order=SortOrder(sf.sort_order) if sf.sort_order else SortOrder.ASC,
    )

    # Reconstruct FilterNode tree from stored JSON
    filter_tree = None
    if sf.filters:
        filter_tree = FilterNode.model_validate(sf.filters)

    items, total = executor.execute(
        pagination=pagination, sort=sort_params, filter_tree=filter_tree, search=sf.search_query,
    )
    return executor.create_paginated_response(
        items=items, total_count=total, pagination=pagination, response_model=response_model,
    )
