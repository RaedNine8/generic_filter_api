from __future__ import annotations

import importlib
import pkgutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

from .io import utc_now_iso


@dataclass
class ScanResult:
    scan: Dict[str, Any]
    diagnostics: Dict[str, Any]
    plan: Dict[str, Any]


def _import_object(import_path: str) -> Any:
    module_name, obj_name = import_path.split(":", 1)
    module = importlib.import_module(module_name)
    return getattr(module, obj_name)


def _purge_module_cache(prefixes: Iterable[str]) -> None:
    normalized = {p for p in prefixes if p}
    for module_name in list(sys.modules.keys()):
        for prefix in normalized:
            if module_name == prefix or module_name.startswith(prefix + "."):
                sys.modules.pop(module_name, None)
                break


def _normalize_sqlalchemy_type(type_obj: Any) -> str:
    tname = type(type_obj).__name__.lower()
    if "integer" in tname:
        return "integer"
    if "float" in tname or "numeric" in tname or "decimal" in tname:
        return "float"
    if "boolean" in tname or tname == "bool":
        return "boolean"
    if "datetime" in tname:
        return "datetime"
    if tname == "date":
        return "date"
    if "enum" in tname:
        return "enum"
    if "json" in tname:
        return "json"
    if "text" in tname:
        return "text"
    if "char" in tname or "string" in tname:
        return "string"
    return tname


def _ops_for_type(type_name: str) -> List[str]:
    if type_name in {"integer", "float"}:
        return ["eq", "ne", "gt", "gte", "lt", "lte", "in", "not_in", "between", "is_null", "is_not_null"]
    if type_name in {"boolean"}:
        return ["eq", "ne", "is_null", "is_not_null"]
    if type_name in {"date", "datetime"}:
        return ["eq", "ne", "gt", "gte", "lt", "lte", "between", "is_null", "is_not_null"]
    if type_name in {"json"}:
        return ["is_null", "is_not_null", "eq", "ne"]
    return ["eq", "ne", "like", "ilike", "starts_with", "ends_with", "in", "not_in", "is_null", "is_not_null"]


def _walk_and_import_package(package_name: str) -> None:
    package = importlib.import_module(package_name)
    if not hasattr(package, "__path__"):
        return
    for info in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        importlib.import_module(info.name)


def _cardinality_of(relationship: Any) -> str:
    direction = getattr(relationship.direction, "name", "")
    if direction == "MANYTOONE":
        return "m2o"
    if direction == "ONETOMANY":
        return "o2m"
    if direction == "MANYTOMANY":
        return "m2m"
    return "unknown"


def _build_entity(cls: Any) -> Dict[str, Any]:
    mapper = cls.__mapper__
    table = cls.__table__

    columns: List[Dict[str, Any]] = []
    primary_keys: List[str] = []

    for col in table.columns:
        normalized_type = _normalize_sqlalchemy_type(col.type)
        fk_targets = [str(fk.target_fullname) for fk in col.foreign_keys]

        if col.primary_key:
            primary_keys.append(col.name)

        columns.append(
            {
                "name": col.name,
                "type": normalized_type,
                "nullable": bool(col.nullable),
                "primary_key": bool(col.primary_key),
                "unique": bool(col.unique),
                "is_fk": bool(col.foreign_keys),
                "fk_targets": fk_targets,
                "ops": _ops_for_type(normalized_type),
            }
        )

    relationships: List[Dict[str, Any]] = []
    for rel in mapper.relationships:
        related_cls = rel.mapper.class_
        related_fields: List[Dict[str, Any]] = []
        for rcol in related_cls.__table__.columns:
            ntype = _normalize_sqlalchemy_type(rcol.type)
            related_fields.append(
                {
                    "name": rcol.name,
                    "type": ntype,
                    "ops": _ops_for_type(ntype),
                }
            )

        display_field = "name" if any(f["name"] == "name" for f in related_fields) else related_fields[0]["name"]

        relationships.append(
            {
                "name": rel.key,
                "related_model": related_cls.__name__,
                "related_table": related_cls.__table__.name,
                "cardinality": _cardinality_of(rel),
                "uselist": bool(rel.uselist),
                "display_field": display_field,
                "related_fields": related_fields,
                "back_populates": rel.back_populates,
            }
        )

    return {
        "model": cls.__name__,
        "module": cls.__module__,
        "table": table.name,
        "primary_keys": primary_keys,
        "fields": columns,
        "relationships": relationships,
    }


def _detect_cycles(graph: Dict[str, Set[str]]) -> List[List[str]]:
    cycles: List[List[str]] = []
    visiting: Set[str] = set()
    visited: Set[str] = set()

    def dfs(node: str, stack: List[str]) -> None:
        visiting.add(node)
        stack.append(node)
        for nxt in graph.get(node, set()):
            if nxt not in graph:
                continue
            if nxt in visiting:
                idx = stack.index(nxt)
                cycle = stack[idx:] + [nxt]
                if cycle not in cycles:
                    cycles.append(cycle)
                continue
            if nxt not in visited:
                dfs(nxt, stack)
        visiting.remove(node)
        visited.add(node)
        stack.pop()

    for node in graph:
        if node not in visited:
            dfs(node, [])
    return cycles


def _max_graph_depth(graph: Dict[str, Set[str]]) -> int:
    best = 0

    def dfs(node: str, seen: Set[str], depth: int) -> None:
        nonlocal best
        best = max(best, depth)
        for nxt in graph.get(node, set()):
            if nxt in seen:
                continue
            dfs(nxt, seen | {nxt}, depth + 1)

    for node in graph:
        dfs(node, {node}, 0)
    return best


def _scan_routes(app_obj: Any) -> List[Dict[str, Any]]:
    routes_out: List[Dict[str, Any]] = []
    routes = getattr(app_obj, "routes", [])
    for route in routes:
        methods = sorted(list(getattr(route, "methods", []) or []))
        if "HEAD" in methods:
            methods.remove("HEAD")
        routes_out.append(
            {
                "path": getattr(route, "path", ""),
                "name": getattr(route, "name", ""),
                "methods": methods,
                "type": type(route).__name__,
            }
        )
    return routes_out


def run_scan(config: Dict[str, Any], project_root: Path) -> ScanResult:
    diagnostics: Dict[str, List[Dict[str, Any]]] = {
        "errors": [],
        "warnings": [],
        "info": [],
    }

    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    py_cfg = config["python"]
    backend_cfg = config["backend"]
    scan_cfg = config["scan"]
    frontend_cfg = config["frontend"]

    app_module_name = py_cfg["app_import"].split(":", 1)[0]
    base_module_name = py_cfg["base_class_import"].split(":", 1)[0]
    model_package_name = py_cfg["models_package"]
    root_packages = {
        app_module_name.split(".", 1)[0],
        base_module_name.split(".", 1)[0],
        model_package_name.split(".", 1)[0],
    }
    _purge_module_cache([model_package_name, app_module_name, base_module_name, *sorted(root_packages)])

    try:
        _walk_and_import_package(py_cfg["models_package"])
    except Exception as exc:  # pragma: no cover
        diagnostics["errors"].append(
            {
                "code": "MODELS_IMPORT_FAILED",
                "message": f"Could not import models package '{py_cfg['models_package']}'.",
                "context": {"error": str(exc)},
            }
        )

    entities: List[Dict[str, Any]] = []
    route_scan: List[Dict[str, Any]] = []

    try:
        base_cls = _import_object(py_cfg["base_class_import"])
        mapper_classes = sorted(
            [m.class_ for m in base_cls.registry.mappers],
            key=lambda c: c.__name__,
        )

        allow_entities = set(backend_cfg.get("entities") or [])
        deny_entities = set(backend_cfg.get("exclude_entities") or [])

        for cls in mapper_classes:
            model_name = cls.__name__
            if allow_entities and model_name not in allow_entities:
                continue
            if model_name in deny_entities:
                continue
            entities.append(_build_entity(cls))

        if not entities:
            diagnostics["warnings"].append(
                {
                    "code": "NO_ENTITIES_SELECTED",
                    "message": "No entities were selected from SQLAlchemy models.",
                    "context": {},
                }
            )

    except Exception as exc:  # pragma: no cover
        diagnostics["errors"].append(
            {
                "code": "BASE_IMPORT_OR_MAPPING_FAILED",
                "message": "Could not load Base registry and mapped model classes.",
                "context": {"error": str(exc)},
            }
        )

    try:
        app_obj = _import_object(py_cfg["app_import"])
        route_scan = _scan_routes(app_obj)
    except Exception as exc:  # pragma: no cover
        diagnostics["warnings"].append(
            {
                "code": "APP_IMPORT_FAILED",
                "message": f"Could not import app from '{py_cfg['app_import']}' for route scan.",
                "context": {"error": str(exc)},
            }
        )

    graph: Dict[str, Set[str]] = {}
    for ent in entities:
        graph[ent["model"]] = {rel["related_model"] for rel in ent["relationships"]}

    cycles = _detect_cycles(graph)
    if cycles:
        diagnostics["warnings"].append(
            {
                "code": "RELATIONSHIP_CYCLES_DETECTED",
                "message": "Relationship cycles were detected in model graph.",
                "context": {"cycles": cycles},
            }
        )

    max_graph_depth = _max_graph_depth(graph) if graph else 0
    configured_max_depth = int(scan_cfg["max_relationship_depth"])
    if max_graph_depth > configured_max_depth:
        diagnostics["warnings"].append(
            {
                "code": "GRAPH_DEPTH_EXCEEDS_CONFIG",
                "message": "Discovered relationship graph depth exceeds configured max traversal depth.",
                "context": {
                    "discovered_depth": max_graph_depth,
                    "configured_depth": configured_max_depth,
                },
            }
        )

    for ent in entities:
        if len(ent["primary_keys"]) > 1:
            diagnostics["warnings"].append(
                {
                    "code": "COMPOSITE_PRIMARY_KEY",
                    "message": f"Entity '{ent['model']}' uses composite primary key.",
                    "context": {"primary_keys": ent["primary_keys"]},
                }
            )
        if ent["primary_keys"] and ent["primary_keys"] != ["id"]:
            diagnostics["info"].append(
                {
                    "code": "NON_STANDARD_PRIMARY_KEY",
                    "message": f"Entity '{ent['model']}' primary key is not the conventional ['id'].",
                    "context": {"primary_keys": ent["primary_keys"]},
                }
            )

    frontend_files = {
        "routes_file": str((project_root / frontend_cfg["routes_file"]).resolve()),
        "app_config_file": str((project_root / frontend_cfg["app_config_file"]).resolve()),
    }
    for key, raw_path in frontend_files.items():
        if not Path(raw_path).exists():
            diagnostics["warnings"].append(
                {
                    "code": "FRONTEND_FILE_NOT_FOUND",
                    "message": f"Frontend target file '{key}' not found.",
                    "context": {"path": raw_path},
                }
            )

    scan_payload: Dict[str, Any] = {
        "generated_at": utc_now_iso(),
        "project": {
            "name": config["project"]["name"],
            "root": str(project_root.resolve()),
        },
        "config_summary": {
            "backend_enabled": backend_cfg["enabled"],
            "frontend_enabled": frontend_cfg["enabled"],
            "database_enabled": config["database"]["enabled"],
            "api_prefix": backend_cfg["api_prefix"],
        },
        "entities": entities,
        "relationship_graph": {k: sorted(list(v)) for k, v in graph.items()},
        "graph_stats": {
            "entity_count": len(entities),
            "relationship_cycle_count": len(cycles),
            "max_depth": max_graph_depth,
        },
        "routes": route_scan,
    }

    plan_payload: Dict[str, Any] = {
        "generated_at": utc_now_iso(),
        "phases": [
            {"name": "scan", "enabled": True},
            {"name": "backend.install", "enabled": bool(backend_cfg["enabled"])},
            {"name": "frontend.install", "enabled": bool(frontend_cfg["enabled"])},
            {"name": "db.install", "enabled": bool(config["database"]["enabled"])},
            {"name": "validate", "enabled": True},
        ],
        "actions": [
            "Generate backend integration modules" if backend_cfg["enabled"] else "Skip backend integration",
            "Generate frontend integration modules" if frontend_cfg["enabled"] else "Skip frontend integration",
            "Generate database migrations" if config["database"]["enabled"] else "Skip database migrations",
        ],
        "entity_targets": [ent["model"] for ent in entities],
    }

    return ScanResult(scan=scan_payload, diagnostics=diagnostics, plan=plan_payload)
