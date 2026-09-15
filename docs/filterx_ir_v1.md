# FilterX Intermediate Representation v1

The FilterX IR is the stable boundary between model scanners and backend/frontend renderers. Its media-type identifier is `filterx-ir/v1`. The normative machine-readable schema is distributed as `filterx/schemas/filterx-ir-v1.schema.json`.

## Compatibility

- IR changes are additive within a schema version.
- A breaking contract change requires a new IR version.
- Plugin versions are independent from the IR version.
- Existing version-1 FilterX configuration and legacy scan JSON remain unchanged. The SQLAlchemy scanner additionally produces this IR internally for registered renderers.
- Entity and route arrays are deterministic. Entities are ordered by name, relationships by relationship name, and route methods lexically.

## Root document

| Property                 | Type     | Meaning                                                                           |
| ------------------------ | -------- | --------------------------------------------------------------------------------- |
| `version`                | string   | Always `filterx-ir/v1`.                                                           |
| `source_framework`       | string   | Scanner family, currently `sqlalchemy`; future values include `prisma` and `jpa`. |
| `entities`               | entity[] | Framework-neutral model definitions.                                              |
| `routes`                 | route[]  | Existing host routes used for conflict checks.                                    |
| `security`               | object   | Cross-language security hook bindings.                                            |
| `max_relationship_depth` | integer  | Maximum acyclic depth discovered in the selected model graph.                     |

## Entity

Each entity contains:

- `name`: stable model identity used by generated routes and metadata.
- `identity.module`: source module/package identity.
- `identity.table`: backing table or collection name.
- `identity.primary_keys`: ordered primary-key field names.
- `fields`: normalized fields.
- `relationships`: direct relationship edges.
- `cycle_memberships`: every detected closed graph path containing the entity.
- `soft_delete`: whether configured soft-delete handling applies and its detected field.

A scoped scan may retain a relationship whose target entity is intentionally excluded from generation. Renderers must not generate an endpoint for an excluded target, but may retain the edge for metadata and validation.

## Field

Normalized field categories are:

- `string`
- `integer`
- `decimal`
- `boolean`
- `date`
- `datetime`
- `enum`
- `uuid`
- `json/blob`
- `binary`

Every field also records its scanner-native `source_type`, nullability, primary-key and uniqueness state, default-value presence, foreign-key targets, supported operation vocabulary, enum values, visibility mode, and optional permission identifier.

The IR normalizes floating-point, numeric, and decimal ORM types to `decimal` while retaining their original normalized scanner value in `source_type`. A renderer is responsible for preserving the precision semantics of its target ecosystem.

## Relationship

Relationship kinds are `one-to-one`, `one-to-many`, `many-to-one`, and `many-to-many`. Each relationship records its target, target table, collection status, reverse binding, join path, depth, and whether the edge participates in a detected cycle.

`join_path` is an ordered list of relationship names. `depth` must equal its length and must be at least one. Generated response serializers must use bounded flat projections/DTOs rather than recursively serializing ORM entities.

## Soft delete

`soft_delete.respected` is true only when soft-delete handling is configured and a supported marker field is present. The detected field is recorded in `soft_delete.field`. A renderer must not silently invent a marker field.

## Routes

Routes record `path`, `name`, sorted HTTP `methods`, and their source framework type. They are conflict-detection inputs, not generated route declarations.

## Security vocabulary

The `security` object carries:

- `identity`: request identity extraction hook.
- `row_predicates`: global row-level restriction hooks.
- `entity_row_predicates`: entity-specific row-level hooks.
- `field_visibility`: field-level visibility/permission hook.

The conceptual and enforcement contract is documented in [FilterX security model](filterx_security_model.md).

## Scanner execution modes

Registered scanners declare one execution mode:

1. `in-process`: reflection in the FilterX Python process, used by SQLAlchemy.
2. `existing-toolchain`: subprocess execution using a toolchain already required by the selected stack, such as Node for Prisma.
3. `new-toolchain`: subprocess execution requiring an additional ecosystem runtime, such as the JVM for JPA.

Subprocess scanners must translate missing runtime, non-zero exit, timeout, malformed JSON, and invalid IR into actionable FilterX diagnostics. They must never expose an unhandled toolchain stack trace as the primary user error.
