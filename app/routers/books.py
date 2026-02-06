from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query, Request, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.book import Book
from app.models.author import Author
from app.models.saved_filter import SavedFilter
from app.schema.book import BookResponse, BookWithAuthorResponse
from app.schema.author import AuthorResponse
from app.schema.saved_filter import SavedFilterCreate, SavedFilterResponse
from app.schema.pagination import GenericPaginationParams
from app.schema.sorting import GenericSortParams
from app.enums.sort_order import SortOrder
from app.generics.query_executor import GenericQueryExecutor
from app.generics.dependencies import create_url_grammar_filter_dependency

router = APIRouter(prefix="/api", tags=["API"])

MODEL_REGISTRY = {"Book": Book, "Author": Author}


@router.get("/books", response_model=Dict[str, Any])
def list_books(
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
        model=Book, db=db,
        sortable_fields=["id", "title", "price", "pages", "published_year", "rating", "created_at"],
        searchable_fields=["title", "description", "genre", "isbn"],
        default_sort_field="id", default_sort_order=SortOrder.DESC
    )
    items, total = executor.execute(pagination=pagination, sort=sort_params, filters=url_filters, search=search)
    return executor.create_paginated_response(items=items, total_count=total, pagination=pagination, response_model=BookWithAuthorResponse)


@router.get("/authors", response_model=Dict[str, Any])
def list_authors(
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
        model=Author, db=db,
        sortable_fields=["id", "name", "email", "country", "birth_year", "created_at"],
        searchable_fields=["name", "email", "country"],
        default_sort_field="id", default_sort_order=SortOrder.DESC
    )
    items, total = executor.execute(pagination=pagination, sort=sort_params, filters=url_filters, search=search)
    return executor.create_paginated_response(items=items, total_count=total, pagination=pagination, response_model=AuthorResponse)


# ============ SAVED FILTERS ============

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


@router.get("/saved-filters/{filter_id}/apply", response_model=Dict[str, Any])
def apply_saved_filter(
    filter_id: int,
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db)
):
    sf = db.query(SavedFilter).filter(SavedFilter.id == filter_id).first()
    if not sf:
        raise HTTPException(status_code=404, detail="Saved filter not found")
    
    model_class = MODEL_REGISTRY.get(sf.model_name)
    if not model_class:
        raise HTTPException(status_code=400, detail=f"Unknown model: {sf.model_name}")
    
    response_model = BookWithAuthorResponse if sf.model_name == "Book" else AuthorResponse
    searchable = ["title", "description", "genre", "isbn"] if sf.model_name == "Book" else ["name", "email", "country"]
    
    pagination = GenericPaginationParams(page=page, size=sf.page_size or 10)
    sort_params = GenericSortParams(sort_by=sf.sort_by, order=SortOrder(sf.sort_order) if sf.sort_order else SortOrder.DESC)
    
    executor = GenericQueryExecutor(model=model_class, db=db, searchable_fields=searchable)
    items, total = executor.execute(pagination=pagination, sort=sort_params, filters=sf.filters, search=sf.search_query)
    return executor.create_paginated_response(items=items, total_count=total, pagination=pagination, response_model=response_model)
