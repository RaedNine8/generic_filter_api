from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from filterx.core.config import load_effective_config
from filterx.core.conflicts import check_route_path_conflicts
from filterx.core.io import load_json
from filterx.core.patcher import PatchOp, apply_patch_operations

from ._stub import run_stub


def _resolve_dry_run(args: Any, cfg: dict[str, Any]) -> bool:
    dry_run = getattr(args, "dry_run", None)
    if dry_run is None:
        return bool(cfg["safety"].get("dry_run_default", True))
    return bool(dry_run)


def _csv_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _filter_entities(scan_entities: list[dict[str, Any]], cfg: dict[str, Any], args: Any) -> list[dict[str, Any]]:
    allow = set(_csv_list(getattr(args, "entities", None)) or (cfg["backend"].get("entities") or []))
    deny = set(cfg["backend"].get("exclude_entities") or [])

    selected: list[dict[str, Any]] = []
    for entity in scan_entities:
        model = entity.get("model")
        if allow and model not in allow:
            continue
        if model in deny:
            continue
        selected.append(entity)
    return selected


def _py_module_path(path_like: str) -> str:
    return Path(path_like).as_posix().strip("/").replace("/", ".")


def _to_filterx_base_path(api_prefix: str) -> str:
    prefix = api_prefix.strip() or "/api"
    if not prefix.startswith("/"):
        prefix = f"/{prefix}"
    if prefix != "/":
        prefix = prefix.rstrip("/")
    else:
        prefix = ""
    return f"{prefix}/filterx"


def _render_entities_py(entities: list[dict[str, Any]]) -> str:
    compact_entities: list[dict[str, Any]] = []
    for entity in entities:
        compact_entities.append(
            {
                "model": entity.get("model"),
                "module": entity.get("module"),
                "table": entity.get("table"),
                "primary_keys": entity.get("primary_keys", []),
                "fields": [
                    {
                        "name": field.get("name"),
                        "type": field.get("type"),
                        "nullable": field.get("nullable"),
                        "primary_key": field.get("primary_key", False),
                        "is_fk": field.get("is_fk", False),
                        "fk_targets": field.get("fk_targets", []),
                        "ops": field.get("ops", []),
                    }
                    for field in entity.get("fields", [])
                ],
                "relationships": [
                    {
                        "name": rel.get("name"),
                        "related_model": rel.get("related_model"),
                        "related_table": rel.get("related_table"),
                        "cardinality": rel.get("cardinality"),
                        "uselist": rel.get("uselist"),
                        "display_field": rel.get("display_field"),
                        "related_fields": rel.get("related_fields", []),
                    }
                    for rel in entity.get("relationships", [])
                ],
            }
        )

    payload = json.dumps(compact_entities, indent=2)
    return (
        "from __future__ import annotations\n\n"
        "import json\n\n"
        f"_ENTITIES_JSON = '''{payload}'''\n"
        "ENTITIES = json.loads(_ENTITIES_JSON)\n"
    )


def _render_metadata_py() -> str:
    return (
        "from __future__ import annotations\n\n"
        "from .entities import ENTITIES\n\n"
        "\n"
        "def build_metadata() -> dict[str, object]:\n"
        "    return {\n"
        "        \"entities\": ENTITIES,\n"
        "        \"entity_count\": len(ENTITIES),\n"
        "    }\n"
    )


def _render_router_factory_py() -> str:
    return r'''from __future__ import annotations

import importlib
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Iterable, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from sqlalchemy import String, asc, cast, desc, func, inspect as sa_inspect, or_
from sqlalchemy.orm import aliased

from .metadata import build_metadata


VALID_OPS = {
    "eq", "ne", "gt", "gte", "lt", "lte",
    "like", "ilike", "starts_with", "ends_with",
    "in", "not_in", "is_null", "is_not_null", "between",
}
RESERVED_QUERY_KEYS = {
    "page", "size", "page_size", "sort_by", "order", "sort_order",
    "search", "filter_id",
}
MAX_FILTER_TREE_DEPTH = 20


def _import_object(import_path: str) -> Any:
    module_name, obj_name = import_path.split(":", 1)
    module = importlib.import_module(module_name)
    return getattr(module, obj_name)


def _normalize_prefix(api_prefix: str) -> str:
    prefix = api_prefix.strip() or "/api"
    if not prefix.startswith("/"):
        prefix = f"/{prefix}"
    if prefix != "/":
        prefix = prefix.rstrip("/")
    else:
        prefix = ""
    return prefix


def _singularize(value: str) -> str:
    lowered = value.strip().lower().replace("-", "_")
    if lowered.endswith("ies") and len(lowered) > 3:
        return lowered[:-3] + "y"
    if lowered.endswith("s") and len(lowered) > 1:
        return lowered[:-1]
    return lowered


def _entity_keys(entity: dict[str, Any]) -> set[str]:
    model = str(entity.get("model") or "")
    table = str(entity.get("table") or "")
    keys = {
        model.lower(),
        table.lower(),
        model.lower().replace("_", "-"),
        table.lower().replace("_", "-"),
        _singularize(model),
        _singularize(table),
        _singularize(model).replace("_", "-"),
        _singularize(table).replace("_", "-"),
    }
    return {key for key in keys if key}


def _build_registry(entities: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for entity in entities:
        for key in _entity_keys(entity):
            registry[key] = entity
    return registry


def _get_entity(registry: dict[str, dict[str, Any]], raw_name: str) -> dict[str, Any]:
    key = raw_name.strip().lower().replace("-", "_")
    entity = registry.get(key) or registry.get(raw_name.strip().lower())
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Unknown FilterX entity: {raw_name}")
    return entity


def _model_for_entity(entity: dict[str, Any]) -> type[Any]:
    module_name = entity.get("module")
    model_name = entity.get("model")
    if not module_name or not model_name:
        raise HTTPException(status_code=500, detail=f"Entity metadata for {model_name!r} is missing module/model.")
    module = importlib.import_module(str(module_name))
    return getattr(module, str(model_name))


def _parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null":
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def _parse_value(value: str, operation: str) -> Any:
    if operation in {"in", "not_in"}:
        return [_parse_scalar(item.strip()) for item in value.split(",") if item.strip()]
    if operation == "between":
        parts = [item.strip() for item in value.split(",")]
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Operation 'between' requires two comma-separated values.")
        return [_parse_scalar(parts[0]), _parse_scalar(parts[1])]
    return _parse_scalar(value)


def _parse_filter_param(key: str, value: str) -> Optional[dict[str, Any]]:
    for op in sorted(VALID_OPS, key=len, reverse=True):
        suffix = f"_{op}"
        if key.endswith(suffix):
            field = key[:-len(suffix)]
            if not field:
                return None
            return {"field": field, "operation": op, "value": _parse_value(value, op)}
    return {"field": key, "operation": "eq", "value": _parse_value(value, "eq")}


def _parse_url_filters(request: Request) -> list[dict[str, Any]]:
    filters: list[dict[str, Any]] = []
    for key, value in request.query_params.items():
        if key in RESERVED_QUERY_KEYS or value == "":
            continue
        parsed = _parse_filter_param(key, value)
        if parsed:
            filters.append(parsed)
    return filters


def _coerce_body_filters(body: Any) -> tuple[Optional[dict[str, Any]], list[dict[str, Any]]]:
    if body is None:
        return None, []
    if isinstance(body, list):
        return None, [item for item in body if isinstance(item, dict)]
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Filter body must be an object or a list of filter objects.")
    if body.get("node_type"):
        return body, []
    tree = body.get("filter_tree") if isinstance(body.get("filter_tree"), dict) else None
    filters = body.get("filters") if isinstance(body.get("filters"), list) else []
    return tree, [item for item in filters if isinstance(item, dict)]


def _field_type(entity: dict[str, Any], field_name: str) -> str:
    flat = field_name.split(".")[-1]
    for field in entity.get("fields", []):
        if field.get("name") == flat:
            return str(field.get("type") or "string")
    return "string"


def _resolve_field(query: Any, root_model: type[Any], field_path: str, operation: Optional[str] = None) -> tuple[Any, Any, bool]:
    parts = field_path.split(".")
    if not parts or any(not part for part in parts):
        raise HTTPException(status_code=400, detail=f"Invalid field path: {field_path}")

    current = root_model
    joined = False
    use_outer = operation in {"is_null", "is_not_null"}

    for rel_name in parts[:-1]:
        if not hasattr(current, rel_name):
            current_name = getattr(current, "__name__", str(current))
            raise HTTPException(status_code=400, detail=f"Model '{current_name}' has no relationship '{rel_name}'.")
        rel_attr = getattr(current, rel_name)
        if not hasattr(rel_attr, "property") or not hasattr(rel_attr.property, "mapper"):
            current_name = getattr(current, "__name__", str(current))
            raise HTTPException(status_code=400, detail=f"Attribute '{rel_name}' on '{current_name}' is not a relationship.")
        related_alias = aliased(rel_attr.property.mapper.class_)
        query = query.outerjoin(related_alias, rel_attr) if use_outer else query.join(related_alias, rel_attr)
        current = related_alias
        joined = True

    col_name = parts[-1]
    if not hasattr(current, col_name):
        current_name = getattr(current, "__name__", str(current))
        raise HTTPException(status_code=400, detail=f"Model '{current_name}' has no field '{col_name}'.")
    return getattr(current, col_name), query, joined


def _filter_expression(column: Any, operation: str, value: Any) -> Any:
    if operation == "eq":
        return column == value
    if operation == "ne":
        return column != value
    if operation == "gt":
        return column > value
    if operation == "gte":
        return column >= value
    if operation == "lt":
        return column < value
    if operation == "lte":
        return column <= value
    if operation == "like":
        return column.like(f"%{value}%")
    if operation == "ilike":
        return column.ilike(f"%{value}%")
    if operation == "starts_with":
        return column.like(f"{value}%")
    if operation == "ends_with":
        return column.like(f"%{value}")
    if operation == "in":
        if not isinstance(value, list) or not value:
            raise HTTPException(status_code=400, detail="Operation 'in' requires a non-empty list value.")
        return column.in_(value)
    if operation == "not_in":
        if not isinstance(value, list) or not value:
            raise HTTPException(status_code=400, detail="Operation 'not_in' requires a non-empty list value.")
        return ~column.in_(value)
    if operation == "is_null":
        return column.is_(None)
    if operation == "is_not_null":
        return column.is_not(None)
    if operation == "between":
        if not isinstance(value, list) or len(value) != 2:
            raise HTTPException(status_code=400, detail="Operation 'between' requires exactly two values.")
        return column.between(value[0], value[1])
    raise HTTPException(status_code=400, detail=f"Unsupported filter operation: {operation}")


def _apply_filter(query: Any, model: type[Any], filter_rule: dict[str, Any]) -> tuple[Any, bool]:
    field = filter_rule.get("field")
    operation = filter_rule.get("operation", "eq")
    value = filter_rule.get("value")
    if not field or operation not in VALID_OPS:
        raise HTTPException(status_code=400, detail=f"Invalid filter rule: {filter_rule}")
    if operation not in {"is_null", "is_not_null"} and value in (None, "", []):
        return query, False
    column, query, joined = _resolve_field(query, model, str(field), str(operation))
    return query.filter(_filter_expression(column, str(operation), value)), joined


def _evaluate_tree(query: Any, model: type[Any], node: dict[str, Any], depth: int = 0) -> tuple[Any, Any, bool]:
    if depth > MAX_FILTER_TREE_DEPTH:
        raise HTTPException(status_code=400, detail=f"Filter tree exceeds maximum depth of {MAX_FILTER_TREE_DEPTH}.")
    node_type = node.get("node_type")
    if node_type == "condition":
        field = node.get("field")
        operation = node.get("operation")
        value = node.get("value")
        if not field or not operation:
            raise HTTPException(status_code=400, detail="Condition nodes require 'field' and 'operation'.")
        if operation not in {"is_null", "is_not_null"} and value in (None, "", []):
            return query, None, False
        column, query, joined = _resolve_field(query, model, str(field), str(operation))
        return query, _filter_expression(column, str(operation), value), joined

    if node_type != "operator":
        raise HTTPException(status_code=400, detail="Filter node_type must be 'operator' or 'condition'.")

    operator = node.get("operator")
    children = node.get("children") or []
    if operator not in {"AND", "OR"} or not children:
        raise HTTPException(status_code=400, detail="Operator nodes require operator AND/OR and at least one child.")

    clauses = []
    any_joined = False
    for child in children:
        if not isinstance(child, dict):
            continue
        query, clause, joined = _evaluate_tree(query, model, child, depth + 1)
        any_joined = any_joined or joined
        if clause is not None:
            clauses.append(clause)

    if not clauses:
        return query, None, any_joined
    if len(clauses) == 1:
        return query, clauses[0], any_joined
    from sqlalchemy import and_, or_
    return query, (and_(*clauses) if operator == "AND" else or_(*clauses)), any_joined


def _apply_tree(query: Any, model: type[Any], tree: Optional[dict[str, Any]]) -> tuple[Any, bool]:
    if not tree:
        return query, False
    query, clause, joined = _evaluate_tree(query, model, tree)
    if clause is not None:
        query = query.filter(clause)
    return query, joined


def _searchable_fields(entity: dict[str, Any]) -> list[str]:
    return [
        str(field.get("name"))
        for field in entity.get("fields", [])
        if str(field.get("type")) in {"string", "text", "enum"}
    ]


def _apply_search(query: Any, model: type[Any], entity: dict[str, Any], search: Optional[str]) -> Any:
    if not search:
        return query
    clauses = []
    for field in _searchable_fields(entity):
        column, query, _ = _resolve_field(query, model, field)
        clauses.append(cast(column, String).ilike(f"%{search}%"))
    if clauses:
        query = query.filter(or_(*clauses))
    return query


def _default_sort_field(entity: dict[str, Any]) -> str:
    primary_keys = entity.get("primary_keys") or []
    if primary_keys:
        return str(primary_keys[0])
    fields = entity.get("fields") or []
    return str(fields[0].get("name") if fields else "id")


def _apply_sort(query: Any, model: type[Any], entity: dict[str, Any], sort_by: Optional[str], order: str) -> Any:
    sort_field = sort_by or _default_sort_field(entity)
    column, query, _ = _resolve_field(query, model, sort_field)
    direction = desc if str(order).lower() == "desc" else asc
    return query.order_by(direction(column))


def _count_query(query: Any, model: type[Any]) -> int:
    primary_keys = sa_inspect(model).primary_key
    if primary_keys:
        return int(query.order_by(None).with_entities(func.count(func.distinct(primary_keys[0]))).scalar() or 0)
    return int(query.count() or 0)


def _json_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _serialize_shallow(obj: Any) -> dict[str, Any]:
    mapper = sa_inspect(obj.__class__)
    return {column.key: _json_value(getattr(obj, column.key)) for column in mapper.columns}


def _serialize_row(obj: Any, entity: dict[str, Any]) -> dict[str, Any]:
    out = _serialize_shallow(obj)
    for rel in entity.get("relationships", []):
        if rel.get("uselist") or rel.get("cardinality") in {"o2m", "m2m"}:
            continue
        name = rel.get("name")
        if not name:
            continue
        try:
            related = getattr(obj, str(name))
        except Exception:
            continue
        out[str(name)] = None if related is None else _serialize_shallow(related)
    return out


def _page_meta(page: int, size: int, total: int) -> dict[str, int]:
    return {
        "page": page,
        "size": size,
        "total_items": total,
        "total_pages": ((total + size - 1) // size) if total else 0,
    }


def _run_query(
    db: Any,
    entity: dict[str, Any],
    model: type[Any],
    *,
    page: int,
    size: int,
    sort_by: Optional[str],
    order: str,
    search: Optional[str],
    filters: list[dict[str, Any]],
    filter_tree: Optional[dict[str, Any]],
) -> dict[str, Any]:
    query = db.query(model)
    for filter_rule in filters:
        query, _ = _apply_filter(query, model, filter_rule)
    query, _ = _apply_tree(query, model, filter_tree)
    query = _apply_search(query, model, entity, search)
    total = _count_query(query, model)
    query = _apply_sort(query, model, entity, sort_by, order)
    rows = query.offset((page - 1) * size).limit(size).all()
    return {
        "data": [_serialize_row(row, entity) for row in rows],
        "meta": _page_meta(page, size, total),
    }


def _run_group_by(
    db: Any,
    entity: dict[str, Any],
    model: type[Any],
    *,
    field: str,
    search: Optional[str],
    filters: list[dict[str, Any]],
    filter_tree: Optional[dict[str, Any]],
) -> list[dict[str, Any]]:
    query = db.query(model)
    for filter_rule in filters:
        query, _ = _apply_filter(query, model, filter_rule)
    query, _ = _apply_tree(query, model, filter_tree)
    query = _apply_search(query, model, entity, search)
    column, query, _ = _resolve_field(query, model, field)
    rows = query.with_entities(column, func.count().label("count")).group_by(column).order_by(func.count().desc()).all()
    return [{"key": _json_value(row[0]), "count": row[1]} for row in rows]


def create_router(
    api_prefix: str = "/api",
    entities: Optional[list[dict[str, Any]]] = None,
    session_dependency_import: str = "app.database:get_db",
) -> APIRouter:
    prefix = _normalize_prefix(api_prefix)
    entity_list = entities or []
    registry = _build_registry(entity_list)
    get_db = _import_object(session_dependency_import)

    router = APIRouter(prefix=f"{prefix}/filterx", tags=["filterx"])

    @router.get("/metadata")
    def get_metadata() -> dict[str, object]:
        return build_metadata()

    @router.get("/{entity}/query")
    def query_entity(
        entity: str,
        request: Request,
        page: int = Query(1, ge=1),
        size: int = Query(20, ge=1, le=100),
        sort_by: Optional[str] = Query(None),
        order: str = Query("asc", pattern="^(asc|desc)$"),
        search: Optional[str] = Query(None),
        db: Any = Depends(get_db),
    ) -> dict[str, Any]:
        entity_meta = _get_entity(registry, entity)
        model = _model_for_entity(entity_meta)
        filters = _parse_url_filters(request)
        return _run_query(
            db,
            entity_meta,
            model,
            page=page,
            size=size,
            sort_by=sort_by,
            order=order,
            search=search,
            filters=filters,
            filter_tree=None,
        )

    @router.post("/{entity}/filter")
    def filter_entity(
        entity: str,
        body: Any = Body(default=None),
        page: int = Query(1, ge=1),
        size: int = Query(20, ge=1, le=100),
        sort_by: Optional[str] = Query(None),
        order: str = Query("asc", pattern="^(asc|desc)$"),
        search: Optional[str] = Query(None),
        db: Any = Depends(get_db),
    ) -> dict[str, Any]:
        entity_meta = _get_entity(registry, entity)
        model = _model_for_entity(entity_meta)
        tree, filters = _coerce_body_filters(body)
        return _run_query(
            db,
            entity_meta,
            model,
            page=page,
            size=size,
            sort_by=sort_by,
            order=order,
            search=search,
            filters=filters,
            filter_tree=tree,
        )

    @router.get("/{entity}/group-by/{field:path}")
    def group_entity(
        entity: str,
        field: str,
        request: Request,
        search: Optional[str] = Query(None),
        db: Any = Depends(get_db),
    ) -> list[dict[str, Any]]:
        entity_meta = _get_entity(registry, entity)
        model = _model_for_entity(entity_meta)
        filters = _parse_url_filters(request)
        return _run_group_by(db, entity_meta, model, field=field, search=search, filters=filters, filter_tree=None)

    @router.post("/{entity}/group-by/{field:path}/filter")
    def group_entity_with_filter(
        entity: str,
        field: str,
        body: Any = Body(default=None),
        search: Optional[str] = Query(None),
        db: Any = Depends(get_db),
    ) -> list[dict[str, Any]]:
        entity_meta = _get_entity(registry, entity)
        model = _model_for_entity(entity_meta)
        tree, filters = _coerce_body_filters(body)
        return _run_group_by(db, entity_meta, model, field=field, search=search, filters=filters, filter_tree=tree)

    return router
'''


def _render_router_py(api_prefix: str, session_dependency_import: str) -> str:
    escaped = api_prefix.replace("\\", "\\\\").replace('"', '\\"')
    escaped_session = session_dependency_import.replace("\\", "\\\\").replace('"', '\\"')
    return (
        "from __future__ import annotations\n\n"
        "from .entities import ENTITIES\n"
        "from .router_factory import create_router\n\n"
        f"API_PREFIX = \"{escaped}\"\n"
        f"SESSION_DEPENDENCY_IMPORT = \"{escaped_session}\"\n"
        "router = create_router(\n"
        "    api_prefix=API_PREFIX,\n"
        "    entities=ENTITIES,\n"
        "    session_dependency_import=SESSION_DEPENDENCY_IMPORT,\n"
        ")\n"
    )


def _render_predicates_py() -> str:
    return (
        "from __future__ import annotations\n\n"
        "from typing import Callable, Iterable\n\n"
        "\n"
        "PredicateHook = Callable[[str, object], object]\n"
        "\n"
        "\n"
        "def register_global_predicates(hooks: Iterable[PredicateHook]) -> list[PredicateHook]:\n"
        "    return [hook for hook in hooks]\n"
    )


def _render_init_py() -> str:
    return (
        "from .router import router\n\n"
        "__all__ = [\"router\"]\n"
    )


def _build_patch_ops(
    generated_root: str,
    entities: list[dict[str, Any]],
    api_prefix: str,
    session_dependency_import: str,
    mount_file: str,
    mount_anchor: str,
    generated_module: str,
    include_mount: bool,
) -> list[PatchOp]:
    root = Path(generated_root).as_posix().rstrip("/")

    ops = [
        PatchOp(
            kind="generated_file",
            path=f"{root}/__init__.py",
            content=_render_init_py(),
            description="FilterX backend package exports",
        ),
        PatchOp(
            kind="generated_file",
            path=f"{root}/entities.py",
            content=_render_entities_py(entities),
            description="FilterX scanned entity registry",
        ),
        PatchOp(
            kind="generated_file",
            path=f"{root}/metadata.py",
            content=_render_metadata_py(),
            description="FilterX metadata builder",
        ),
        PatchOp(
            kind="generated_file",
            path=f"{root}/router_factory.py",
            content=_render_router_factory_py(),
            description="FilterX router factory",
        ),
        PatchOp(
            kind="generated_file",
            path=f"{root}/router.py",
            content=_render_router_py(api_prefix, session_dependency_import),
            description="FilterX mountable router",
        ),
        PatchOp(
            kind="generated_file",
            path=f"{root}/predicates.py",
            content=_render_predicates_py(),
            description="FilterX global predicate hooks",
        ),
    ]

    if include_mount:
        snippet = (
            f"from {generated_module}.router import router as filterx_generated_router\n"
            "app.include_router(filterx_generated_router)"
        )
        ops.append(
            PatchOp(
                kind="anchor_insert",
                path=mount_file,
                anchor=mount_anchor,
                snippet=snippet,
                insert_mode="after",
                owner="host",
                description="Mount generated FilterX router",
            )
        )

    return ops


def _detect_generation_conflicts(
    project_root: Path,
    operations: list[PatchOp],
    allow_overwrite_generated: bool,
) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    for op in operations:
        if op.kind != "generated_file":
            continue
        target = project_root / op.path
        if target.exists():
            existing = target.read_text(encoding="utf-8")
            if existing != op.content and not allow_overwrite_generated:
                conflicts.append(
                    {
                        "code": "GENERATED_FILE_HASH_MISMATCH",
                        "path": op.path,
                        "message": "Existing generated file differs and overwrite is disabled.",
                    }
                )
    return conflicts


def _backend_validate_payload(
    project_root: Path,
    cfg: dict[str, Any],
    generated_module: str,
) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    root = Path(cfg["backend"]["generated_package"]).as_posix().rstrip("/")
    required = [
        f"{root}/__init__.py",
        f"{root}/entities.py",
        f"{root}/metadata.py",
        f"{root}/router_factory.py",
        f"{root}/router.py",
        f"{root}/predicates.py",
    ]
    for rel in required:
        if not (project_root / rel).exists():
            errors.append({"code": "BACKEND_GENERATED_FILE_MISSING", "path": str(project_root / rel)})

    mount_file = project_root / cfg["backend"]["mount_file"]
    mount_anchor = cfg["backend"]["mount_anchor"]
    mount_snippet = f"from {generated_module}.router import router as filterx_generated_router"

    if not mount_file.exists():
        errors.append({"code": "BACKEND_MOUNT_FILE_MISSING", "path": str(mount_file)})
    else:
        content = mount_file.read_text(encoding="utf-8")
        if mount_anchor not in content:
            warnings.append(
                {
                    "code": "BACKEND_MOUNT_ANCHOR_NOT_FOUND",
                    "path": str(mount_file),
                    "anchor": mount_anchor,
                }
            )
        if mount_snippet not in content:
            warnings.append(
                {
                    "code": "BACKEND_MOUNT_SNIPPET_NOT_FOUND",
                    "path": str(mount_file),
                    "snippet": mount_snippet,
                }
            )

    return {
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings),
    }


def run_install(args: Any) -> int:
    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config).resolve() if args.config else None
    effective = load_effective_config(project_root, config_path)
    cfg = effective.raw

    if not cfg["backend"].get("enabled", True):
        if args.json:
            print(json.dumps({"skipped": True, "reason": "backend disabled in config"}, indent=2))
        else:
            print("FilterX backend install skipped: backend.enabled is false.")
        return 0

    dry_run = _resolve_dry_run(args, cfg)
    check_mode = bool(getattr(args, "check", False))
    strict_conflict_mode = bool(cfg["safety"].get("strict_conflict_mode", True))

    scan_path = project_root / cfg["output"]["scan_file"]
    if not scan_path.exists():
        payload = {
            "errors": [
                {
                    "code": "SCAN_FILE_MISSING",
                    "path": str(scan_path),
                    "message": "Run 'filterx scan' before backend install.",
                }
            ]
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print("FilterX backend install failed: scan artifact is missing.")
            print(f"- Expected scan file: {scan_path}")
        return 2

    scan_payload = load_json(scan_path)
    scan_entities = list(scan_payload.get("entities", []))
    selected_entities = _filter_entities(scan_entities, cfg, args)

    api_prefix = str(getattr(args, "api_prefix", None) or cfg["backend"].get("api_prefix", "/api"))
    mount_file = str(getattr(args, "mount_file", None) or cfg["backend"]["mount_file"])
    mount_anchor = str(getattr(args, "mount_anchor", None) or cfg["backend"]["mount_anchor"])
    include_mount = not bool(getattr(args, "no_mount", False))

    generated_root = str(cfg["backend"]["generated_package"])
    generated_module = _py_module_path(generated_root)

    operations = _build_patch_ops(
        generated_root=generated_root,
        entities=selected_entities,
        api_prefix=api_prefix,
        session_dependency_import=str(cfg["python"]["session_dependency_import"]),
        mount_file=mount_file,
        mount_anchor=mount_anchor,
        generated_module=generated_module,
        include_mount=include_mount,
    )

    existing_routes = list(scan_payload.get("routes", []))
    filterx_base_path = _to_filterx_base_path(api_prefix)
    candidate_paths = [
        f"{filterx_base_path}/metadata",
        f"{filterx_base_path}/{{entity}}/query",
        f"{filterx_base_path}/{{entity}}/filter",
        f"{filterx_base_path}/{{entity}}/group-by/{{field:path}}",
        f"{filterx_base_path}/{{entity}}/group-by/{{field:path}}/filter",
    ]
    route_conflicts = check_route_path_conflicts(existing_routes, candidate_paths)
    conflict_payload = [
        {
            "code": conflict.code,
            "message": conflict.message,
            "context": conflict.context,
        }
        for conflict in route_conflicts.conflicts
    ]

    allow_overwrite_generated = bool(cfg["safety"].get("allow_overwrite_generated", True)) or bool(
        getattr(args, "force", False)
    )
    generation_conflicts = _detect_generation_conflicts(
        project_root=project_root,
        operations=operations,
        allow_overwrite_generated=allow_overwrite_generated,
    )

    all_conflicts = conflict_payload + generation_conflicts
    if strict_conflict_mode and all_conflicts:
        payload = {
            "dry_run": dry_run or check_mode,
            "strict_conflict_mode": strict_conflict_mode,
            "conflicts": all_conflicts,
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print("FilterX backend install blocked by safety conflicts.")
            for conflict in all_conflicts:
                print(f"- {conflict['code']}: {conflict['message']}")
        return 3

    manifest_path = project_root / cfg["safety"]["idempotency_manifest"]
    patch_dir = project_root / cfg["output"]["patch_dir"]

    result = apply_patch_operations(
        project_root=project_root,
        operations=operations,
        manifest_path=manifest_path,
        patch_dir=patch_dir,
        dry_run=dry_run,
        check_mode=check_mode,
        strict_conflict_mode=strict_conflict_mode,
        description="backend.install",
    )

    payload = {
        "dry_run": result.dry_run,
        "check_mode": check_mode,
        "patch_id": result.patch_id,
        "generated_root": str((project_root / generated_root).resolve()),
        "selected_entities": [entity.get("model") for entity in selected_entities],
        "touched_files": result.touched_files,
        "applied_ops": result.applied_ops,
        "skipped_ops": result.skipped_ops,
        "issues": [
            {
                "code": issue.code,
                "message": issue.message,
                "context": issue.context,
            }
            for issue in result.issues
        ],
        "conflicts": all_conflicts,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("FilterX backend install completed.")
        print(f"- Dry run: {payload['dry_run']}")
        print(f"- Check mode: {payload['check_mode']}")
        print(f"- Patch ID: {payload['patch_id']}")
        print(f"- Applied ops: {payload['applied_ops']}")
        print(f"- Skipped ops: {payload['skipped_ops']}")
        print(f"- Touched files: {len(payload['touched_files'])}")

    if result.has_conflicts:
        return 3
    if getattr(args, "fail_on_warning", False) and result.issues:
        return 3
    return 0


def run_validate(args: Any) -> int:
    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config).resolve() if args.config else None
    effective = load_effective_config(project_root, config_path)
    cfg = effective.raw

    generated_module = _py_module_path(cfg["backend"]["generated_package"])
    payload = _backend_validate_payload(project_root=project_root, cfg=cfg, generated_module=generated_module)

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("FilterX backend validation completed.")
        print(f"- Errors: {payload['error_count']}")
        print(f"- Warnings: {payload['warning_count']}")

    if payload["errors"]:
        return 4
    if getattr(args, "fail_on_warning", False) and payload["warnings"]:
        return 3
    return 0


def run_remove(args: Any) -> int:
    return run_stub(args, "backend remove")
