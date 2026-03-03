"""
GenericQueryExecutor — orchestrates filtering, sorting, pagination, search, and grouping
for any SQLAlchemy model.
"""

from typing import Any, Dict, List, Optional, Tuple, Type

from sqlalchemy import String, asc, cast, desc, func, or_
from sqlalchemy.orm import Session, Query
from pydantic import BaseModel

from app.enums.sort_order import SortOrder
from app.generics.filter_builder import QueryFilterBuilder
from app.schema.filter_node import FilterNode
from app.schema.pagination import GenericPaginationParams, PaginatedResponseMetadata
from app.schema.sorting import GenericSortParams


class GenericQueryExecutor:
    def __init__(
        self,
        model: Type[Any],
        db: Session,
        sortable_fields: Optional[List[str]] = None,
        searchable_fields: Optional[List[str]] = None,
        default_sort_field: str = "created_at",
        default_sort_order: SortOrder = SortOrder.ASC,
    ):
        self.model = model
        self.db = db
        self.sortable_fields = sortable_fields or []
        self.searchable_fields = searchable_fields or []
        self.default_sort_field = default_sort_field
        self.default_sort_order = default_sort_order

    # ──────────────────────────────────────────────────────────────
    # Main execute
    # ──────────────────────────────────────────────────────────────

    def execute(
        self,
        pagination: GenericPaginationParams,
        sort: Optional[GenericSortParams] = None,
        filter_tree: Optional[FilterNode] = None,
        filters: Optional[List[Dict[str, Any]]] = None,
        search: Optional[str] = None,
        group_by: Optional[str] = None,
    ) -> Tuple[List[Any], int]:
        """
        Execute the query with all parameters applied.

        Args:
            filter_tree: Boolean expression tree (new primary API).
            filters: Flat list of filter dicts (URL grammar fallback).
            group_by: Field name to group results by (server-side GROUP BY).
        """
        query = self.db.query(self.model)
        builder = QueryFilterBuilder(query, self.model)

        # Apply tree-based filters
        if filter_tree:
            builder.apply_tree(filter_tree)

        # Apply flat list filters (URL grammar compatibility)
        if filters:
            builder.apply_filters_from_list(filters)

        query = builder.get_query()

        # Apply search
        if search and self.searchable_fields:
            query = self._apply_search(query, search, builder)

        # Get total count before pagination
        total_count = query.count()

        # Apply sorting and pagination
        query = self._apply_sorting(query, sort)
        query = self._apply_pagination(query, pagination)

        items = query.all()
        return items, total_count

    def execute_grouped(
        self,
        group_by: str,
        filter_tree: Optional[FilterNode] = None,
        filters: Optional[List[Dict[str, Any]]] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a grouped query with server-side GROUP BY.
        Returns: [{"key": <value>, "count": <int>}, ...]
        """
        query = self.db.query(self.model)
        builder = QueryFilterBuilder(query, self.model)

        if filter_tree:
            builder.apply_tree(filter_tree)
        if filters:
            builder.apply_filters_from_list(filters)

        query = builder.get_query()

        if search and self.searchable_fields:
            query = self._apply_search(query, search, builder)

        # Resolve group_by column, allowing dot-notation for relationships
        try:
            column = builder._resolve_field(group_by)
            # Make sure we update the query after resolve_field might have added joins
            query = builder.get_query()
        except ValueError:
            raise ValueError(f"Cannot group by field '{group_by}'.")

        rows = (
            query
            .with_entities(column, func.count().label("count"))
            .group_by(column)
            .order_by(func.count().desc())
            .all()
        )
        return [{"key": row[0], "count": row[1]} for row in rows]

    # ──────────────────────────────────────────────────────────────
    # Search
    # ──────────────────────────────────────────────────────────────

    def _apply_search(
        self, query: Query, search: str, builder: QueryFilterBuilder
    ) -> Query:
        """Search across searchable fields, including relationship fields."""
        conditions = []
        for field_name in self.searchable_fields:
            if "." in field_name:
                # Relationship field — resolve via builder to get JOINs
                col = builder._resolve_field(field_name)
                conditions.append(cast(col, String).ilike(f"%{search}%"))
            elif hasattr(self.model, field_name):
                col = getattr(self.model, field_name)
                conditions.append(cast(col, String).ilike(f"%{search}%"))
        if conditions:
            query = builder.get_query()
            query = query.filter(or_(*conditions))
            builder.query = query
        return query

    # ──────────────────────────────────────────────────────────────
    # Sorting
    # ──────────────────────────────────────────────────────────────

    def _apply_sorting(self, query: Query, sort: Optional[GenericSortParams]) -> Query:
        sort_field = (sort.sort_by if sort and sort.sort_by else self.default_sort_field)
        sort_order = (sort.order if sort and sort.sort_by else self.default_sort_order)

        if self.sortable_fields and sort_field not in self.sortable_fields:
            raise ValueError(f"Invalid sort field '{sort_field}'.")

        column = self._resolve_sort_field(sort_field, query)
        if column is not None:
            query = query[0] if isinstance(query, tuple) else query # Handle if _resolve_sort_field returns new query
            query = query.order_by(desc(column) if sort_order == SortOrder.DESC else asc(column))
        return query

    def _resolve_sort_field(self, field: str, query: Query = None):
        """Resolve a field name to a column. For relationships in sorting, we'd need joins usually."""
        if hasattr(self.model, field):
            return getattr(self.model, field)
        return None

    # ──────────────────────────────────────────────────────────────
    # Pagination
    # ──────────────────────────────────────────────────────────────

    def _apply_pagination(self, query: Query, pagination: GenericPaginationParams) -> Query:
        skip = (pagination.page - 1) * pagination.size
        return query.offset(skip).limit(pagination.size)

    # ──────────────────────────────────────────────────────────────
    # Response builder
    # ──────────────────────────────────────────────────────────────

    def create_paginated_response(
        self,
        items: List[Any],
        total_count: int,
        pagination: GenericPaginationParams,
        response_model: Type[BaseModel],
    ) -> Dict[str, Any]:
        total_pages = (
            (total_count + pagination.size - 1) // pagination.size
            if total_count > 0
            else 0
        )
        data = [response_model.model_validate(item) for item in items]
        metadata = PaginatedResponseMetadata(
            page=pagination.page,
            size=pagination.size,
            total_items=total_count,
            total_pages=total_pages,
        )
        return {"data": data, "meta": metadata}
