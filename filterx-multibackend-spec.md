# FilterX — Multi-Backend Expansion & Core Refactor Implementation Spec

**Audience:** a coding agent implementing this work directly in the `generic_filter_api` repository.
**Non-negotiable constraint:** every existing user, on the current version, with an existing FastAPI + Angular project that already ran `filterx scan / install / validate`, must be able to upgrade FilterX and re-run every command with **zero behavioral change** unless they explicitly opt into a new target. Nothing in this document may ship as a breaking change. Where a tradeoff exists between "clean design" and "backward compatible," backward compatible wins, and the clean design is achieved through additive abstraction instead.

This spec covers, in order: the core refactor, the ExpressJS+TypeScript backend target, the Spring Boot backend target, the onboarding/instant-demo experience, and the export + React frontend features — plus the cross-cutting versioning, documentation, and testing work that all five depend on. Do not write implementation code in response to this document; treat it as the task breakdown and acceptance criteria to build against.

---

## 0. Ground Rules That Apply to All Five Steps

1. **Audit before touching anything.** Before any refactor code is written, produce a written inventory of every current consumer of the scanner's output shape, the config schema, the manifest format, and the patcher's anchor conventions. This inventory becomes the backward-compatibility checklist against which every later change is verified.
2. **Additive schema evolution only.** Every change to `filterx.yaml`, the scan-output shape, and the manifest format must be a superset of the current shape. New fields get defaults that reproduce today's behavior exactly. No field is renamed or removed in this body of work; if a field is truly obsolete, it is marked deprecated with a warning, not deleted.
3. **Feature-flagged rollout.** New backend targets, new frontend targets, and new IR-based internals are gated behind explicit opt-in configuration. The default code path for an existing project must remain the current, pre-refactor path (or a byte-for-byte / semantically identical successor) until the user explicitly changes their target framework.
4. **One capability at a time, always shippable.** Each of the five steps must land as an independently mergeable, independently releasable unit that leaves `main` in a working state. No step should depend on an unfinished later step.
5. **Every new mechanism gets a dry-run and a rollback path.** Anything added in this work that writes to a user's project (new scanners, new renderers, new dependency-file patchers) must integrate with the existing dry-run/validate/rollback/manifest system rather than inventing a parallel one.
6. **Golden-output regression is the safety net for the whole effort.** Before any refactor code is written, capture the exact current output of `scan`, `backend install`, `frontend install`, and `db` commands against a small set of representative fixture projects (simple entity, entity with one-to-many, entity with many-to-many, entity with a relationship cycle, entity with soft-delete configured, entity with a custom predicate hook). These become the golden baseline. Every later change in this spec must be verified against this baseline with either exact equality or an explicitly documented and approved difference.

---

## Step 1 — Core Refactor: Intermediate Representation + Pluggable Scanner/Renderer Architecture

### Why this is first
Every other step is blocked on this. Adding a second backend language without first separating "what FilterX knows about your models" from "how FastAPI happens to represent that" will force the same abstraction work to be redone twice, worse, under time pressure. This step must be validated by building it *alongside* Step 2, not as a purely theoretical exercise — abstractions designed without a second real consumer tend to be wrong in ways that only show up when that second consumer arrives.

### What must be built

**1.1 — Define a versioned Intermediate Representation (IR) contract.**
Specify a stable, explicitly versioned (e.g. `filterx-ir/v1`) JSON schema that fully describes: entity name and identity, every field with its normalized type category (string, integer, decimal, boolean, date, datetime, enum, uuid, json/blob, binary), nullability, default value presence, every relationship (kind: one-to-one / one-to-many / many-to-one / many-to-many, target entity, join path, computed depth from root), cycle annotations, soft-delete metadata, and any per-field permission or visibility metadata already tracked today. This schema must be capable of representing everything the current Python/SQLAlchemy scanner already extracts — no information loss going from today's internal representation into the IR. Document the schema itself as a first-class artifact (a schema reference document), not just as inline code — this is what future backend/frontend authors, including third parties, will read.

**1.2 — Refactor the existing SQLAlchemy scanner to be an IR producer, not a special case.**
The current scanner's output must be reshaped to emit the IR exactly, with a compatibility shim ensuring anything downstream that still expects the old internal shape continues to receive it (either the shim continues generating it, or every consumer is migrated in this same step — pick migrating every consumer, since maintaining two shapes long-term is itself a regression risk).

**1.3 — Define a Scanner plugin interface, and make it explicit that not all scanners run in-process.**
The current scanner works via same-process reflection against Python objects. This assumption does not hold for other languages. The interface must support three execution modes: in-process reflection (Python/SQLAlchemy, as today), out-of-process invocation of another already-required toolchain (e.g. invoking Node to read a Prisma schema, since Node is already required for the Angular frontend tooling), and out-of-process invocation of a toolchain that is *new* to the user's environment (e.g. invoking a Java process for Spring Boot/JPA). Each mode has different failure characteristics (missing runtime, missing dependency, version mismatch, timeout) and each must be detected and reported with an actionable error rather than a stack trace.

**1.4 — Define a Renderer plugin interface with a registry, not hardcoded imports.**
`filterx.yaml`'s `backend.framework` and `frontend.framework` values must resolve to renderer implementations through a discoverable registry mechanism, so that adding a new target is "register a new plugin" rather than "add a new branch to existing conditionals scattered through the codebase." Audit every current place that branches on "we're doing FastAPI" or "we're doing Angular" implicitly (not just explicit if/else — also naming conventions, file layout assumptions, and hardcoded file extensions) and route all of it through this registry.

**1.5 — Generalize dependency-file injection beyond text-anchor patching.**
The current patcher does generic anchor-comment text patching, which is safe for source files but not safe for structured dependency manifests. Specify that `package.json` must be patched via structured JSON parsing/merging (not text insertion), and that any future XML-based manifest (e.g. Maven's `pom.xml`) or Groovy/Kotlin-DSL-based manifest (e.g. Gradle) must be patched via a real parser for that format, never via text-anchor insertion. Text-anchor patching remains the mechanism for actual source files only. This must be designed now, even though it is only fully exercised in Steps 2 and 3, because retrofitting it later would touch the same core patcher code twice.

**1.6 — Define a cross-language security hook vocabulary.**
Specify three abstract hook points that every renderer must support, regardless of target language: identity extraction from an incoming request, a row-level filtering predicate hook (equivalent to today's global predicate hooks), and a field-level visibility/permission hook (new capability, not currently present — specify it now as part of the common vocabulary so every future renderer, including the existing FastAPI one, implements it consistently rather than Python getting a different security model than everything that follows). Document how each of the three existing/future backends satisfies each hook conceptually, without prescribing implementation code.

**1.7 — Specify serialization safety for relationship cycles as a first-class, cross-language requirement.**
Any renderer that generates response serialization must generate flat projection/DTO shapes rather than serializing ORM/entity objects directly, specifically to avoid infinite recursion or accidental over-fetching on bidirectional relationships. This applies to the existing FastAPI target's generated code as much as to future targets — audit the current generated response models against this requirement and correct them if needed as part of this step, since a shared vocabulary is worthless if the first implementation doesn't already follow it.

**1.8 — Migration path for existing manifests, backups, and rollback bundles.**
Any user with an existing manifest file generated by the current version must have their manifest recognized and fully operable (rollback, validate, re-install) after upgrading to the refactored version. Specify a manifest schema version field, and specify that the manifest loader must handle both the pre-refactor shape and the new shape without requiring the user to take any manual action.

**1.9 — Deprecation and communication policy.**
Anything genuinely obsoleted by this refactor (not deleted, per the ground rules — deprecated) must emit a clear, actionable warning when encountered, pointing to what replaces it and on what timeline it will eventually be removed in a future major version.

### Edge cases and failure modes to explicitly account for
- A project with relationship cycles that the current scanner already special-cases — verify the IR represents this identically post-refactor.
- A project using `respect_soft_delete` and custom predicate hooks — verify these survive translation into the IR without silent loss of configuration.
- A manifest or backup bundle created by a pre-refactor version, loaded by a post-refactor version, then rolled back — must restore the project to its exact original state.
- Partial/interrupted patch operations from a previous version, combined with a new version's validate/rollback logic — must not corrupt state or silently skip conflict detection.
- A `filterx.yaml` file with no new fields at all (a genuinely untouched legacy config) must produce identical generation output to the pre-refactor version, not "equivalent" output — identical.

### Testing requirements for this step (necessary tests only, no boilerplate)
- **Golden-output regression suite**: run `scan`, `backend install`, `frontend install`, and `db` against every fixture project captured in the ground-rules baseline, both immediately before and immediately after the refactor, and assert equality (or document and get explicit sign-off on any intentional difference).
- **IR schema contract tests**: validate that the IR produced by the refactored scanner conforms to the published IR schema, for every fixture project, including the cycle-containing and soft-delete-containing ones.
- **Manifest migration tests**: load manifests generated by the pre-refactor version and confirm validate/rollback/re-install all function correctly against the post-refactor codebase.
- **Registry resolution tests**: confirm that an unregistered/misconfigured `backend.framework` or `frontend.framework` value fails fast with a clear, actionable error rather than falling through to undefined behavior.
- Do not write unit tests for internal helper functions that have no external contract implication — test the IR contract, the migration path, and the golden-output equivalence, not implementation details that are free to change.

---

## Step 2 — ExpressJS + TypeScript Backend Target

### Why this is second
It is the first real consumer that proves the Step 1 architecture generalizes beyond a single language, and it is the lowest-risk second target available: Node is already a required toolchain dependency (the Angular frontend needs it), Prisma's own schema metadata is already fully structured and introspectable, and TypeScript shares a type system with the existing Angular frontend, which reduces the number of genuinely new concepts introduced at once.

### What must be built

**2.1 — A scanner that reads Prisma schema metadata and translates it into the Step 1 IR.**
This scanner runs as an out-of-process Node invocation. It must detect whether Prisma is present and configured in the target project, and produce a clear, actionable error (not a stack trace) if it is not, including guidance on what the user needs to add before FilterX can proceed. The translation from Prisma's own structured metadata into the FilterX IR must preserve every concept the IR requires: field nullability, relationship kind and direction, relationship depth, and cycle detection equivalent to what the Python scanner already performs.

**2.2 — A dynamic query-building layer against Prisma's query API**, mapping the same operator vocabulary the FastAPI backend already supports (equality, comparison, range, membership, null checks, text/pattern matching, and the existing grouping/sorting/pagination semantics) so that the same abstract filter tree produces logically equivalent results regardless of which backend executes it.

**2.3 — Response DTO generation**, following the Step 1 requirement that responses are flat projections rather than serialized ORM entities, to avoid circular-relationship serialization failures.

**2.4 — Validation via a TypeScript-native schema validation library**, providing the equivalent guarantees Pydantic provides today: reject malformed filter trees, invalid operators for a given field type, and out-of-range pagination parameters before they reach the query layer.

**2.5 — The three security hooks from Step 1.6**, implemented via Express middleware: identity extraction, a row-level predicate hook equivalent to the existing global predicate hooks, and the new field-level visibility hook.

**2.6 — Production-hardening middleware**: secure HTTP headers, and a rate limiter / query-cost guard equivalent to what is specified for the existing backend, sized appropriately for the deep-relationship-join risk that already exists conceptually in the current codebase's cycle/depth detection.

**2.7 — Structured logging**, at parity with whatever the current backend's logging approach provides, so operators running a mixed-stack deployment get consistent observability.

**2.8 — Dependency-file patching for `package.json`**, using the structured JSON-merge mechanism specified in Step 1.5, not text-anchor insertion — must correctly merge into an existing `package.json` without disturbing unrelated dependencies, scripts, or formatting conventions already present in the user's file.

**2.9 — Router/app mounting into an existing Express application**, using anchor-based patching (this part of the pipeline is a genuine source file, so the existing patcher mechanism applies), including detection of common existing Express app structures so the generated router can be mounted without assuming a greenfield project layout.

### Edge cases and failure modes to explicitly account for
- Prisma client generation is a separate build step from schema authoring — the scanner must account for the possibility that the Prisma client is stale relative to the schema file and must not silently produce IR based on outdated generated artifacts.
- TypeScript build configuration variance (module resolution strategy, target ECMAScript version, monorepo path aliases) must not break the generated code; detect the project's existing `tsconfig.json` conventions rather than assuming a single configuration.
- Existing Express apps vary widely in structure (single-file, layered, feature-folder) — the mounting anchor strategy must degrade gracefully with a clear error rather than guessing incorrectly when no recognizable mounting point is found.
- Data type edge cases specific to this stack: JavaScript's single numeric type versus SQL decimal/numeric precision, `null` versus `undefined` semantics in Prisma versus Python's `None`, and timezone handling differences between Prisma's date handling and the existing backend's — all filter operators touching numeric or date fields must be verified for consistent behavior across backends, not just consistent syntax.
- Case sensitivity and collation differences for text pattern matching, which can vary by underlying database engine independent of the ORM — verify behavior is documented and consistent per supported database, and that any known inconsistency is surfaced to the user rather than silently producing different results than the FastAPI backend would for the same filter.

### Testing requirements for this step
- **Scanner unit tests** against a small set of representative Prisma schema fixtures: a simple entity, one-to-many, many-to-many, and a relationship cycle — asserting correct IR output for each.
- **Cross-backend parity tests**: given the same abstract filter tree fixture, assert that the Express backend and the existing FastAPI backend return logically equivalent results against equivalent seeded data, for every supported operator and for grouping/sorting/pagination.
- **End-to-end tests** that actually generate a fresh Express project via FilterX, install its dependencies, run it against a seeded test database, and exercise filter/search/paginate/sort/group requests through real HTTP calls.
- **Security enforcement tests**: confirm the row-level predicate hook and field-level visibility hook actually restrict results/fields as configured, and confirm the rate limiter actually triggers under configured thresholds.
- **Dry-run/rollback tests** specific to the new `package.json` JSON-merge patcher, confirming it can be applied and rolled back without corrupting an existing file's untouched contents.
- Skip redundant unit tests for logic that is already covered by the cross-backend parity suite — the parity suite is the primary correctness signal for this step, not isolated unit tests of internal helpers.

---

## Step 3 — Spring Boot Backend Target

### Why this is third, not second
This is the highest-risk target in the whole plan: it introduces a genuinely new toolchain dependency (the JVM) that the user's environment does not otherwise require, it is a compiled language where generation errors can surface only at build time rather than at generation time, and its serialization, security, and dependency-management conventions differ the most from the Python baseline. Doing this second, before the Step 1 architecture has been proven against a real second consumer in Step 2, risks discovering the abstraction was only ever generic enough for two JavaScript-family languages and forcing a second disruptive refactor mid-flight. Doing it third means the architecture is already validated and this step is "hardening a proven design against a harder case," not "debugging the design and the new language simultaneously."

### What must be built

**3.1 — A versioned scanner helper artifact for the JVM side**, invoked as an out-of-process step, that uses JPA's runtime metamodel (or the equivalent Hibernate metadata facility) against the user's compiled entity classes to extract the same information the IR requires, including relationship kind/depth/cycle detection at parity with the existing scanner. This artifact must be explicitly versioned and its compatibility with the FilterX Python package version must be checked at invocation time, with a clear error if versions are mismatched. Specify graceful, actionable failure when no JVM is present, when the project cannot be compiled/reflected against (e.g. it has pre-existing compile errors), or when the helper artifact and the installed FilterX version have drifted apart.

**3.2 — A dynamic query-building layer using JPA's Criteria API and Specification composition**, explicitly avoiding any approach that requires a build-time annotation-processing step, since that would conflict with FilterX's "generate and patch, don't require the host project to adopt a new build pipeline" philosophy. Map the same operator vocabulary as the other two backends.

**3.3 — Generated response DTOs using the language's built-in record feature** rather than requiring an additional boilerplate-reduction library, specifically to avoid forcing an extra dependency choice onto the host project — consistent with the "minimally invasive" principle that governs every other part of this tool.

**3.4 — Bean validation** on generated filter/request DTOs, providing the same category of guarantee Pydantic provides today.

**3.5 — The three security hooks from Step 1.6**, implemented via the host framework's security/filter mechanism and method-level authorization annotations: identity extraction, row-level predicate composition, and field-level visibility.

**3.6 — Mandatory API documentation generation.** Unlike the existing FastAPI target, this framework does not generate interactive API documentation by default — an explicit dependency and configuration for this must be part of the generated output, not treated as optional, since parity with the existing backend's out-of-the-box documentation experience is part of what makes this a fair third option rather than a downgrade.

**3.7 — A rate limiter / query-cost guard** at parity with the other two backends, appropriately sized for this ecosystem's idiomatic resilience libraries.

**3.8 — Structured logging** at parity with the other two backends.

**3.9 — Dependency-file patching for both supported build tools.** Both Maven's XML-based manifest and Gradle's manifest must be supported (detect which the host project uses, do not assume one), using the real-parser-based patching mechanism specified in Step 1.5 — never text-anchor insertion for these files, since a malformed insertion into a build manifest can silently break the user's entire build rather than failing loudly.

**3.10 — A generation-time compile-verification step.** Because this is a compiled language, a generated file can be syntactically or semantically wrong in a way that is invisible until the host project is built. The generation pipeline for this target must include an automated compile-check (invoking the project's own build tool in a check/verify mode) as part of `validate`, so that generation failures are caught immediately rather than surfacing later as a confusing build error disconnected from the FilterX command that caused it.

**3.11 — Directory/package-naming convention enforcement.** Unlike the other two backends, this ecosystem enforces a strict correspondence between package declarations and directory layout. The renderer must derive correct package declarations from the host project's existing structure and must fail explicitly, before writing any files, if the target location and intended package name would be inconsistent — rather than generating a file that compiles-fails after the fact.

### Edge cases and failure modes to explicitly account for
- Multi-module build layouts, where entities, security configuration, and web-layer code may live in different modules — the scanner and renderer must detect and handle this rather than assuming a single-module project.
- Numeric precision differences between this ecosystem's high-precision decimal type and the equivalent types in the other two backends — any filter operator touching decimal/currency-like fields must be verified for consistent comparison behavior across all three backends.
- Enum handling differences (this ecosystem's native enums versus the other two backends' representations) — verify equivalent filtering behavior for enum-typed fields across all three targets.
- Timezone-aware versus timezone-naive datetime handling differences between this ecosystem's date/time API and the other two backends — must be explicitly tested, since this is a common, easy-to-miss source of silent cross-backend inconsistency.
- A host project that already uses a boilerplate-reduction library the generated code deliberately avoids introducing — the renderer must not assume its absence causes friction, and must not attempt to detect/require it either way, remaining agnostic to what else exists in the project outside what it directly touches.

### Testing requirements for this step
- **Scanner artifact tests**, run on the JVM side, against representative fixture entity sets (simple entity, one-to-many, many-to-many, relationship cycle) — asserting correct IR extraction for each, mirroring the Step 2 scanner test structure.
- **Cross-backend parity tests**, extending the Step 2 parity suite to include this backend as a third participant, confirming the same abstract filter tree produces logically equivalent results across all three backends against equivalent seeded data.
- **Generation-time compile-verification tests**: for every fixture project, confirm that generated code actually compiles successfully as part of the automated test suite, not just at manual review time.
- **End-to-end tests** that generate a fresh project via FilterX, build it with its own build tool, run it against a seeded test database (using a disposable, ephemeral database instance per test run), and exercise the same filter/search/paginate/sort/group requests as the other two backends' end-to-end suites.
- **Security enforcement tests**, mirroring Step 2's, adapted to this ecosystem's security/authorization mechanism.
- **Version-compatibility tests** for the scanner helper artifact, confirming a mismatched version between the artifact and the installed FilterX package is detected and reported clearly rather than producing corrupted or incomplete IR output silently.

---

## Step 4 — Onboarding / Instant-Demo Experience

### Why this is fourth
Its value is directly proportional to how many real stack combinations exist to showcase — it is far more compelling once there are three backend and (eventually) two frontend targets to demonstrate than it would have been with only the original single-stack combination. It is also a purely additive, presentation-layer investment: it does not modify any existing generation logic, only adds new scaffolding entry points, so it correctly carries no regression risk to the core system and can safely be sequenced after the harder architectural work it exists to showcase.

### What must be built

**4.1 — A one-command scaffolding entry point** that creates a small, fully working sample project (a handful of related entities covering at least one one-to-many and one many-to-many relationship) already wired up end-to-end for a chosen backend/frontend combination, runs the equivalent of scan/install/validate automatically, and starts both the generated backend and frontend so a new evaluator sees working filtering, search, pagination, sorting, and grouping without performing any manual setup steps themselves.

**4.2 — Explicit non-interference with the existing manual workflow.** This entry point must be entirely additive: it must not alter the behavior, defaults, or output of the existing manual `scan`/`install`/`validate` command sequence for users who are integrating FilterX into their own existing project rather than trying the demo.

**4.3 — Coverage across the full stack matrix.** Once Steps 2 and 3 exist, this scaffolding must offer the demo across all supported backend targets (and, when a second frontend eventually lands, across supported frontend targets too), not only the original combination, since demonstrating breadth is a core part of this step's purpose.

**4.4 — A low-friction discovery path** for someone evaluating the project without installing anything locally first (for example, a hosted or embeddable version of the same demo scaffold), so the barrier to seeing the tool work is as close to zero as possible.

### Edge cases and failure modes to explicitly account for
- The demo scaffolding must clean up or clearly sandbox itself (ports, temporary databases, generated files) so running it repeatedly, or running it alongside a user's own unrelated FilterX project, cannot collide with or corrupt anything else on the user's machine.
- Any dependency the demo needs (a JVM for the Spring Boot demo option, for instance) that the user does not have installed must be detected up front with a clear, actionable message, not a confusing failure partway through scaffolding.

### Testing requirements for this step
- **Smoke tests across the full stack matrix in CI**: for every supported backend/frontend combination, confirm the one-command scaffold completes successfully and the resulting generated project starts up and responds correctly to a basic filter/paginate/sort request.
- Do not write deep functional tests here — correctness of filtering behavior itself is already covered by the parity and end-to-end suites in Steps 1–3; this step's tests only need to confirm the scaffolding and startup sequence itself works for every combination.

---

## Step 5 — Export (CSV/Excel/JSON) and Second Frontend (React)

### Why this is last
Both pieces are genuinely valuable but are self-contained, additive features that neither block nor are blocked by the framework-expansion work in Steps 1–3. They can be picked up opportunistically once the harder architectural bets have landed, and — importantly — implementing them *after* the multi-backend refactor means they only need to be built once, against the shared IR and the shared query-building contract, rather than being built once for the original stack and then redone for each new backend afterward.

### What must be built — Export
**5.1 — A streaming export capability** that reuses the exact same filter/sort/query-building logic already used for the interactive JSON results, for every supported backend, so export results and interactive results can never silently diverge from one another.

**5.2 — Support for at least CSV, Excel, and JSON output formats**, generated via streaming rather than full in-memory buffering, so large result sets do not risk memory exhaustion on the server.

**5.3 — The same row-level and field-level security hooks must apply to exports as apply to interactive queries** — an export path must never become an unintentional bypass of access controls that are enforced on the interactive endpoint.

**5.4 — A corresponding UI affordance** in the generated frontend component(s) to trigger an export of the currently applied filter/sort configuration.

**5.5 — Character-encoding correctness for CSV specifically**, since this is a common, easy-to-miss cross-platform correctness issue (encoding and line-ending conventions differ across operating systems and spreadsheet applications).

### What must be built — React Frontend Target
**5.6 — A renderer implementing the same generated feature set as the existing frontend target** (filtering UI, search, pagination, custom filter builder, sorting, grouping) against the shared IR from Step 1, ensuring feature parity rather than a reduced subset.

**5.7 — Shared type generation**, deriving frontend types directly from the same IR that drives backend generation, so this target — like the Express/TypeScript backend — benefits from a genuinely type-safe path from data model through to UI, rather than re-deriving types by hand.

**5.8 — The same dependency-file patching care applied to `package.json`** as specified in Step 2.8, since a React project shares the same manifest format and the same risk of naive text-patching corrupting an existing file.

### Edge cases and failure modes to explicitly account for
- Export of a result set produced by a filter tree with deep relationship joins must respect the same query-cost/rate-limit guards as interactive queries — an export request is not exempt from the abuse-prevention work done in Steps 2 and 3.
- Very large result sets must not be fully materialized in memory on either the backend (query execution/streaming) or the generated frontend (triggering a download versus attempting to render the full set in the browser).
- The React renderer must be verified against the same relationship-cycle and deep-nesting fixtures used for the existing frontend target, since UI components that recursively render nested filter groups are a plausible place for the same class of cycle-related bug to reappear in a new codebase.

### Testing requirements for this step
- **Parity tests for export**: confirm exported data for a given filter/sort configuration matches the equivalent interactive JSON response, for every supported backend and every supported export format.
- **Security tests for export**: confirm row-level and field-level restrictions that apply to interactive queries are also enforced on export requests, for every supported backend.
- **Component-level tests for the React renderer**, covering the same representative fixture set (simple entity, one-to-many, many-to-many, relationship cycle) used throughout the rest of this spec, to confirm feature parity with the existing frontend target rather than a reduced feature set.
- **Dependency-file patching tests** for the React target's `package.json` merge, mirroring Step 2.8's tests.

---

## Cross-Cutting Requirements That Span All Five Steps

**Versioning and release strategy.** Adopt semantic versioning discipline for this entire body of work: the IR schema, the manifest schema, and each renderer/scanner plugin should be independently versioned where practical, so that a future change to one backend target does not force a version bump that implies changes to unrelated targets. New backend/frontend targets ship as explicitly opt-in configuration values, never as a change in default behavior for existing projects.

**A `filterx upgrade` capability for configuration migration.** As the config schema gains new optional fields across these steps, provide a command that can inspect an existing `filterx.yaml` and a manifest from an older version and bring them forward automatically, rather than requiring users to hand-edit configuration files across version boundaries.

**Documentation must be treated as a deliverable, not an afterthought.** For each of the five steps: update the README and any existing docs/pitch materials to reflect new capabilities, publish the IR schema reference as a standalone document, and produce a security-model document explaining the three cross-language hooks from Step 1.6 so a team evaluating or switching backend targets understands the guarantees without reading source code.

**A consistent error/response shape across backend targets.** Since a team may reasonably run the same Angular (or future React) frontend against different backend choices in different projects, error response shapes, pagination metadata shapes, and validation-error formats must be specified once, centrally, and every renderer held to that same contract — this avoids a frontend needing backend-specific error-handling logic depending on which target generated its API.

**A full CI matrix covering every supported combination.** Continuous integration must be capable of running the Python, Node, and JVM toolchains together, and must run the golden-output regression suite, the cross-backend parity suite, and the end-to-end suite for every backend target on every pull request that touches scanner, renderer, patcher, or IR schema code — this is what actually enforces the "do not break anything" requirement over time, rather than relying on manual verification before each release.

---

## Master Testing Strategy Summary

Testing across this entire body of work is organized around four necessary layers — deliberately avoiding redundant or low-value unit tests of internal implementation details that carry no external contract:

1. **Golden-output regression** — proves the refactor in Step 1 changes nothing for existing users.
2. **IR and manifest contract tests** — prove every scanner produces a valid, complete IR, and every manifest version is correctly migrated and rolled back.
3. **Cross-backend parity tests** — prove that the same abstract filter tree produces logically equivalent results regardless of which of the three backends executes it, across every operator, and across grouping/sorting/pagination/export.
4. **End-to-end tests per backend/frontend target** — prove that a freshly generated project, built and run for real, correctly serves filter/search/paginate/sort/group/export requests and correctly enforces the row-level and field-level security hooks, including under rate-limit/query-cost-guard conditions.

Every test added in this work should map to one of these four layers. If a proposed test does not clearly map to one of them, it is very likely testing an implementation detail that is free to change and should not be written.

---

## Risk Register — Things Easy to Miss

- Circular relationship serialization must be solved once, correctly, in the IR/renderer contract (Step 1.7) — do not let each backend renderer solve this independently, or three subtly different bugs will emerge instead of one correct design.
- Numeric precision (decimal/currency handling), enum representation, and timezone-aware-vs-naive datetime handling all differ subtly across the three backend ecosystems — every filter operator touching these types must be explicitly cross-backend tested, not assumed to be consistent because the syntax looks similar.
- `null`/`undefined`/`None` semantics differ across the three ecosystems and must be normalized consistently at the IR boundary so "field is null" filtering behaves identically regardless of backend.
- Text pattern-matching case sensitivity and collation can vary by underlying database engine independent of which backend/ORM is used — document and test this per supported database rather than assuming ORM choice fully determines behavior.
- A compiled-language target (Spring Boot) can fail in ways invisible until build time — the compile-verification step in Step 3.10 is not optional polish, it is the mechanism that keeps generation failures from becoming confusing, disconnected build errors for the end user.
- Dependency-file patching for structured formats (JSON, XML, Gradle's DSL) must never reuse the plain-text anchor-comment mechanism designed for source files — a malformed patch to a build manifest can silently break a user's entire build in a way a malformed patch to a source file typically will not.
- Export functionality must be treated as a second surface subject to the same security hooks as interactive queries, not a bypass — this is an easy place to accidentally leak row- or field-level restricted data if export is implemented as a separate, parallel code path instead of reusing the same query and authorization pipeline.
- Existing manifests, backups, and rollback bundles created by pre-refactor versions of FilterX must remain fully operable after the Step 1 refactor ships — this is the single most direct test of the "do not break anything" requirement and should be verified explicitly, not assumed to follow automatically from the schema being a superset.

---

## Definition of Done, Per Step

- **Step 1** is done when the golden-output regression suite passes with zero unintended differences, the IR schema is published and validated against every fixture project, and every existing manifest/backup file from the pre-refactor version can be loaded, validated, and rolled back successfully.
- **Step 2** is done when the cross-backend parity suite passes for the Express/TypeScript target across every operator and every grouping/sorting/pagination scenario, the end-to-end suite passes against a real generated project, and the security enforcement tests pass.
- **Step 3** is done when the same parity and end-to-end bar as Step 2 is met for Spring Boot, the compile-verification step is part of the automated pipeline (not a manual step), and the scanner helper artifact's version-compatibility checks are verified.
- **Step 4** is done when the one-command scaffold succeeds for every supported backend/frontend combination in CI, and the existing manual workflow is verified unaffected.
- **Step 5** is done when export parity and security tests pass for every backend and format, and the React frontend renderer passes the same fixture-based component tests as the existing frontend target with no feature gap.
