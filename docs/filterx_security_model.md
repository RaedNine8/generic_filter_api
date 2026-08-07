# FilterX cross-language security model

Every FilterX backend renderer implements the same three security concepts. Framework adapters may use native dependencies, middleware, filters, or annotations, but cannot weaken the contract.

## 1. Identity extraction

Identity extraction runs before generated metadata, query, filter, group, export, and persistence operations. It converts the framework-native request identity into a principal usable by the other hooks.

- FastAPI: configured dependency resolved through `Depends`.
- Express: configured middleware populating a typed request principal.
- Spring Boot: configured security filter/context integration.

No identity hook is configured by default for backward compatibility. Configuring one makes it mandatory on every generated action.

## 2. Row-level predicate

A row predicate receives the principal, request context, entity metadata/model, and action. It contributes a framework-native query restriction or leaves the query unchanged.

Predicates must execute before user filters, search, grouping, counts, sorting, pagination, and export. This guarantees that result rows, totals, grouping buckets, and exported rows all describe the same authorized dataset.

Global and entity-specific predicates compose cumulatively. A renderer must not fetch unrestricted rows and filter them in application memory.

## 3. Field-level visibility

A field-visibility hook decides whether each projected field is visible to the current principal for the current entity and action. The hook is applied while constructing response DTO/projection shapes, including export columns.

The backward-compatible default is public visibility for every generated field. A configured hook may remove or deny fields but cannot cause recursive ORM/entity serialization.

## Enforcement invariants

- Metadata disclosure follows the same field-visibility decision as data responses.
- Interactive queries and exports share the same identity, row, and field authorization path.
- Pagination totals and grouped counts are calculated after row predicates.
- Denials use the shared FilterX error contract for the target framework.
- Hook failures are not silently ignored.
- Relationship cycles are bounded through flat DTO/projection output.
- New backend renderers must pass the common security contract tests before registration as supported targets.

## Compatibility

Existing projects without the new field-visibility hook retain their current generated response shape. Existing FastAPI authentication, permission, global predicate, and entity predicate import paths remain supported. New targets are opt-in and use target-specific configuration namespaces without renaming legacy fields.
