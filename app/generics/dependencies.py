from typing import Optional, List, Type, Any
from fastapi import Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import json
from fastapi import Request
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


URL_GRAMMAR_OPERATIONS = {
    "eq": "eq", "ne": "ne", "gt": "gt", "gte": "gte", "lt": "lt", "lte": "lte",
    "like": "like", "ilike": "ilike", "in": "in", "not_in": "not_in",
    "is_null": "is_null", "is_not_null": "is_not_null", "between": "between",
    "starts_with": "starts_with", "ends_with": "ends_with",
}


def parse_url_filter_param(key: str, value: str) -> Optional[dict]:
    sorted_ops = sorted(URL_GRAMMAR_OPERATIONS.keys(), key=len, reverse=True)
    for op_suffix in sorted_ops:
        suffix = f"_{op_suffix}"
        if key.endswith(suffix):
            field_name = key[:-len(suffix)]
            if field_name:
                parsed_value = _parse_filter_value(value, op_suffix)
                return {"field": field_name, "operation": op_suffix, "value": parsed_value}
    return {"field": key, "operation": "eq", "value": _parse_filter_value(value, "eq")}


def _parse_filter_value(value: str, operation: str):
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
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    if value.lower() == 'null':
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def create_url_grammar_filter_dependency(
    reserved_keys: Optional[List[str]] = None,
    max_filters: int = 50
):
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
