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
        query = self.db.query(self.model)
        
        if filters:
            if isinstance(filters, list):
                query = self._apply_list_filters(query, filters)
            elif isinstance(filters, dict):
                query = self._apply_dict_filters(query, filters)
        
        if filter_params:
            query = self._apply_param_filters(query, filter_params)
        
        if search and self.searchable_fields:
            query = self._apply_search(query, search)
        
        total_count = query.count()
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
        search_conditions = []
        for field_name in self.searchable_fields:
            if hasattr(self.model, field_name):
                column = getattr(self.model, field_name)
                search_conditions.append(cast(column, String).ilike(f"%{search}%"))
        if search_conditions:
            query = query.filter(or_(*search_conditions))
        return query
    
    def _apply_sorting(self, query: Query, sort: Optional[GenericSortParams]) -> Query:
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
            if hasattr(self.model, self.default_sort_field):
                column = getattr(self.model, self.default_sort_field)
                if self.default_sort_order == SortOrder.DESC:
                    query = query.order_by(desc(column))
                else:
                    query = query.order_by(asc(column))
        return query
    
    def _apply_pagination(self, query: Query, pagination: GenericPaginationParams) -> Query:
        skip = (pagination.page - 1) * pagination.size
        return query.offset(skip).limit(pagination.size)
    
    def create_paginated_response(
        self,
        items: List[Any],
        total_count: int,
        pagination: GenericPaginationParams,
        response_model: Type[BaseModel]
    ) -> Dict[str, Any]:
        total_pages = (total_count + pagination.size - 1) // pagination.size if total_count > 0 else 0
        has_next = pagination.page < total_pages
        has_previous = pagination.page > 1
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
