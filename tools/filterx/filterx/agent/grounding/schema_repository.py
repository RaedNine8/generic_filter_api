from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


class SchemaRepository:
    def __init__(self, scan_file: Path, entities: Iterable[dict[str, Any]] | None = None) -> None:
        self.scan_file = scan_file
        self._seed_entities = list(entities) if entities is not None else None
        self._entities: list[dict[str, Any]] | None = None
        self._registry: dict[str, dict[str, Any]] = {}

    def reload(self) -> None:
        self._entities = None
        self._registry = {}
        self._ensure_loaded()

    def list_entities(self) -> list[dict[str, Any]]:
        self._ensure_loaded()
        return list(self._entities or [])

    def get_entity(self, name: str) -> dict[str, Any] | None:
        self._ensure_loaded()
        return self._registry.get(self._normalize_key(name))

    def get_field(self, entity_name: str, field_path: str) -> dict[str, Any] | None:
        entity = self.get_entity(entity_name)
        if entity is None:
            return None
        parts = field_path.split(".")
        if len(parts) == 1:
            return self._find_field(entity.get("fields", []), parts[0])
        relationship = next((rel for rel in entity.get("relationships", []) if rel.get("name") == parts[0]), None)
        if relationship is None:
            return None
        return self._find_field(relationship.get("related_fields", []), parts[-1])

    def allowed_ops(self, entity_name: str, field_path: str) -> list[str]:
        field = self.get_field(entity_name, field_path)
        return list(field.get("ops", [])) if field else []

    def _ensure_loaded(self) -> None:
        if self._entities is not None:
            return
        if self._seed_entities is not None:
            entities = self._merge_seed_entities(self._seed_entities)
        else:
            payload = json.loads(self.scan_file.read_text(encoding="utf-8"))
            entities = list(payload.get("entities", []))
        self._entities = entities
        self._registry = {}
        for entity in entities:
            for key in self._entity_keys(entity):
                self._registry[key] = entity

    @staticmethod
    def _find_field(fields: Iterable[dict[str, Any]], name: str) -> dict[str, Any] | None:
        return next((field for field in fields if field.get("name") == name), None)

    def _merge_seed_entities(self, seed_entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not self.scan_file.exists():
            return seed_entities
        payload = json.loads(self.scan_file.read_text(encoding="utf-8"))
        scan_entities = list(payload.get("entities", []))
        scan_by_key: dict[str, dict[str, Any]] = {}
        for entity in scan_entities:
            for key in self._entity_keys(entity):
                scan_by_key[key] = entity
        merged: list[dict[str, Any]] = []
        for entity in seed_entities:
            scan_entity = next((scan_by_key.get(key) for key in self._entity_keys(entity) if scan_by_key.get(key)), None)
            merged.append({**(scan_entity or {}), **entity, "module": entity.get("module") or (scan_entity or {}).get("module")})
        return merged

    @classmethod
    def _entity_keys(cls, entity: dict[str, Any]) -> set[str]:
        model = str(entity.get("model") or "")
        table = str(entity.get("table") or "")
        values = {model, table, cls._singularize(model), cls._singularize(table)}
        return {cls._normalize_key(value) for value in values if value}

    @staticmethod
    def _singularize(value: str) -> str:
        lowered = value.strip().lower().replace("-", "_")
        if lowered.endswith("ies") and len(lowered) > 3:
            return lowered[:-3] + "y"
        if lowered.endswith("s") and len(lowered) > 1:
            return lowered[:-1]
        return lowered

    @staticmethod
    def _normalize_key(value: str) -> str:
        return value.strip().lower().replace("-", "_")
