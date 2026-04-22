
from typing import Any, Dict, List, Optional, Set, Tuple, Type

from sqlalchemy import String
from sqlalchemy import asc, cast, desc, func, or_
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session, Query
from pydantic import BaseModel

from app.enums.sort_order import SortOrder
from app.generics.filter_builder import QueryFilterBuilder
from app.generics.type_registry import (
    FIELD_TYPE_BOOLEAN,
    FIELD_TYPE_STRING,
    get_field_type,
)
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
        self._model_column_names: Set[str] = self._get_model_column_names()
        # sortable_fields restricts which columns the caller exposes for sorting.
        # When None, every model column is sortable.
        self.sortable_fields = sortable_fields
        self.searchable_fields = searchable_fields or []
        self.default_sort_field = default_sort_field
        self.default_sort_order = default_sort_order


    def execute(
        self,
        pagination: GenericPaginationParams,
        sort: Optional[GenericSortParams] = None,
        filter_tree: Optional[FilterNode] = None,
        filters: Optional[List[Dict[str, Any]]] = None,
        search: Optional[str] = None,
        group_by: Optional[str] = None,
    ) -> Tuple[List[Any], int]:
        query = self.db.query(self.model)
        builder = QueryFilterBuilder(query, self.model)

        if filter_tree:
            builder.apply_tree(filter_tree)

        if filters:
            builder.apply_filters_from_list(filters)

        query = builder.get_query()

        if search and self.searchable_fields:
            query = self._apply_search(query, search, builder)

        total_count = self._count_results(query)

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
        query = self.db.query(self.model)
        builder = QueryFilterBuilder(query, self.model)

        if filter_tree:
            builder.apply_tree(filter_tree)
        if filters:
            builder.apply_filters_from_list(filters)

        query = builder.get_query()

        if search and self.searchable_fields:
            query = self._apply_search(query, search, builder)

        try:
            column = builder._resolve_field(group_by)
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


    def _apply_search(
        self, query: Query, search: str, builder: QueryFilterBuilder
    ) -> Query:
        conditions: list = []
        search_lower = search.strip().lower()

        is_numeric = self._is_numeric(search)
        is_bool_term = search_lower in ("true", "false", "yes", "no", "1", "0")

        for field_name in self.searchable_fields:
            try:
                if "." in field_name:
                    col = builder._resolve_field(field_name)
                elif hasattr(self.model, field_name):
                    col = getattr(self.model, field_name)
                else:
                    continue

                col_type = self._get_column_type_str(col)

                if col_type == FIELD_TYPE_STRING:
                    conditions.append(cast(col, String).ilike(f"%{search}%"))
                elif col_type in ("integer", "float") and is_numeric:
                    conditions.append(cast(col, String).ilike(f"%{search}%"))
                elif col_type == FIELD_TYPE_BOOLEAN and is_bool_term:
                    bool_val = search_lower in ("true", "yes", "1")
                    conditions.append(col == bool_val)

            except (ValueError, AttributeError):
                continue

        if conditions:
            query = builder.get_query()
            query = query.filter(or_(*conditions))
            builder.query = query
        return query

    @staticmethod
    def _is_numeric(value: str) -> bool:
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _get_column_type_str(column) -> str:
        try:
            col_type = column.property.columns[0].type
            return get_field_type(col_type)
        except AttributeError:
            return FIELD_TYPE_STRING


    def _apply_sorting(self, query: Query, sort: Optional[GenericSortParams]) -> Query:
        sort_field = (sort.sort_by if sort and sort.sort_by else self.default_sort_field)
        sort_order = (sort.order if sort and sort.sort_by else self.default_sort_order)

        column, query = self._resolve_sort_column(sort_field, query)

        query = query.order_by(
            desc(column) if sort_order == SortOrder.DESC else asc(column)
        )
        return query

    def _resolve_sort_column(self, field: str, query: Query) -> Tuple[Any, Query]:
        """Resolve a sort field to its SQLAlchemy column, validated against the model mapper.

        Raises ValueError with a clear message if the field doesn't exist on the
        model or is not in the explicit sortable_fields restriction list.
        """
        # Relationship path (e.g. "author.name")
        if "." in field:
            builder = QueryFilterBuilder(query, self.model)
            try:
                column = builder._resolve_field(field)
                return column, builder.get_query()
            except ValueError:
                raise ValueError(
                    f"Invalid sort field '{field}': could not resolve "
                    f"relationship path on model '{self.model.__name__}'."
                )

        # Flat field — must be an actual database column on the model
        if field not in self._model_column_names:
            raise ValueError(
                f"Invalid sort field '{field}': not a column on model "
                f"'{self.model.__name__}'. "
                f"Available columns: {', '.join(sorted(self._model_column_names))}"
            )

        # If an explicit allowlist was provided, enforce it
        if self.sortable_fields is not None and field not in self.sortable_fields:
            raise ValueError(
                f"Sorting by '{field}' is not allowed. "
                f"Allowed sort fields: {', '.join(sorted(self.sortable_fields))}"
            )

        return getattr(self.model, field), query

    def _get_model_column_names(self) -> Set[str]:
        """Return the set of all database column attribute names from the model mapper."""
        mapper = getattr(self.model, "__mapper__", None)
        if not mapper:
            return set()
        return set(mapper.columns.keys())


    def _apply_pagination(self, query: Query, pagination: GenericPaginationParams) -> Query:
        skip = (pagination.page - 1) * pagination.size
        return query.offset(skip).limit(pagination.size)

    def _count_results(self, query: Query) -> int:
        """Count rows with deduplication when joins are present.

        For relationship joins, count(distinct(primary_key)) prevents inflated totals.
        """
        try:
            statement_sql = str(query.statement).upper()
            has_joins = " JOIN " in statement_sql
        except Exception:
            has_joins = False

        if not has_joins:
            return query.count()

        primary_keys = sa_inspect(self.model).primary_key
        if not primary_keys:
            return query.count()

        pk_col = primary_keys[0]
        count_query = query.order_by(None).with_entities(func.count(func.distinct(pk_col)))
        return int(count_query.scalar() or 0)


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
