
from typing import Any, Dict, List, Optional, Type

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import RelationshipProperty

from app.generics.type_registry import get_field_type, get_permitted_operations


def _get_display_fields(model: Type[Any]) -> List[Dict[str, Any]]:
    mapper = sa_inspect(model)
    result: List[Dict[str, Any]] = []
    for col in mapper.columns:
        if col.primary_key:
            continue
        if col.foreign_keys:
            continue
        field_type = get_field_type(col.type)
        result.append({
            "name": col.key,
            "type": field_type,
            "ops": [op.value for op in get_permitted_operations(field_type)],
        })
    return result


def get_model_metadata(model: Type[Any]) -> Dict[str, Any]:
    mapper = sa_inspect(model)
    fields: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []

    for col in mapper.columns:
        field_type = get_field_type(col.type)
        permitted_ops = [op.value for op in get_permitted_operations(field_type)]

        field_meta: Dict[str, Any] = {
            "name": col.key,
            "type": field_type,
            "nullable": col.nullable,
            "ops": permitted_ops,
        }

        if col.foreign_keys:
            fk = next(iter(col.foreign_keys))
            field_meta["is_fk"] = True
            field_meta["fk_target_table"] = fk.column.table.name
            field_meta["fk_target_column"] = fk.column.name
        else:
            field_meta["is_fk"] = False

        fields.append(field_meta)

    for rel_prop in mapper.relationships:
        rel: RelationshipProperty = rel_prop
        related_model = rel.mapper.class_

        if rel.uselist:
            cardinality = "o2m"
            if rel.secondary is not None:
                cardinality = "m2m"
        else:
            cardinality = "m2o"

        related_fields = _get_display_fields(related_model)
        display_field = "name"
        string_fields = [f for f in related_fields if f["type"] == "string"]
        if string_fields:
            if not any(f["name"] == "name" for f in string_fields):
                display_field = string_fields[0]["name"]

        relationships.append({
            "name": rel.key,
            "related_model": related_model.__name__,
            "related_table": related_model.__tablename__,
            "cardinality": cardinality,
            "display_field": display_field,
            "related_fields": related_fields,
        })

    return {
        "model": model.__name__,
        "table": model.__tablename__,
        "fields": fields,
        "relationships": relationships,
    }
