"""
Model Introspection — examines any SQLAlchemy model and returns
field metadata (types, FK info, relationship cardinalities, permitted ops).

Used by the metadata endpoint so the frontend can auto-discover
which fields exist, what widget to render, and which operations are valid.
"""

from typing import Any, Dict, List, Optional, Type

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import RelationshipProperty

from app.generics.type_registry import get_field_type, get_permitted_operations


def get_model_metadata(model: Type[Any]) -> Dict[str, Any]:
    """
    Introspect a SQLAlchemy model and return a metadata dict with:
      - fields: list of field descriptors (name, type, ops, FK info)
      - relationships: list of relationship descriptors
    """
    mapper = sa_inspect(model)
    fields: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []

    # ── Columns ──────────────────────────────────────────────────
    for col in mapper.columns:
        field_type = get_field_type(col.type)
        permitted_ops = [op.value for op in get_permitted_operations(field_type)]

        field_meta: Dict[str, Any] = {
            "name": col.key,
            "type": field_type,
            "nullable": col.nullable,
            "ops": permitted_ops,
        }

        # FK detection
        if col.foreign_keys:
            fk = next(iter(col.foreign_keys))
            field_meta["is_fk"] = True
            field_meta["fk_target_table"] = fk.column.table.name
            field_meta["fk_target_column"] = fk.column.name
        else:
            field_meta["is_fk"] = False

        fields.append(field_meta)

    # ── Relationships ────────────────────────────────────────────
    for rel_prop in mapper.relationships:
        rel: RelationshipProperty = rel_prop
        related_model = rel.mapper.class_

        # Determine cardinality
        if rel.uselist:
            cardinality = "o2m"  # or m2m depending on secondary
            if rel.secondary is not None:
                cardinality = "m2m"
        else:
            cardinality = "m2o"

        relationships.append({
            "name": rel.key,
            "related_model": related_model.__name__,
            "related_table": related_model.__tablename__,
            "cardinality": cardinality,
        })

    return {
        "model": model.__name__,
        "table": model.__tablename__,
        "fields": fields,
        "relationships": relationships,
    }
