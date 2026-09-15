from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping, Sequence

IR_VERSION = "filterx-ir/v1"


class FieldType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    ENUM = "enum"
    UUID = "uuid"
    JSON_BLOB = "json/blob"
    BINARY = "binary"


class RelationshipKind(str, Enum):
    ONE_TO_ONE = "one-to-one"
    ONE_TO_MANY = "one-to-many"
    MANY_TO_ONE = "many-to-one"
    MANY_TO_MANY = "many-to-many"


class Visibility(str, Enum):
    PUBLIC = "public"
    HOOK = "hook"


@dataclass(frozen=True)
class FieldIR:
    name: str
    type: FieldType
    source_type: str
    nullable: bool
    primary_key: bool
    unique: bool
    has_default: bool
    foreign_keys: tuple[str, ...] = ()
    operations: tuple[str, ...] = ()
    enum_values: tuple[str, ...] = ()
    visibility: Visibility = Visibility.PUBLIC
    permission: str | None = None


@dataclass(frozen=True)
class RelationshipIR:
    name: str
    kind: RelationshipKind
    target_entity: str
    target_table: str
    join_path: tuple[str, ...]
    depth: int
    collection: bool
    back_populates: str | None = None
    cycle: bool = False


@dataclass(frozen=True)
class SoftDeleteIR:
    respected: bool
    field: str | None = None


@dataclass(frozen=True)
class EntityIdentityIR:
    module: str
    table: str
    primary_keys: tuple[str, ...]


@dataclass(frozen=True)
class EntityIR:
    name: str
    identity: EntityIdentityIR
    fields: tuple[FieldIR, ...]
    relationships: tuple[RelationshipIR, ...]
    cycle_memberships: tuple[tuple[str, ...], ...] = ()
    soft_delete: SoftDeleteIR = field(default_factory=lambda: SoftDeleteIR(respected=False))


@dataclass(frozen=True)
class SecurityHooksIR:
    identity: str | None = None
    row_predicates: tuple[str, ...] = ()
    entity_row_predicates: tuple[tuple[str, tuple[str, ...]], ...] = ()
    field_visibility: str | None = None


@dataclass(frozen=True)
class RouteIR:
    path: str
    name: str
    methods: tuple[str, ...]
    source_type: str


@dataclass(frozen=True)
class FilterxIR:
    version: str
    source_framework: str
    entities: tuple[EntityIR, ...]
    routes: tuple[RouteIR, ...] = ()
    security: SecurityHooksIR = field(default_factory=SecurityHooksIR)
    max_relationship_depth: int = 0

    def to_dict(self) -> dict[str, Any]:
        return _json_value(asdict(self))


class IRValidationError(ValueError):
    def __init__(self, errors: Sequence[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("Invalid FilterX IR: " + "; ".join(self.errors))


def ir_from_dict(payload: Mapping[str, Any]) -> FilterxIR:
    try:
        entities = tuple(
            EntityIR(
                name=str(entity["name"]),
                identity=EntityIdentityIR(
                    module=str(entity["identity"]["module"]),
                    table=str(entity["identity"]["table"]),
                    primary_keys=tuple(str(item) for item in entity["identity"]["primary_keys"]),
                ),
                fields=tuple(
                    FieldIR(
                        name=str(item["name"]),
                        type=FieldType(item["type"]),
                        source_type=str(item["source_type"]),
                        nullable=bool(item["nullable"]),
                        primary_key=bool(item["primary_key"]),
                        unique=bool(item["unique"]),
                        has_default=bool(item["has_default"]),
                        foreign_keys=tuple(str(value) for value in item.get("foreign_keys", [])),
                        operations=tuple(str(value) for value in item.get("operations", [])),
                        enum_values=tuple(str(value) for value in item.get("enum_values", [])),
                        visibility=Visibility(item.get("visibility", Visibility.PUBLIC.value)),
                        permission=item.get("permission"),
                    )
                    for item in entity["fields"]
                ),
                relationships=tuple(
                    RelationshipIR(
                        name=str(item["name"]),
                        kind=RelationshipKind(item["kind"]),
                        target_entity=str(item["target_entity"]),
                        target_table=str(item["target_table"]),
                        join_path=tuple(str(value) for value in item["join_path"]),
                        depth=int(item["depth"]),
                        collection=bool(item["collection"]),
                        back_populates=item.get("back_populates"),
                        cycle=bool(item.get("cycle", False)),
                    )
                    for item in entity["relationships"]
                ),
                cycle_memberships=tuple(
                    tuple(str(value) for value in cycle) for cycle in entity.get("cycle_memberships", [])
                ),
                soft_delete=SoftDeleteIR(
                    respected=bool(entity.get("soft_delete", {}).get("respected", False)),
                    field=entity.get("soft_delete", {}).get("field"),
                ),
            )
            for entity in payload["entities"]
        )
        security_payload = payload.get("security", {})
        ir = FilterxIR(
            version=str(payload["version"]),
            source_framework=str(payload["source_framework"]),
            entities=entities,
            routes=tuple(
                RouteIR(
                    path=str(route["path"]),
                    name=str(route["name"]),
                    methods=tuple(str(method) for method in route["methods"]),
                    source_type=str(route["source_type"]),
                )
                for route in payload.get("routes", [])
            ),
            security=SecurityHooksIR(
                identity=security_payload.get("identity"),
                row_predicates=tuple(str(item) for item in security_payload.get("row_predicates", [])),
                entity_row_predicates=tuple(
                    (str(item[0]), tuple(str(path) for path in item[1]))
                    for item in security_payload.get("entity_row_predicates", [])
                ),
                field_visibility=security_payload.get("field_visibility"),
            ),
            max_relationship_depth=int(payload.get("max_relationship_depth", 0)),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise IRValidationError([str(exc)]) from exc
    validate_ir(ir)
    return ir


def _json_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    return value


def _field_type(source_type: str) -> FieldType:
    normalized = source_type.lower()
    if normalized == "integer":
        return FieldType.INTEGER
    if normalized in {"float", "numeric", "decimal"}:
        return FieldType.DECIMAL
    if normalized == "boolean":
        return FieldType.BOOLEAN
    if normalized == "date":
        return FieldType.DATE
    if normalized == "datetime":
        return FieldType.DATETIME
    if normalized == "enum":
        return FieldType.ENUM
    if "uuid" in normalized:
        return FieldType.UUID
    if normalized in {"json", "jsonb", "blob"}:
        return FieldType.JSON_BLOB
    if normalized in {"binary", "largebinary", "bytes"}:
        return FieldType.BINARY
    return FieldType.STRING


def _relationship_kind(cardinality: str, collection: bool) -> RelationshipKind:
    if cardinality == "o2m":
        return RelationshipKind.ONE_TO_MANY
    if cardinality == "m2o":
        return RelationshipKind.MANY_TO_ONE
    if cardinality == "m2m":
        return RelationshipKind.MANY_TO_MANY
    if not collection:
        return RelationshipKind.ONE_TO_ONE
    return RelationshipKind.ONE_TO_MANY


def _normalized_cycles(cycles: Iterable[Sequence[str]]) -> tuple[tuple[str, ...], ...]:
    return tuple(sorted((tuple(str(node) for node in cycle) for cycle in cycles), key=lambda item: item))


def from_legacy_scan(
    scan: Mapping[str, Any],
    config: Mapping[str, Any],
    *,
    column_details: Mapping[tuple[str, str], Mapping[str, Any]] | None = None,
) -> FilterxIR:
    details = column_details or {}
    graph = {str(name): tuple(str(target) for target in targets) for name, targets in scan.get("relationship_graph", {}).items()}
    cycles = _normalized_cycles(_cycles_for_graph(graph))
    respect_soft_delete = bool(config.get("scan", {}).get("respect_soft_delete", False))
    entities: list[EntityIR] = []

    for legacy_entity in sorted(scan.get("entities", []), key=lambda item: str(item.get("model", ""))):
        entity_name = str(legacy_entity["model"])
        fields: list[FieldIR] = []
        field_names: set[str] = set()
        for legacy_field in legacy_entity.get("fields", []):
            name = str(legacy_field["name"])
            field_names.add(name)
            detail = details.get((entity_name, name), {})
            fields.append(
                FieldIR(
                    name=name,
                    type=_field_type(str(legacy_field.get("type", "string"))),
                    source_type=str(legacy_field.get("type", "string")),
                    nullable=bool(legacy_field.get("nullable", True)),
                    primary_key=bool(legacy_field.get("primary_key", False)),
                    unique=bool(legacy_field.get("unique", False)),
                    has_default=bool(detail.get("has_default", False)),
                    foreign_keys=tuple(sorted(str(item) for item in legacy_field.get("fk_targets", []))),
                    operations=tuple(str(item) for item in legacy_field.get("ops", [])),
                    enum_values=tuple(str(item) for item in legacy_field.get("enum_values", [])),
                )
            )

        memberships = tuple(cycle for cycle in cycles if entity_name in cycle)
        relationships: list[RelationshipIR] = []
        for relationship in sorted(legacy_entity.get("relationships", []), key=lambda item: str(item.get("name", ""))):
            target = str(relationship["related_model"])
            relationships.append(
                RelationshipIR(
                    name=str(relationship["name"]),
                    kind=_relationship_kind(
                        str(relationship.get("cardinality", "unknown")),
                        bool(relationship.get("uselist", False)),
                    ),
                    target_entity=target,
                    target_table=str(relationship.get("related_table", "")),
                    join_path=(str(relationship["name"]),),
                    depth=1,
                    collection=bool(relationship.get("uselist", False)),
                    back_populates=(
                        str(relationship["back_populates"])
                        if relationship.get("back_populates") is not None
                        else None
                    ),
                    cycle=any(entity_name in cycle and target in cycle for cycle in cycles),
                )
            )

        soft_delete_field = next(
            (candidate for candidate in ("deleted_at", "is_deleted", "deleted") if candidate in field_names),
            None,
        )
        entities.append(
            EntityIR(
                name=entity_name,
                identity=EntityIdentityIR(
                    module=str(legacy_entity.get("module", "")),
                    table=str(legacy_entity.get("table", "")),
                    primary_keys=tuple(str(item) for item in legacy_entity.get("primary_keys", [])),
                ),
                fields=tuple(fields),
                relationships=tuple(relationships),
                cycle_memberships=memberships,
                soft_delete=SoftDeleteIR(
                    respected=respect_soft_delete and soft_delete_field is not None,
                    field=soft_delete_field,
                ),
            )
        )

    backend = config.get("backend", {})
    entity_predicates = tuple(
        (str(name), tuple(str(path) for path in paths))
        for name, paths in sorted((backend.get("entity_predicate_hooks") or {}).items())
    )
    routes = tuple(
        RouteIR(
            path=str(route.get("path", "")),
            name=str(route.get("name", "")),
            methods=tuple(sorted(str(method) for method in route.get("methods", []))),
            source_type=str(route.get("type", "")),
        )
        for route in sorted(scan.get("routes", []), key=lambda item: (str(item.get("path", "")), str(item.get("name", ""))))
    )
    ir = FilterxIR(
        version=IR_VERSION,
        source_framework="sqlalchemy",
        entities=tuple(entities),
        routes=routes,
        security=SecurityHooksIR(
            identity=backend.get("auth_dependency_import"),
            row_predicates=tuple(str(path) for path in backend.get("global_predicate_hooks") or []),
            entity_row_predicates=entity_predicates,
            field_visibility=backend.get("field_visibility_hook_import"),
        ),
        max_relationship_depth=int(scan.get("graph_stats", {}).get("max_depth", 0)),
    )
    validate_ir(ir)
    return ir


def _cycles_for_graph(graph: Mapping[str, Sequence[str]]) -> list[list[str]]:
    cycles: list[list[str]] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, stack: list[str]) -> None:
        visiting.add(node)
        stack.append(node)
        for target in sorted(graph.get(node, ())):
            if target not in graph:
                continue
            if target in visiting:
                cycle = stack[stack.index(target) :] + [target]
                if cycle not in cycles:
                    cycles.append(cycle)
            elif target not in visited:
                visit(target, stack)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in sorted(graph):
        if node not in visited:
            visit(node, [])
    return cycles


def validate_ir(ir: FilterxIR) -> None:
    errors: list[str] = []
    if ir.version != IR_VERSION:
        errors.append(f"unsupported version '{ir.version}'")
    names = [entity.name for entity in ir.entities]
    if names != sorted(names):
        errors.append("entities must be ordered by name")
    if len(names) != len(set(names)):
        errors.append("entity names must be unique")
    for entity in ir.entities:
        field_names = [item.name for item in entity.fields]
        if len(field_names) != len(set(field_names)):
            errors.append(f"entity '{entity.name}' has duplicate fields")
        for primary_key in entity.identity.primary_keys:
            if primary_key not in field_names:
                errors.append(f"entity '{entity.name}' references unknown primary key '{primary_key}'")
        relationship_names: set[str] = set()
        for relationship in entity.relationships:
            if relationship.name in relationship_names:
                errors.append(f"entity '{entity.name}' has duplicate relationship '{relationship.name}'")
            relationship_names.add(relationship.name)
            if relationship.depth < 1 or relationship.depth != len(relationship.join_path):
                errors.append(f"entity '{entity.name}' relationship '{relationship.name}' has invalid depth")
        if entity.soft_delete.field is not None and entity.soft_delete.field not in field_names:
            errors.append(f"entity '{entity.name}' has unknown soft-delete field '{entity.soft_delete.field}'")
    if errors:
        raise IRValidationError(errors)
