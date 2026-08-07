# FilterX CLI

FilterX adds a reusable filtering layer to an existing project through safe code generation and anchor-based patching.
It is designed to remove repetitive filtering boilerplate while keeping changes explicit and reversible.

The current default stack remains `sqlalchemy` scanning, `fastapi-sqlalchemy` backend rendering, and `angular` frontend rendering. These defaults are additive configuration values; existing version-1 configuration files do not need to be edited and retain identical generated output.

## The idea in one minute

FilterX workflow is always:

1. Scan your models and routes
2. Generate integration files
3. Patch only at your explicit anchors
4. Validate
5. Rollback if needed

This means no blind rewriting of host files.

## What you need before first run

Required:

- Python 3.10+
- Importable FastAPI app object
- Importable SQLAlchemy Base
- Importable SQLAlchemy models package
- Angular workspace for generated UI integration
- Node.js + npm

Optional:

- Alembic migration folder (only if db generation is enabled)

## Install

For contributors inside this repo:

```powershell
python -m pip install -e tools/filterx
```

For consumers from GitHub:

```powershell
pip install "git+https://github.com/RaedNine8/generic_filter_api.git#subdirectory=tools/filterx"
```

Check command:

```powershell
filterx --help
```

## First successful run (copy/paste)

1. Create filterx.yaml in your project root.
2. Add anchors in your configured backend and frontend host files:

```python
# FILTERX:ROUTER_MOUNT
```

```ts
// FILTERX:ROUTES
// FILTERX:PROVIDERS
```

3. Run:

```powershell
filterx install --project-root . --config filterx.yaml --dry-run --json
filterx install --project-root . --config filterx.yaml --no-dry-run --yes --json
filterx validate --project-root . --config filterx.yaml --json
```

4. Install generated frontend dependencies and build your Angular app:

```powershell
cd frontend
npm install
npm run build
cd ..
```

Replace `frontend` with your configured `frontend.workspace_root` if your Angular app lives elsewhere.

5. Verify endpoint:

```text
GET /api/filterx/metadata
```

## filterx.yaml purpose

filterx.yaml is the contract between FilterX and your project.
It tells FilterX where your app is, where generated files should go, and which host files can be patched.

Minimum keys you must set correctly:

- python.app_import
- python.base_class_import
- python.models_package
- python.session_dependency_import
- backend.mount_file
- backend.mount_anchor
- frontend.workspace_root
- frontend.routes_file
- frontend.app_config_file

Optional plugin selectors default to the legacy stack:

- scan.framework: sqlalchemy
- backend.framework: fastapi-sqlalchemy
- frontend.framework: angular

The opt-in frontend renderer values are `react-vite`, `nextjs`, and `vue`. All three generate IR-derived entity types plus search, nested filter groups, sorting, grouping, pagination, and CSV/XLSX/JSON export controls. Angular remains the default.

Unknown plugin names fail before generation with the registered alternatives listed in the diagnostic.

## Intermediate representation and plugins

Registered scanners produce the versioned `filterx-ir/v1` contract consumed by new renderer plugins. The legacy scan, diagnostics, plan, manifest, and generated files remain unchanged for existing projects.

- IR schema reference: ../../docs/filterx_ir_v1.md
- Security hook model: ../../docs/filterx_security_model.md
- Normative JSON Schema: filterx/schemas/filterx-ir-v1.schema.json

Scanner plugins declare whether they run in-process, through an already-required toolchain, or through a new external toolchain. Missing runtimes, timeouts, failed subprocesses, and malformed IR are reported as actionable scanner errors.

Source files continue using explicit text anchors. Structured dependency manifests use parser-backed operations instead: JSON uses the standard JSON parser, Maven POMs use `xml.etree.ElementTree`, and Gradle Groovy/Kotlin DSL files use their pinned tree-sitter grammars. FilterX never falls back to anchor insertion for dependency manifests. Maven merge payloads contain optional `properties` and a `dependencies` list whose entries use `group_id`, `artifact_id`, and optional `version`, `scope`, `type`, `classifier`, and `optional`. Gradle payloads contain a `dependencies` list whose entries use `configuration` plus either `group`/`name`/`version` or an explicit `notation`. Entries are sorted and deduplicated deterministically; dry-run, manifest tracking, exact backup, and rollback use the common patch pipeline.

## Spring Boot + JPA target

The `jpa` scanner is opt-in and requires a full JDK 17+ installation. It compiles the selected Maven or Gradle module, resolves its runtime classpath, then source-launches the versioned bundled Java helper to reflect runtime-visible `jakarta.persistence` or `javax.persistence` annotations into `filterx-ir/v1`.

```yaml
scan:
  framework: jpa
  jpa:
    module_path: services/catalog
    build_tool: maven # optional when exactly one build manifest is present
backend:
  framework: spring-boot-jpa
```

Maven Wrapper and Gradle Wrapper commands are preferred automatically, so globally installed Maven/Gradle is not required when a wrapper exists. `scan.jpa.module_path` selects a module; `java_command`, `maven_command`, `gradle_command`, compile/helper timeouts, and extra build arguments are configurable. `classes_dir` plus `classpath` can select already-compiled output. Missing Java/build tools, ambiguous manifests, pre-existing compile errors, classpath failures, timeouts, reflection failures, and helper/package/protocol version drift have distinct actionable scanner errors.

The opt-in `spring-boot-jpa` renderer generates metadata, request DTOs, JPA specifications, query services, controllers, security extension points, configuration, streaming exports, and shared JSON error handling. It parser-merges Spring Data JPA, validation, springdoc, Resilience4j, and Apache POI dependencies into Maven or Gradle and validates the generated project with its real build tool. Configure module/build paths, generated package, records, dependency versions (including `poi_version`), query-cost and rate limits, compile timeout, command overrides, and extra build arguments under `backend.spring`. Host applications can override the conditional identity extractor, row-level security, and field-visibility beans without modifying generated sources.

## Express + Prisma target

The Express target is opt-in. Set:

```yaml
scan:
  framework: prisma
backend:
  framework: express-prisma
frontend:
  enabled: false
```

The host project must contain a configured Prisma schema, declare both `prisma` and `@prisma/client`, have a current generated Prisma client, and expose an Express app file containing `// FILTERX:ROUTER_MOUNT`. Override paths under `scan.prisma` and `backend.express` when the defaults do not match the project layout.

Run `filterx scan` before `filterx backend install`. Prisma scans always emit `.filterx/ir.json`. Installation then:

- generates TypeScript metadata, Zod validation, Prisma query translation, flat response projection, and the FilterX router;
- mounts the router under the configured API prefix;
- structurally merges runtime and development dependencies into the existing `package.json`;
- preserves dry-run, manifest, validation, backup, and rollback behavior.

Generated routes support the same query, filter-tree, grouping, sorting, search, and pagination contracts as the FastAPI target. Security hooks are exported from the module configured by `backend.express.hooks_module`; it must export `hooks` implementing identity extraction, row predicates, and field visibility. Safe no-op hooks are generated when no custom module is configured.

Case-insensitive Prisma filters follow the configured datasource provider. PostgreSQL and MongoDB receive Prisma's `mode: 'insensitive'`; providers such as SQLite and MySQL rely on their database collation behavior because Prisma does not accept that option for those providers. Deployments requiring a particular case-folding policy must configure matching database collations across backends.

## Web frontend targets

Choose one renderer and configure its target-specific paths:

```yaml
frontend:
  framework: react-vite # react-vite, nextjs, vue, or the default angular
  react_vite:
    workspace_root: frontend
    generated_root: src/filterx-generated
    host_file: src/App.tsx
    host_anchor: "// FILTERX:APP"
    api_base_url: /api/filterx
```

`nextjs` generates `src/app/filterx/page.tsx` and uses `frontend.nextjs.workspace_root`, `generated_root`, and `api_base_url`. `vue` uses `frontend.vue.workspace_root`, `generated_root`, `host_file`, `host_anchor` (`<!-- FILTERX:APP -->` by default), and `api_base_url`. React/Vite and Vue require their host anchor; Next.js owns only its generated route. Package dependencies are structurally merged into the existing package manifest and remain rollback-safe.

Real build checks are opt-in in the contributor suite with `FILTERX_RUN_WEB_E2E=1`.

## Streaming exports

FastAPI/SQLAlchemy, Express/Prisma, and Spring Boot/JPA expose the same endpoint:

```text
POST /api/filterx/{entity}/export?format=csv|xlsx|json&sort_by=...&order=...&search=...
```

The request body carries the current `filter_tree` or flat `filters`. Exports iterate through all matching rows in bounded batches; the browser does not first materialize the complete result set. CSV uses a UTF-8 BOM and CRLF records, JSON is streamed as an array, and XLSX uses spooled/streaming workbook output. Export requests pass through the normal query-cost, row-predicate, permission, and field-visibility pipelines using the `export` action, so hidden rows and fields are never restored by changing format.

Real backend parity checks are opt-in with `FILTERX_RUN_NODE_E2E=1` and `FILTERX_RUN_JAVA_E2E=1`.

## Are anchors mandatory?

Anchors are mandatory only for enabled patch operations.
If an enabled operation expects an anchor and it is missing, installation is blocked in strict mode.

Anchor defaults:

- backend mount: # FILTERX:ROUTER_MOUNT
- frontend routes: // FILTERX:ROUTES
- frontend providers: // FILTERX:PROVIDERS

## Command map

- filterx scan: discovers entities/routes and writes .filterx artifacts
- filterx install: runs scan, enabled installs, then validate
- filterx validate: checks generated integration health
- filterx rollback: restores files using patch bundle backups

Layer-specific commands:

- filterx backend install|validate
- filterx frontend install|validate|remove
- filterx db install|validate

## Common errors and fixes

- SCAN_FILE_MISSING
  Fix: run install or scan with writes enabled first.

- ANCHOR_NOT_FOUND
  Fix: add the configured anchor in the configured host file.

- Route conflict on /api/filterx/metadata
  Fix: change backend.api_prefix or remove the conflicting route.

## Safety and rollback

FilterX stores operational state in .filterx:

- scan.json, plan.json, diagnostics.json
- manifest.json for idempotency and file hashes
- patches folder for rollback metadata and backups

Rollback commands:

```powershell
filterx rollback --project-root . --config filterx.yaml --list
filterx rollback --project-root . --config filterx.yaml
filterx rollback --project-root . --config filterx.yaml --patch-id <id>
```
