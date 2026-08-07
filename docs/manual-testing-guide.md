# FilterX Manual Testing Guide

> **Source of truth**: this document is derived strictly from the current source
> tree under `tools/filterx/filterx/` (renderers, scanners, commands, core
> config) and from the existing test suite under `tools/filterx/tests/`. It does
> **not** rely on `README.md` (which still describes the FastAPI+Angular flow
> only) or on `filterx-multibackend-spec.md` (which is the original
> design proposal — not the implementation). Where the implementation deviates
> from the spec, that is flagged in **DEVIATIONS** notes.

---

## Table of contents

1. [Phase 1 inventory — what actually exists](#phase-1-inventory--what-actually-exists)
   - 1.1 [Supported backends](#11-supported-backends)
   - 1.2 [Supported frontends](#12-supported-frontends)
   - 1.3 [Supported combinations](#13-supported-combinations)
   - 1.4 [The `filterx.yaml` schema (every option that affects the chosen combination)](#14-the-filterxyaml-schema-every-option-that-affects-the-chosen-combination)
   - 1.5 [Required host-file anchors per target](#15-required-host-file-anchors-per-target)
   - 1.6 [Toolchain prerequisites per target](#16-toolchain-prerequisites-per-target)
   - 1.7 [CLI surface as it actually behaves today](#17-cli-surface-as-it-actually-behaves-today)
2. [Global prerequisites for every combination](#global-prerequisites-for-every-combination)
3. [Per-combination testing sections](#per-combination-testing-sections)
   - 3.1 [FastAPI + Angular](#31-fastapi--angular)
   - 3.2 [FastAPI + React (Vite)](#32-fastapi--react-vite)
   - 3.3 [FastAPI + Next.js](#33-fastapi--nextjs)
   - 3.4 [FastAPI + Vue](#34-fastapi--vue)
   - 3.5 [Express + Prisma + Angular](#35-express--prisma--angular)
   - 3.6 [Express + Prisma + React (Vite)](#36-express--prisma--react-vite)
   - 3.7 [Express + Prisma + Next.js](#37-express--prisma--nextjs)
   - 3.8 [Express + Prisma + Vue](#38-express--prisma--vue)
   - 3.9 [Spring Boot JPA + Angular](#39-spring-boot-jpa--angular)
   - 3.10 [Spring Boot JPA + React (Vite)](#310-spring-boot-jpa--react-vite)
   - 3.11 [Spring Boot JPA + Next.js](#311-spring-boot-jpa--nextjs)
   - 3.12 [Spring Boot JPA + Vue](#312-spring-boot-jpa--vue)
4. [Cross-combination parity check (manual)](#cross-combination-parity-check-manual)
5. [Known gaps and partial support](#known-gaps-and-partial-support)
6. [Appendix A — endpoints every backend exposes](#appendix-a--endpoints-every-backend-exposes)
7. [Appendix B — filter operators supported by every backend](#appendix-b--filter-operators-supported-by-every-backend)

---

## Phase 1 inventory — what actually exists

### 1.1 Supported backends

From `tools/filterx/filterx/renderers/__init__.py` (verified by reading the
file — there are exactly three `BACKEND` renderers registered):

| `backend.framework` value | Renderer class              | Implementation file                                         | Host language / runtime                  |
| ------------------------- | --------------------------- | ----------------------------------------------------------- | ---------------------------------------- |
| `fastapi-sqlalchemy`      | `FastAPISQLAlchemyRenderer` | `renderers/builtin.py` (delegates to `commands/backend.py`) | Python ≥ 3.10, FastAPI, SQLAlchemy       |
| `express-prisma`          | `ExpressPrismaRenderer`     | `renderers/express_prisma.py`                               | Node.js ≥ 18, Express 5, Prisma 6        |
| `spring-boot-jpa`         | `SpringBootJPARenderer`     | `renderers/spring_boot_jpa.py`                              | JDK 21, Spring Boot 3.4.x, JPA/Hibernate |

> **DEVIATION from the spec**: the spec (`filterx-multibackend-spec.md`)
> mentions FastAPI, Express, and Spring Boot. The implementation matches
> those three and does not include a Go/Gin or .NET target the spec
> hinted at as possible future work. The renderer registration list is
> the single source of truth — if a value is not in the table above,
> the CLI will reject it with `BACKEND_RENDERER_NOT_REGISTERED`.

### 1.2 Supported frontends

From the same `renderers/__init__.py` (one `BACKEND` `angular` and three
`FRONTEND` web targets):

| `frontend.framework` value | Renderer class      | Implementation file                                          | Host language / runtime                       | Generated `FilterxApp` entry component                                                      |
| -------------------------- | ------------------- | ------------------------------------------------------------ | --------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `angular`                  | `AngularRenderer`   | `renderers/builtin.py` (delegates to `commands/frontend.py`) | TypeScript, Angular ≥ 17 (PrimeNG UI runtime) | standalone component, mounted through route + `provideFilterx`                              |
| `react-vite`               | `ReactViteRenderer` | `renderers/web_frontends.py`                                 | React 19, Vite 6, TypeScript 5.7              | `FilterxApp.tsx` mounted in host `src/App.tsx`                                              |
| `nextjs`                   | `NextjsRenderer`    | `renderers/web_frontends.py`                                 | Next.js 15 (app router), React 19, TS 5.7     | `FilterxApp.tsx` exposed via generated `src/app/filterx/page.tsx` (no host file is patched) |
| `vue`                      | `VueRenderer`       | `renderers/web_frontends.py`                                 | Vue 3.5, Vite 6, TypeScript 5.7, vue-tsc 2.2  | `FilterxApp.vue` + `FilterxFilterBuilder.vue` mounted in host `src/App.vue`                 |

> **DEVIATION from the spec**: the spec talks about "React" as if it were
> one thing. The implementation distinguishes `react-vite` (a standalone
> Vite SPA) from `nextjs` (App-Router). The old `frontend.framework: react`
> value does **not** exist; an unknown value triggers
> `FRONTEND_RENDERER_NOT_REGISTERED` and the help output lists the three
> real names (`test_web_frontend_renderers.py::test_unknown_frontend_renderer_lists_new_targets`).

### 1.3 Supported combinations

The renderer registry does not gate combinations — the backend and frontend
pipelines are independent. Any of the 3 × 4 = 12 pairs is wired up and the
test suite exercises every one of them. The combinations below are the
canonical ones the test suite (and the source itself) call out:

- FastAPI + Angular (the original)
- FastAPI + React (Vite)
- FastAPI + Next.js
- FastAPI + Vue
- Express + Prisma + Angular
- Express + Prisma + React (Vite)
- Express + Prisma + Next.js
- Express + Prisma + Vue
- Spring Boot JPA + Angular
- Spring Boot JPA + React (Vite)
- Spring Boot JPA + Next.js
- Spring Boot JPA + Vue

There is no cross-validation in the registry. If the backend is set to
`express-prisma` and the frontend to `angular`, the install will simply
generate a `frontend/src/app/filterx-generated/*` Angular UI that talks
to whatever URL the user has configured. The user is responsible for
ensuring the dev proxy / Next rewrites / Spring CORS line up — FilterX
does not enforce this.

### 1.4 The `filterx.yaml` schema (every option that affects the chosen combination)

Top-level keys are **mandatory** (see `core/config.py::_validate`):

```
version: 1                  # must be the integer 1
project: {name, root, backend_root, frontend_root, alembic_ini}
python:   {app_import, base_class_import, models_package, session_dependency_import, sqlalchemy_url_env}
backend:  {enabled, framework, ...}    # see below
frontend: {enabled, framework, ...}    # see below
database: {enabled, provider, migration_dir, features}
scan:     {framework, emit_ir, timeout_seconds, prisma, jpa, max_relationship_depth, include_views, include_hybrid_properties, respect_soft_delete}
safety:   {dry_run_default, require_anchor_comments, idempotency_manifest, allow_overwrite_generated, strict_conflict_mode}
output:   {scan_file, ir_file, plan_file, diagnostics_file, patch_dir}
```

The keys whose value actually depends on which `backend.framework` /
`frontend.framework` you pick:

**Backend — `fastapi-sqlalchemy`** (used by `commands/backend.py`):

```yaml
backend:
  enabled: true
  framework: fastapi-sqlalchemy
  api_prefix: /api # becomes /api/filterx
  generated_package: app/filterx_generated # relative to project root
  mount_file: app/main.py # must contain mount_anchor
  mount_anchor: "# FILTERX:ROUTER_MOUNT"
  entities: [] # optional allowlist (CLI: --entities)
  exclude_entities: [] # optional denylist (CLI: --exclude-entities)
  auth_dependency_import: null # module:object or null
  permission_hook_import: null
  field_visibility_hook_import: null
  global_predicate_hooks: [] # list of module:object paths
  entity_predicate_hooks: {} # {ModelName: [module:object, ...]}
```

**Backend — `express-prisma`** (consumed in `renderers/express_prisma.py`):

```yaml
backend:
  enabled: true
  framework: express-prisma
  api_prefix: /api
  express:
    generated_root: src/filterx-generated
    app_file: src/app.ts # must contain app_anchor
    app_anchor: "// FILTERX:ROUTER_MOUNT"
    package_json: package.json # deps merged here
    tsconfig: tsconfig.json # module=NodeNext triggers .js imports
    hooks_module: null # e.g. "../filterx-hooks.ts" with the three hooks
    rate_limit_per_minute: 120 # hard-codes the express-rate-limit
    max_query_cost: 100 # hard-codes the in-router queryCost() guard
```

**Backend — `spring-boot-jpa`** (consumed in `renderers/spring_boot_jpa.py`):

```yaml
backend:
  enabled: true
  framework: spring-boot-jpa
  api_prefix: /api
  spring:
    module_path: . # used to compute sources
    build_tool: maven # null | "maven" | "gradle"
    maven_command: null # defaults to "mvn" on PATH
    gradle_command: null # defaults to "gradle" on PATH
    source_root: src/main/java
    generated_package: com.example.filterx.generated
    application_class: com.example.FilterxFixtureApplication # required
    pom_file: pom.xml
    gradle_file: null
    use_records: true
    jpa_provider: hibernate
    springdoc_version: 2.8.9
    resilience4j_version: 2.3.0
    poi_version: 5.4.1
    rate_limit_per_minute: 120 # turns into a Resilience4j limiter
    max_query_cost: 100 # enforced in FilterxQueryService
    compile_timeout_seconds: 180
    maven_args: []
    gradle_args: []
```

**Frontend — `angular`** (consumed in `commands/frontend.py`):

```yaml
frontend:
  enabled: true
  framework: angular
  workspace_root: frontend
  generated_root: frontend/src/app/filterx-generated
  routes_file: frontend/src/app/app.routes.ts
  routes_anchor: "// FILTERX:ROUTES"
  app_config_file: frontend/src/app/app.config.ts
  app_config_anchor: "// FILTERX:PROVIDERS"
  entity_style: kebab # kebab | camel | snake
```

**Frontend — `react-vite` / `nextjs` / `vue`** (consumed in
`renderers/web_frontends.py`):

```yaml
frontend:
  enabled: true
  framework: react-vite # or: nextjs | vue
  workspace_root: frontend
  react_vite: # or nextjs / vue
    workspace_root: frontend
    generated_root: src/filterx-generated
    host_file: src/App.tsx # for vue: src/App.vue (default)
    host_anchor: "// FILTERX:APP" # for vue: <!-- FILTERX:APP -->
    api_base_url: /api/filterx
  nextjs:
    workspace_root: frontend
    generated_root: src/filterx-generated
    api_base_url: /api/filterx
    # Next.js: no host_file/host_anchor — the renderer creates
    # frontend/src/app/filterx/page.tsx as the entry route.
  vue:
    workspace_root: frontend
    generated_root: src/filterx-generated
    host_file: src/App.vue
    host_anchor: "<!-- FILTERX:APP -->"
    api_base_url: /api/filterx
```

> **DEVIATION from the spec / README**: the README documents
> `frontend.route_prefix: filterx`. This key is **not** consumed anywhere
> in the current code (`grep -R "route_prefix" tools/filterx/filterx`
> returns no matches in source). If you need to dodge a route collision,
> rename the host routes manually before running `filterx frontend install`
> or use the `frontend.<target>.host_file` to mount the FilterX UI under a
> different component path.

> **DEVIATION from the spec**: the spec mentioned `frontend.framework:
vue` only with an "experimental" tag. The implementation actually
> registers `vue`, `react-vite`, and `nextjs` as first-class renderers
> with the same generation/rollback semantics as `angular`. None of them
> carry an "experimental" flag in source.

### 1.5 Required host-file anchors per target

Anchors are mandatory — without them the renderer returns warnings and
exits 3 (`FRONTEND_ROUTE_ANCHOR_NOT_FOUND`, `BACKEND_MOUNT_ANCHOR_NOT_FOUND`,
`EXPRESS_MOUNT_ANCHOR_MISSING`, etc.). This is enforced by
`safety.strict_conflict_mode: true` (the default).

| Target               | Required file (default)                                                        | Required anchor text                                                                               |
| -------------------- | ------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| FastAPI              | `app/main.py`                                                                  | `# FILTERX:ROUTER_MOUNT`                                                                           |
| Express + Prisma     | `src/app.ts`                                                                   | `// FILTERX:ROUTER_MOUNT`                                                                          |
| Spring Boot JPA      | (none)                                                                         | The generated package must be under the application class's package for Spring component scanning. |
| Angular              | `frontend/src/app/app.routes.ts` _or_ `frontend/src/app/app-routing.module.ts` | `// FILTERX:ROUTES`                                                                                |
| Angular (standalone) | `frontend/src/app/app.config.ts`                                               | `// FILTERX:PROVIDERS`                                                                             |
| React (Vite)         | `frontend/src/App.tsx`                                                         | `// FILTERX:APP`                                                                                   |
| Vue                  | `frontend/src/App.vue`                                                         | `<!-- FILTERX:APP -->`                                                                             |
| Next.js              | (none)                                                                         | Renderer creates `frontend/src/app/filterx/page.tsx` as the entry route.                           |

(\*) The Angular renderer auto-detects which routes file is present; see
`commands/frontend.py::_resolve_routes_file` and
`commands/frontend.py::_resolve_app_config_file`.

### 1.6 Toolchain prerequisites per target

Verified from the scanners and renderers:

| Target               | Tools that MUST already be installed & on PATH before `filterx scan`                                                                                                                                                                                                                                                                    |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| FastAPI + SQLAlchemy | Python ≥ 3.10, the host project's venv (must import your models), `pip`                                                                                                                                                                                                                                                                 |
| Express + Prisma     | Node.js ≥ 18, **npm** (the Prisma scanner shells out to `node reference_runtime/scanners/prisma_scanner.mjs`), and a **generated Prisma client** at `node_modules/.prisma/client/index.js` (set `scan.prisma.allow_stale_client: true` to bypass, but expect downstream errors). `prisma` ≥ 6.0 for `prisma generate`/`prisma db push`. |
| Spring Boot JPA      | JDK 21 (matches `pom.xml` `java.version=21` in the test fixture), **Maven** or **Gradle** on PATH (the JPA scanner compiles a small helper Java class and inspects its bytecode — see `scanners/jpa.py` and `reference_runtime/scanners/FilterxJpaScanner.java`).                                                                       |

| Target           | Tools needed before `filterx backend install`                                                                |
| ---------------- | ------------------------------------------------------------------------------------------------------------ |
| FastAPI          | none beyond `filterx` being installed                                                                        |
| Express + Prisma | the app file must already exist (`src/app.ts` by default) with the anchor comment                            |
| Spring Boot JPA  | Maven or Gradle on PATH (used by `backend validate` to run `mvn -DskipTests compile` / `gradle compileJava`) |

| Target       | Tools needed before `filterx frontend install`                                              |
| ------------ | ------------------------------------------------------------------------------------------- |
| Angular      | `frontend/package.json` must exist (the renderer merges UI deps into it). Node 18+.         |
| React (Vite) | `frontend/package.json`, `frontend/src/App.tsx` with the anchor comment. Node 18+.          |
| Vue          | `frontend/package.json`, `frontend/src/App.vue` with the anchor comment. Node 18+.          |
| Next.js      | `frontend/package.json` and a working `frontend/src/app/` (layout.tsx, page.tsx). Node 18+. |

After install, the user must still run `npm install` themselves in the
frontend workspace (the renderer only edits `package.json`).

### 1.7 CLI surface as it actually behaves today

Verified by reading `cli.py` end-to-end:

```text
filterx --help
  --project-root PATH   (default: ".")
  --config PATH         (default: None)
  --dry-run / --no-dry-run
  --check               (alias for validation mode)
  --json
  --verbose
  --yes
  --fail-on-warning

Subcommands:
  filterx scan --entities "Author,Book" --exclude-entities "SavedFilter" --max-depth 3
  filterx backend install [--mount-file PATH] [--mount-anchor TEXT] [--api-prefix PATH] [--force] [--no-mount]
  filterx backend validate
  filterx backend remove          # stub: use `filterx rollback`
  filterx frontend install [--routes-file PATH] [--routes-anchor TEXT] [--app-config-file PATH] [--app-config-anchor TEXT] [--style kebab|camel|snake] [--force] [--no-route-patch]
  filterx frontend validate
  filterx frontend remove [--list] [--patch-id ID]
  filterx db install [--saved-filters / --no-saved-filters] [--shared-filters / --no-shared-filters] [--auditing / --no-auditing] [--migration-dir PATH] [--name TEXT] [--apply]
  filterx db validate
  filterx install            # orchestrated: scan → backend.install → frontend.install → db.install → validate
  filterx validate           # cross-layer validate
  filterx rollback [--list] [--patch-id ID]
```

Exit codes (consistent across all subcommands):

| Code | Meaning                                                             |
| ---- | ------------------------------------------------------------------- |
| 0    | Success                                                             |
| 2    | Pre-flight failure (missing artifact, bad config, unknown renderer) |
| 3    | Conflict blocked by `strict_conflict_mode` or `--fail-on-warning`   |
| 4    | Validation produced errors                                          |

> **DEVIATION from the README**: the README only documents `filterx scan`,
> `filterx backend install/validate`, `filterx frontend install/validate`,
> `filterx install`, `filterx validate`, and `filterx rollback`. The
> subcommands `filterx db install/validate`, `filterx backend remove`, and
> `filterx frontend remove` exist but are **not** described in README.

---

## Global prerequisites for every combination

1. **Install the FilterX CLI** (editable install for development; pip
   install for the user-facing flow). The test suite uses an editable
   install: `pip install -e tools/filterx`. After that `filterx --help`
   must succeed.

2. **Pick a clean workspace root** (the directory in which you will run
   `filterx scan … --project-root .`). This directory must be the parent
   of both the backend project and the frontend project, **except** for
   the Express backend where the project root IS the backend itself (the
   e2e test creates `tmp_path/express_e2e/{package.json, prisma/, src/, filterx.yaml}`).

3. **Verify tools you need are present** before starting each combination:
   - `python --version` (must be ≥ 3.10)
   - `node --version` (must be ≥ 18 for any frontend or the Express backend)
   - `npm --version`
   - `java -version` and either `mvn -v` **or** `gradle -v` (Spring only)
   - `psql --version` or the equivalent for the database you intend to use

   On Windows, run these from PowerShell:

   ```powershell
   python --version
   node --version
   npm --version
   ```

4. **Initialize `filterx.yaml`** at the workspace root (or at the Express
   project root for Express). The cleanest way is to start from a copy
   of the **default config** the CLI itself emits, which you can obtain
   by `python -c "import json,filterx.core.config as c; print(json.dumps(c.default_config(), indent=2))"`.
   Then edit only the keys relevant to your combination.

5. **Anchor comments** must be present in the host files before
   `install` runs; otherwise you will get `*_ANCHOR_NOT_FOUND` warnings
   and (under `strict_conflict_mode: true`) exit code 3.

---

## Per-combination testing sections

Each section below is independent. It is **strongly recommended** that
you create a fresh temporary directory per section so that prior
artifacts (`package.json` deps, `node_modules/`, generated patches) do
not pollute the next test.

### How to read each section

For every combination, you will see:

1. **Prerequisites** — exact tool/runtime versions and the verification
   commands you can paste.
2. **Fresh scaffold** — the exact files to create, the `filterx.yaml`
   contents for that combination, the host-file anchors, and the
   `filterx scan` step.
3. **Run scan/install/validate** — exact command sequence and how to
   interpret success vs. failure.
4. **Start backend + frontend** — exact run commands, expected ports,
   and how to confirm both are up.
5. **Functional test checklist** — the things to click / curl.
6. **Security checks** — how to manually verify the row-level and
   field-level hooks + the rate limiter / query-cost guard.
7. **Rollback verification** — exact rollback commands and how to
   confirm a clean revert.
8. **Known gaps** — limitations, partial support, or deviations that
   you will hit on this combination.

The exact curl/click URLs use the same `Author/Book` fixture the
test suite uses (e.g. `test_spring_boot_jpa_install.py`). For local
manual testing, you can use your own models; the same endpoint shapes
apply — see [Appendix A](#appendix-a--endpoints-every-backend-exposes).

---

### 3.1 FastAPI + Angular

> This is the original combination. It is the only one whose
> end-to-end flow is covered by `filterx_playwright` tests under
> `frontend/tests-e2e/`.

#### 3.1.1 Prerequisites

- Python ≥ 3.10
- A FastAPI app with SQLAlchemy models that can be imported by name
- A PostgreSQL (or SQLite for dev) with the tables already migrated
- Node.js ≥ 18 and npm
- An Angular ≥ 17 workspace with a `package.json` at the configured
  `frontend.workspace_root`

Verify:

```powershell
python --version                        # 3.10+
node --version                          # 18+
npm --version
```

#### 3.1.2 Fresh scaffold

Layout:

```text
workspace/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── author.py
│   │   │   └── book.py
│   │   └── security.py        # optional, for security hooks
│   ├── pyproject.toml
│   └── alembic/
├── frontend/
│   ├── package.json
│   ├── angular.json
│   └── src/app/{app.routes.ts, app.config.ts, main.ts}
└── filterx.yaml
```

`app/main.py` must end with the anchor (verify line is present):

```python
from fastapi import FastAPI
from app.routers import items  # your existing routers

app = FastAPI()
app.include_router(items.router)

# FILTERX:ROUTER_MOUNT
```

`frontend/src/app/app.routes.ts`:

```ts
import { Routes } from "@angular/router";
export const routes: Routes = [
  // FILTERX:ROUTES
];
```

If your Angular project is standalone (no `AppModule`), add the provider anchor in
`app.config.ts`:

```ts
import { ApplicationConfig, provideZoneChangeDetection } from "@angular/core";
import { provideRouter } from "@angular/router";
import { routes } from "./app.routes";

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    // FILTERX:PROVIDERS
  ],
};
```

`filterx.yaml`:

```yaml
version: 1
project:
  name: my_project
  root: .
  backend_root: backend
  frontend_root: frontend
  alembic_ini: backend/alembic.ini
python:
  app_import: app.main:app
  base_class_import: app.database:Base
  models_package: app.models
  session_dependency_import: app.database:get_db
  sqlalchemy_url_env: DATABASE_URL
backend:
  enabled: true
  framework: fastapi-sqlalchemy
  api_prefix: /api
  generated_package: backend/app/filterx_generated
  mount_file: backend/app/main.py
  mount_anchor: "# FILTERX:ROUTER_MOUNT"
  # Leave these as null unless you want to wire security hooks
  auth_dependency_import: null
  permission_hook_import: null
  field_visibility_hook_import: null
  global_predicate_hooks: []
  entity_predicate_hooks: {}
frontend:
  enabled: true
  framework: angular
  workspace_root: frontend
  generated_root: frontend/src/app/filterx-generated
  routes_file: frontend/src/app/app.routes.ts
  routes_anchor: "// FILTERX:ROUTES"
  app_config_file: frontend/src/app/app.config.ts
  app_config_anchor: "// FILTERX:PROVIDERS"
  entity_style: kebab
database:
  enabled: false
  provider: alembic
  migration_dir: backend/alembic/versions
  features:
    saved_filters: true
    shared_filters: false
    auditing: false
scan:
  framework: sqlalchemy
  emit_ir: false
  max_relationship_depth: 3
  include_views: false
  include_hybrid_properties: false
  respect_soft_delete: true
safety:
  dry_run_default: true
  require_anchor_comments: true
  idempotency_manifest: .filterx/manifest.json
  allow_overwrite_generated: true
  strict_conflict_mode: true
output:
  scan_file: .filterx/scan.json
  ir_file: .filterx/ir.json
  plan_file: .filterx/plan.json
  diagnostics_file: .filterx/diagnostics.json
  patch_dir: .filterx/patches
```

#### 3.1.3 Running scan / install / validate

Activate your Python venv, then from the workspace root:

```powershell
# 1) Scan (writes .filterx/scan.json, .filterx/plan.json, .filterx/diagnostics.json)
filterx scan --project-root . --config filterx.yaml --no-dry-run --json

# Successful output (truncated):
#   "entity_count": N
#   "scan_file": "...\\.filterx\\scan.json"
#   "diagnostics_file": "...\\.filterx\\diagnostics.json"
#   "plan_file": "...\\.filterx\\plan.json"

# 2) Backend install (writes Python package + anchors the router mount)
filterx backend install --project-root . --config filterx.yaml --no-dry-run --yes --json

# Successful output:
#   "patch_id": "...",
#   "selected_entities": ["Author", "Book", ...],
#   "touched_files": [...],
#   "applied_ops": N,
#   "skipped_ops": 0

# 3) Frontend install (writes Angular runtime + per-entity pages + anchors routes/providers)
filterx frontend install --project-root . --config filterx.yaml --no-dry-run --yes --json

# 4) Validate cross-layer
filterx validate --project-root . --config filterx.yaml --json
# Expect: "error_count": 0, "warning_count": 0 (or warnings that are acceptable)
```

**Failure indicators**:

- exit code 2 with `"code": "SCAN_FILE_MISSING"` — you ran install/validate
  before scan.
- exit code 2 with `"code": "ENTITY_SCOPE_RESCAN_REQUIRED"` — you passed
  `--entities` to install but not to scan (or vice versa); re-run scan
  with the same allowlist.
- exit code 3 with `"code": "BACKEND_MOUNT_ANCHOR_NOT_FOUND"` — your
  `app/main.py` is missing the anchor comment.
- exit code 3 with `"code": "FRONTEND_ROUTE_ANCHOR_NOT_FOUND"` or
  `FRONTEND_PROVIDERS_ANCHOR_NOT_FOUND` — the matching anchor is missing
  in the Angular host files.
- exit code 3 with `"code": "FRONTEND_ROUTE_PATH_ALREADY_EXISTS"` — the
  host's `app.routes.ts` already has one of the generated entity paths.
  Either remove them, set `frontend.<target>.host_file` to mount the UI
  elsewhere, or rerun with `--force`.

#### 3.1.4 Starting both

Backend (terminal 1):

```powershell
cd backend
uvicorn app.main:app --reload --port 8000
```

Sanity:

```powershell
curl http://127.0.0.1:8000/api/filterx/metadata
# Expect: a JSON body with "entities": [...] and "entity_count": N
```

Frontend (terminal 2):

```powershell
cd frontend
npm install            # ONE TIME after filterx frontend install, deps were added
npm start              # usually runs `ng serve` on http://localhost:4200
```

Sanity: open <http://localhost:4200>. The home page is whatever your
host app already shows. The generated entity pages live at
`/<kebab-table-name>` (e.g. `/books`, `/authors`).

Confirm the dev proxy is wired: the CLI wrote `frontend/proxy.conf.cjs`
targeting `http://127.0.0.1:8000`, and updated `angular.json` so that
`serve.options.proxyConfig = "proxy.conf.cjs"`. After `npm start`,
browser requests to `/api/...` from the SPA should be proxied to the
FastAPI app.

#### 3.1.5 Functional test checklist

For the `Author` / `Book` fixture (or your own entities):

- [ ] `GET /api/filterx/metadata` returns the list of entities.
- [ ] `GET /api/filterx/{entity}/metadata` returns a single entity.
- [ ] `GET /api/filterx/{entity}?size=5&page=1` paginates.
- [ ] `GET /api/filterx/{entity}?name_eq=Ada` filters by equality.
- [ ] `GET /api/filterx/{entity}?name_ilike=%25ada%25` filters with
      `ilike` (case-insensitive contains).
- [ ] `GET /api/filterx/{entity}?price_gte=10&price_lte=50` combines
      two predicates with AND.
- [ ] `GET /api/filterx/{entity}?genre_in=Tech,Fiction` uses the `in`
      operator.
- [ ] `GET /api/filterx/{entity}?note_is_null=true` filters nulls.
- [ ] `GET /api/filterx/{entity}?sort_by=title&order=desc` sorts.
- [ ] `GET /api/filterx/{entity}?search=alpha` runs the global text
      search across all string/enum fields.
- [ ] `POST /api/filterx/{entity}/filter` with a `filter_tree` body
      containing a nested AND/OR group (this is what the Angular
      `filter-builder` component sends).
- [ ] `GET /api/filterx/{entity}/group-by/{field}` returns the
      `[{key, count}, ...]` buckets.
- [ ] `POST /api/filterx/{entity}/group-by/{field}/filter` applies a
      filter to the group-by.
- [ ] `POST /api/filterx/{entity}/export?format=csv` (or `xlsx`/`json`)
      downloads an export.
- [ ] Open the Angular page in the browser; the URL `/books` should
      show a search box, sort headers, page-size selector, group-by
      selector, and the filter-builder drawer.
- [ ] Add a custom filter (e.g. `price > 20`) and confirm the URL
      reflects the new state and the table updates.

#### 3.1.6 Security checks

> Security hooks are **opt-in**. Out of the box, the CLI generates
> a no-op `predicates.py`, no `permission_hook`, and no
> `field_visibility_hook`. To exercise this, you must implement the
> hooks in your host project and reference them in `filterx.yaml`.

To verify row-level and field-level enforcement:

1. Implement hooks in `backend/app/security.py`:

   ```python
   from fastapi import Header
   from sqlalchemy import Column

   def get_principal(x_genre: str = Header(...)):
       return x_genre

   def row_predicate(*, principal, request, entity, model, action):
       if entity.get("model") == "Book":
           return model.genre == principal
       return None

   def field_visible(*, principal, request, entity, field, action):
       return field != "price"
   ```

2. Reference them in `filterx.yaml`:

   ```yaml
   backend:
     auth_dependency_import: app.security:get_principal
     global_predicate_hooks: ["app.security:row_predicate"]
     field_visibility_hook_import: app.security:field_visible
   ```

3. Re-run `filterx backend install --no-dry-run --yes --json`.

4. Then with the backend running:

   ```powershell
   # Without x-genre header: 401 (because get_principal requires Header(...))
   curl -i http://127.0.0.1:8000/api/filterx/books

   # With x-genre=Tech: only Tech books, and "price" field is hidden
   curl -H "x-genre: Tech" http://127.0.0.1:8000/api/filterx/books
   # Expect: data[*] does not contain "price"; data[*]["genre"] == "Tech"
   ```

The rate limiter / query-cost guard for the **FastAPI** backend is
**not** built in. The Express backend has a `RATE_LIMITED` response
(`429`) and a `QUERY_COST_EXCEEDED` (`400`) error; the FastAPI one
does not. If you need these on FastAPI, write a Starlette middleware
or upstream rate-limiter. The CLI does not generate one for you.

#### 3.1.7 Rollback verification

```powershell
# List available patch bundles
filterx rollback --project-root . --config filterx.yaml --list

# Roll back the most recent bundle (or pass --patch-id <id>)
filterx rollback --project-root . --config filterx.yaml
```

Successful rollback (per `commands/rollback.py`):

- The `backend/app/filterx_generated/` directory is removed.
- The `# FILTERX:ROUTER_MOUNT` snippet added to `app/main.py` is
  reverted to the original file.
- The `frontend/src/app/filterx-generated/` directory is removed.
- The Angular `app.routes.ts` and `app.config.ts` are restored from
  the manifest snapshot.
- `frontend/package.json` deps added by FilterX are removed.
- `frontend/proxy.conf.cjs` is removed (if FilterX created it).

Confirm by `git status` (or a tree diff against a fresh clone):
nothing outside the `frontend/src/app/filterx-generated` and
`backend/app/filterx_generated` directories should have been
touched, and after rollback the project is identical to its
pre-install state.

#### 3.1.8 Known gaps for this combination

- **No built-in rate limiter** for FastAPI (only Express and Spring
  ship one). If you need it, add a Starlette / FastAPI middleware
  yourself.
- **Field visibility hook is off by default**. The generated
  `entities.py` carries a `related_fields` array even when no
  `field_visible` hook is registered, but `_serialize_row` will not
  actually call the hook unless `field_visibility_hook_import` is
  set. To opt in, see §3.1.6.
- **`route_prefix` is documented in the README but is not honored by
  the current source** (DEVIATION flagged in §1.4). If you need to
  mount the Angular UI under `/filterx/...`, either set the host's
  router `path` accordingly yourself or use the
  `frontend.<target>.host_file` switch (Angular reuses the `angular`
  config keys, not the per-target ones, so for Angular specifically
  you would have to alter the route entries by hand).

---

### 3.2 FastAPI + React (Vite)

#### 3.2.1 Prerequisites

- Python ≥ 3.10 (same as 3.1.1)
- Node.js ≥ 18, npm ≥ 9
- A React + Vite + TypeScript project with:
  - `frontend/package.json` containing `"type": "module"` and a
    `dev` script (the renderer only edits deps; the host scripts
    are preserved)
  - `frontend/src/App.tsx` (default host file)
  - `frontend/src/main.tsx` mounting `<App />`

Verify:

```powershell
python --version
node --version
npm --version
```

#### 3.2.2 Fresh scaffold

Same backend layout as 3.1.2. The frontend becomes a Vite SPA:

```text
frontend/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── index.html
└── src/
    ├── main.tsx
    └── App.tsx
```

`frontend/src/App.tsx` MUST contain the anchor (default):

```tsx
export default function App() {
  return <main>// FILTERX:APP</main>;
}
```

`filterx.yaml` differs only in `frontend`:

```yaml
version: 1
# ... (project / python / backend / database / scan / safety / output
#      as in §3.1.2)

frontend:
  enabled: true
  framework: react-vite
  workspace_root: frontend
  # Top-level frontend.react_vite is the actual block the renderer reads:
  react_vite:
    workspace_root: frontend
    generated_root: src/filterx-generated
    host_file: src/App.tsx
    host_anchor: "// FILTERX:APP"
    api_base_url: /api/filterx
```

#### 3.2.3 Running scan / install / validate

Same sequence as 3.1.3, but you can run `filterx install` (the
orchestrator) since both backend and frontend are enabled:

```powershell
filterx install --project-root . --config filterx.yaml --no-dry-run --yes --json
```

Successful JSON payload from `frontend install` includes:

```json
{
  "framework": "react-vite",
  "patch_id": "...",
  "generated_root": "...\\frontend\\src\\filterx-generated",
  "entity_count": N,
  "touched_files": ["frontend/src/App.tsx", "frontend/src/filterx-generated/FilterxApp.tsx", ...]
}
```

**Failure indicators**:

- exit code 2 with `"code": "FRONTEND_TARGET_INVALID"` and the message
  starting with `"react-vite package manifest not found: ..."` —
  the renderer could not find `frontend/package.json`.
- exit code 2 with `"code": "FRONTEND_RENDERER_NOT_REGISTERED"` — you
  set `frontend.framework: react` instead of `react-vite` (the spec
  did not survive into the implementation).

#### 3.2.4 Starting both

Backend (terminal 1) — same as 3.1.4:

```powershell
cd backend
uvicorn app.main:app --reload --port 8000
```

Frontend (terminal 2):

```powershell
cd frontend
npm install         # one-time
npm run dev         # Vite dev server, default port 5173
```

Sanity:

- Open <http://127.0.0.1:5173> — you should see the FilterX shell
  with a top nav listing each generated entity.
- In the browser DevTools network panel, every `/api/...` call should
  go to `http://127.0.0.1:5173/api/...` and Vite should proxy it to
  `http://127.0.0.1:8000/api/...`. **Verify this for yourself**: the
  generated `api.ts` uses `api_base_url` (`/api/filterx` by default),
  so it relies on the Vite dev proxy being configured. FilterX does
  **not** edit `vite.config.ts` to add the proxy for you; you must
  add the proxy yourself:

  ```ts
  // vite.config.ts
  import { defineConfig } from "vite";
  import react from "@vitejs/plugin-react";

  export default defineConfig({
    plugins: [react()],
    server: {
      proxy: {
        "/api": "http://127.0.0.1:8000",
      },
    },
  });
  ```

  > **DEVIATION**: the Angular renderer creates `proxy.conf.cjs` and
  > updates `angular.json` for you. The Vite/Next.js/Vue renderers
  > do **not** touch your dev-server config. You have to wire the
  > proxy yourself.

#### 3.2.5 Functional test checklist

Same endpoints as 3.1.5. In the UI, the generated `FilterxApp.tsx`
provides:

- A top nav with one button per entity.
- A search box bound to `state.search`.
- A `Group by…` select listing every entity field.
- A custom filter builder with `+ condition`, `+ group`, an AND/OR
  toggle, and per-condition field / operation / value inputs.
- A `<table>` whose column headers are click-to-sort.
- Pagination (Previous / Next, page numbers, page size select).
- `CSV` / `Excel` / `JSON` export buttons.

#### 3.2.6 Security checks

Same approach as 3.1.6: implement hooks in `backend/app/security.py`,
reference them in `filterx.yaml`, re-run `filterx backend install`,
then curl with and without the `x-genre` header.

The Express-style rate-limit (`429 RATE_LIMITED`) and the in-router
query-cost guard are **not** part of the FastAPI backend. The Vite
dev server will return whatever your upstream returns, so if you
proxy through a rate-limiter, the React UI will just see the 4xx.

#### 3.2.7 Rollback verification

```powershell
filterx rollback --project-root . --config filterx.yaml
# or
filterx frontend remove --project-root . --config filterx.yaml --list
filterx frontend remove --project-root . --config filterx.yaml --patch-id <id>
```

`frontend remove` for `react-vite` calls `rollback_patch_bundle()`
for the most recent `frontend.install.react-vite` bundle. After
removal:

- `frontend/src/filterx-generated/` is gone.
- `frontend/src/App.tsx` is restored to its pre-install content
  (i.e. the `<FilterxApp />` line and the import are removed).
- `frontend/package.json` is restored to its pre-install content
  (the merged `react`, `react-dom`, `vite`, etc. are removed).

#### 3.2.8 Known gaps

- **The renderer does not configure your Vite dev proxy.** Add the
  `server.proxy` block in `vite.config.ts` yourself, or the SPA
  will hit the Vite origin and 404.
- **No scaffold generator.** Unlike the Angular renderer (which
  copies a large reference runtime under `src/app/core/**` and
  `src/app/shared/**`), the React renderer only writes files into
  `src/filterx-generated/`. You bring your own `App.tsx`, `main.tsx`,
  and `index.html`.
- **No Angular Material / PrimeNG equivalent is wired.** The
  generated `FilterxApp.tsx` ships with hand-rolled CSS in
  `filterx.css`. If you want a UI library (e.g. Mantine, shadcn/ui),
  add it yourself.

---

### 3.3 FastAPI + Next.js

#### 3.3.1 Prerequisites

- Python ≥ 3.10
- Node.js ≥ 18, npm ≥ 9
- A Next.js ≥ 15 project with the **App Router** (the renderer
  writes to `frontend/src/app/filterx/page.tsx`, so the
  `frontend/src/app/` directory must exist)
- `frontend/package.json` with `"scripts": {"build": "next build"}`
  or equivalent

Verify:

```powershell
python --version
node --version
npm --version
```

#### 3.3.2 Fresh scaffold

Same backend as 3.1.2. Frontend:

```text
frontend/
├── package.json
├── tsconfig.json
├── next.config.ts
├── next-env.d.ts
└── src/
    └── app/
        ├── layout.tsx
        └── page.tsx
```

`filterx.yaml`:

```yaml
version: 1
# ... (project / python / backend / database / scan / safety / output
#      as in §3.1.2)

frontend:
  enabled: true
  framework: nextjs
  workspace_root: frontend
  nextjs:
    workspace_root: frontend
    generated_root: src/filterx-generated
    api_base_url: /api/filterx
```

> **No host anchor is required.** The renderer creates a new
> Next.js page at `src/app/filterx/page.tsx`. It does **not** touch
> `layout.tsx` or your home `page.tsx`.

#### 3.3.3 Running scan / install / validate

```powershell
filterx install --project-root . --config filterx.yaml --no-dry-run --yes --json
```

After install, `frontend/src/filterx-generated/` should contain:
`FilterxApp.tsx`, `index.ts`, `types.ts`, `entities.ts`, `api.ts`,
`filterx.css`. Additionally `frontend/src/app/filterx/page.tsx`
should exist with:

```tsx
import { FilterxApp } from "../../filterx-generated/FilterxApp";
export default function FilterxPage() {
  return <FilterxApp />;
}
```

#### 3.3.4 Starting both

Backend (terminal 1):

```powershell
cd backend
uvicorn app.main:app --reload --port 8000
```

Frontend (terminal 2):

```powershell
cd frontend
npm install
npm run dev         # Next.js dev server, default port 3000
```

Sanity:

- Open <http://127.0.0.1:3000/filterx>. The FilterX UI should render.
- Open <http://127.0.0.1:3000/>. Your existing home page should be
  untouched.

**Routing the API to the backend in dev**: the generated `api.ts`
uses `api_base_url` (default `/api/filterx`) and does a plain
`fetch()`. In a Next.js dev server, you need to set up `rewrites()`
in `next.config.ts` so that `/api/*` is forwarded to your FastAPI
app. FilterX does **not** write this for you — add it yourself:

```ts
// next.config.ts
import type { NextConfig } from "next";
const config: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/api/:path*",
      },
    ];
  },
};
export default config;
```

#### 3.3.5 Functional test checklist

Same as 3.2.5; the generated `FilterxApp.tsx` is identical between
the React/Vite and Next.js renderers (the only difference is the
`'use client';` directive that the Next.js renderer prepends).

#### 3.3.6 Security checks

Same as 3.1.6 / 3.2.6. The Next.js page is a client component
under `'use client';`, so the request goes directly to your API
rewrite target. CORS does not apply because the rewrite preserves
the same origin.

#### 3.3.7 Rollback verification

```powershell
filterx frontend remove --project-root . --config filterx.yaml
```

After removal:

- `frontend/src/filterx-generated/` is gone.
- `frontend/src/app/filterx/page.tsx` is gone.
- `frontend/package.json` is restored to its pre-install content
  (added `next`, `react`, `react-dom` are removed).
- `frontend/next.config.ts` is **not** touched (and so any rewrites
  you added manually are preserved).

#### 3.3.8 Known gaps

- **The renderer does not touch `next.config.ts`.** You have to add
  `rewrites()` yourself.
- **No host page patching.** The renderer creates a new
  `/filterx` page; it does not embed the FilterX UI in your existing
  home page. To make the home page link to it, edit
  `frontend/src/app/page.tsx` yourself.
- **Server components**: the generated `FilterxApp.tsx` is a client
  component (`'use client';`). If you have a strict RSC-only project,
  this is something you have to refactor.

---

### 3.4 FastAPI + Vue

#### 3.4.1 Prerequisites

- Python ≥ 3.10
- Node.js ≥ 18, npm ≥ 9
- A Vue 3 + Vite + TypeScript project with:
  - `frontend/package.json` containing `"type": "module"` and a
    `build` script (e.g. `"build": "vue-tsc -b && vite build"`)
  - `frontend/src/App.vue` with the anchor
  - `frontend/src/main.ts` calling `createApp(App).mount('#app')`

Verify:

```powershell
python --version
node --version
npm --version
```

#### 3.4.2 Fresh scaffold

Same backend as 3.1.2. Frontend:

```text
frontend/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── index.html
└── src/
    ├── main.ts
    ├── env.d.ts
    └── App.vue
```

`App.vue` must contain the anchor:

```vue
<script setup lang="ts">
const host = true;
</script>
<template>
  <!-- FILTERX:APP -->
</template>
```

`filterx.yaml`:

```yaml
version: 1
# ... (project / python / backend / database / scan / safety / output
#      as in §3.1.2)

frontend:
  enabled: true
  framework: vue
  workspace_root: frontend
  vue:
    workspace_root: frontend
    generated_root: src/filterx-generated
    host_file: src/App.vue
    host_anchor: "<!-- FILTERX:APP -->"
    api_base_url: /api/filterx
```

#### 3.4.3 Running scan / install / validate

```powershell
filterx install --project-root . --config filterx.yaml --no-dry-run --yes --json
```

After install, `frontend/src/filterx-generated/` should contain:
`FilterxApp.vue`, `FilterxFilterBuilder.vue`, `index.ts`, `types.ts`,
`entities.ts`, `api.ts`, `filterx.css`.

The renderer also adds the import line `import FilterxApp from
'./filterx-generated/FilterxApp.vue';` inside the `<script setup>`
block of `App.vue`, and replaces the anchor with `<FilterxApp />`.

**Failure indicators**:

- exit code 2 with `"code": "FRONTEND_TARGET_INVALID"`, message
  starts with `"vue package manifest not found: ..."`.
- The `App.vue` parser can't find a `<script setup>` block — the
  renderer will create one for you (it prepends an entire
  `<script setup lang="ts">…</script>`), but you should then review
  the diff carefully.

#### 3.4.4 Starting both

Backend (terminal 1): same as 3.1.4.

Frontend (terminal 2):

```powershell
cd frontend
npm install
npm run dev         # Vite dev server, default port 5173
```

Same Vite proxy gotcha as 3.2.4: add the `server.proxy` block in
`vite.config.ts` to forward `/api` to `http://127.0.0.1:8000`.

#### 3.4.5 Functional test checklist

Same as 3.2.5. Differences specific to the Vue renderer:

- The FilterX UI is in `FilterxApp.vue` and the nested
  `FilterxFilterBuilder.vue` (the Vue equivalent of the React
  FilterBuilder).
- The custom-filter tree is `v-model`-bound; the Apply button
  copies the tree into `state.filterTree` and triggers a fetch.
- Sort/group/pagination are wired with `v-for` and `@click` on
  the table headers.

#### 3.4.6 Security checks

Same as 3.1.6 / 3.2.6.

#### 3.4.7 Rollback verification

```powershell
filterx frontend remove --project-root . --config filterx.yaml
```

After removal: `frontend/src/filterx-generated/` is gone,
`frontend/src/App.vue` is restored, `frontend/package.json` is
restored.

#### 3.4.8 Known gaps

- Same as 3.2.8: the Vite dev proxy is not configured for you.
- The Vue renderer's bundled CSS (`filterx.css`) is shared with
  React; if your Vue project already has a global stylesheet, watch
  out for selector collisions.

---

### 3.5 Express + Prisma + Angular

> This is the combination exercised by
> `tests/test_express_prisma_e2e.py`. It is the only non-FastAPI
> backend for which the test suite spins up a real HTTP server.

#### 3.5.1 Prerequisites

- Node.js ≥ 18, npm ≥ 9
- A working Prisma ≥ 6.0 setup with a `prisma/schema.prisma` that
  you can `prisma generate` and `prisma db push` against
- A `package.json` at the project root (the Express backend is
  self-contained — **the project root IS the backend**, not a
  parent of it)
- Python ≥ 3.10 only for running the `filterx` CLI itself

Verify:

```powershell
node --version
npm --version
npx prisma --version       # or: npm ls prisma
python --version
```

#### 3.5.2 Fresh scaffold

```text
express-e2e/
├── package.json
├── tsconfig.json
├── prisma/
│   └── schema.prisma
├── src/
│   ├── app.ts
│   └── filterx-hooks.ts    # you write this for security hooks
└── filterx.yaml
```

Minimum `package.json`:

```json
{
  "name": "express-filterx-fixture",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "dependencies": {
    "@prisma/client": "^6.0.0",
    "express": "^5.0.0"
  },
  "devDependencies": {
    "prisma": "^6.0.0",
    "typescript": "^5.7.0"
  }
}
```

Minimum `tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "esModuleInterop": true,
    "outDir": "dist"
  },
  "include": ["src/**/*.ts"]
}
```

`src/app.ts` must contain the anchor:

```ts
import express from "express";
export const app = express();
app.use(express.json());
// FILTERX:ROUTER_MOUNT
```

`prisma/schema.prisma` (example):

```prisma
generator client {
  provider = "prisma-client-js"
}
datasource db {
  provider = "sqlite"
  url = env("DATABASE_URL")
}
model Author {
  id    Int    @id @default(autoincrement())
  name  String
  books Book[]
}
model Book {
  id        Int     @id @default(autoincrement())
  title     String
  genre     String
  price     Decimal
  note      String?
  authorId  Int
  author    Author  @relation(fields: [authorId], references: [id])
}
```

`filterx.yaml`:

```yaml
version: 1
project:
  name: express_filterx
  root: .
  backend_root: .
  frontend_root: frontend
  alembic_ini: alembic.ini
python:
  app_import: app.main:app
  base_class_import: app.database:Base
  models_package: app.models
  session_dependency_import: app.database:get_db
  sqlalchemy_url_env: DATABASE_URL
backend:
  enabled: true
  framework: express-prisma
  api_prefix: /api
  express:
    generated_root: src/filterx-generated
    app_file: src/app.ts
    app_anchor: "// FILTERX:ROUTER_MOUNT"
    package_json: package.json
    tsconfig: tsconfig.json
    hooks_module: null
    rate_limit_per_minute: 120
    max_query_cost: 100
frontend:
  enabled: true
  framework: angular
  workspace_root: frontend
  generated_root: frontend/src/app/filterx-generated
  routes_file: frontend/src/app/app.routes.ts
  routes_anchor: "// FILTERX:ROUTES"
  app_config_file: frontend/src/app/app.config.ts
  app_config_anchor: "// FILTERX:PROVIDERS"
  entity_style: kebab
database:
  enabled: false
  provider: alembic
  migration_dir: alembic/versions
  features:
    saved_filters: true
    shared_filters: false
    auditing: false
scan:
  framework: prisma
  emit_ir: false
  max_relationship_depth: 3
  include_views: false
  include_hybrid_properties: false
  respect_soft_delete: true
  prisma:
    schema: prisma/schema.prisma
    package_json: package.json
    client_marker: node_modules/.prisma/client/index.js
    node_command: node
    allow_stale_client: false
safety:
  dry_run_default: true
  require_anchor_comments: true
  idempotency_manifest: .filterx/manifest.json
  allow_overwrite_generated: true
  strict_conflict_mode: true
output:
  scan_file: .filterx/scan.json
  ir_file: .filterx/ir.json
  plan_file: .filterx/plan.json
  diagnostics_file: .filterx/diagnostics.json
  patch_dir: .filterx/patches
```

> **DEVIATION**: with `scan.framework: prisma`, the scan emits BOTH
> `.filterx/scan.json` and `.filterx/ir.json` (the IR is mandatory
> for the new renderers). See `commands/scan.py` line 57:
> `emit_ir = bool(cfg["scan"].get("emit_ir", False)) or
 str(cfg["scan"].get("framework", "sqlalchemy")) != "sqlalchemy"`.

#### 3.5.3 Running scan / install / validate

The Express + Prisma scan **requires a generated Prisma client**
to exist on disk before it can run. So:

```powershell
# 1) Install host deps so node_modules/.prisma/client/index.js exists
npm install --ignore-scripts --no-audit --no-fund
npx prisma generate
npx prisma db push --skip-generate      # actually create the tables

# 2) Scan (uses the Prisma scanner reference runtime
#    reference_runtime/scanners/prisma_scanner.mjs via `node`)
filterx scan --project-root . --config filterx.yaml --no-dry-run --json
# Expect: "entity_count": 2 (Author, Book), and an ir_file key

# 3) Backend install
filterx backend install --project-root . --config filterx.yaml --no-dry-run --yes --json
# Expect: src/filterx-generated/{types,metadata,validation,query,security,router,index}.ts created
# Expect: src/app.ts now contains
#         "import { filterxRouter } from './filterx-generated/index.js';"
#         "app.use('/api/filterx', filterxRouter);"
# Expect: package.json gained helmet, zod, exceljs, express-rate-limit, pino, pino-http

# 4) Frontend install
filterx frontend install --project-root . --config filterx.yaml --no-dry-run --yes --json
# Expect: frontend/src/app/filterx-generated/* created, app.routes.ts has FilterX routes, app.config.ts has providers

# 5) Validate
filterx validate --project-root . --config filterx.yaml --json
```

**Failure indicators**:

- `npm install` must come BEFORE `filterx scan`. If
  `node_modules/.prisma/client/index.js` does not exist, the scan
  fails with `PRISMA_CLIENT_MISSING`. To bypass for inspection only,
  set `scan.prisma.allow_stale_client: true`.
- If `prisma/schema.prisma` is newer than the generated client, the
  scan fails with `PRISMA_CLIENT_STALE`. Re-run `npx prisma generate`.
- exit code 2 with `"code": "EXPRESS_CONFIGURATION_INVALID"` and a
  message about "Multiple Express application entry files" — your
  project has both `src/app.ts` and `src/server.ts`; set
  `backend.express.app_file` explicitly.
- exit code 2 with `"code": "EXPRESS_CONFIGURATION_INVALID"` and a
  message about "Prisma schema was not found" — set
  `scan.prisma.schema` correctly.

#### 3.5.4 Starting both

Compile and start the backend:

```powershell
# Compile TypeScript (the renderer emits ESM with .js import suffixes
# when module=NodeNext in tsconfig)
npx tsc

# Seed your data (the e2e test uses a seed.mjs that calls
# prisma.book.deleteMany() and prisma.author.create(...))
node seed.mjs

# Run your server
node dist/server.js   # or however your host wraps `app`
```

Default port: the test uses `server.listen(0, '127.0.0.1', ...)` and
prints `LISTENING:<port>` to stdout. For a real app, use a fixed port
(e.g. 3000) and set `app.listen(3000)`.

Sanity:

```powershell
curl http://127.0.0.1:3000/api/filterx/metadata
```

Frontend (terminal 2): same as 3.1.4 — `cd frontend && npm install && npm start`.

The Angular dev server proxies `/api/*` to the Express server via
`frontend/proxy.conf.cjs` (which FilterX writes for you). Update the
proxy target from `http://127.0.0.1:8000` to `http://127.0.0.1:3000`
if you run Express on a different port than 8000.

#### 3.5.5 Functional test checklist

Same endpoints as 3.1.5, except:

- There is no FastAPI, so the URL prefix is still `/api/filterx/...`
  (set via `backend.api_prefix`).
- Export streaming uses `ExcelJS` for `.xlsx` and a manual CSV writer
  for `.csv`.
- The "group by a relationship field" is **rejected** — the
  Express renderer raises `GROUP_FIELD_UNSUPPORTED` if the group
  field contains a dot. This is a documented limitation, see
  `renderers/express_prisma.py` line 546.

#### 3.5.6 Security checks

1. Implement hooks in `src/filterx-hooks.ts`:

   ```ts
   export const hooks = {
     extractIdentity: (request: any) => request.header("x-genre") ?? null,
     rowPredicate: ({ principal, entity }: any) =>
       entity.name === "Book" && principal ? { genre: principal } : {},
     fieldVisible: ({ field }: any) => field !== "price",
   };
   ```

2. Reference the file in `filterx.yaml`:

   ```yaml
   backend:
     express:
       hooks_module: "../filterx-hooks.ts"
   ```

3. Re-run `filterx backend install --no-dry-run --yes`.

4. With the server running:

   ```powershell
   # Without x-genre: rowPredicate returns {} → all books
   curl http://127.0.0.1:3000/api/filterx/books

   # With x-genre=Tech: only Tech books, "price" is hidden
   curl -H "x-genre: Tech" http://127.0.0.1:3000/api/filterx/books
   ```

5. **Rate limit**: in the renderer code, the default is
   `rate_limit_per_minute: 120`. If you set this to e.g. `5` in
   `filterx.yaml` and re-run install, the 6th request within a
   minute will return:

   ```json
   {
     "error": {
       "code": "RATE_LIMITED",
       "message": "Too many FilterX requests; ..."
     }
   }
   ```

   with HTTP status 429. Confirm by `curl` loop.

6. **Query-cost guard**: in the renderer code, the default is
   `max_query_cost: 100`. The `queryCost()` function counts each
   filter as `1 + parts_in_field_path` and adds tree depth. A
   filter tree that exceeds the limit returns:

   ```json
   {
     "error": {
       "code": "QUERY_COST_EXCEEDED",
       "message": "Query cost N exceeds limit M."
     }
   }
   ```

   with HTTP status 400. Set `max_query_cost: 5` in your config to
   make this easy to trigger, then send:

   ```bash
   curl -X POST http://127.0.0.1:3000/api/filterx/books/filter \
        -H "content-type: application/json" \
        -d '{"filter_tree":{"node_type":"operator","operator":"AND","children":[
              {"node_type":"condition","field":"title","operation":"eq","value":"x"},
              {"node_type":"condition","field":"title","operation":"eq","value":"y"},
              {"node_type":"condition","field":"title","operation":"eq","value":"z"},
              {"node_type":"condition","field":"title","operation":"eq","value":"w"},
              {"node_type":"condition","field":"title","operation":"eq","value":"v"},
              {"node_type":"condition","field":"title","operation":"eq","value":"u"},
              {"node_type":"condition","field":"title","operation":"eq","value":"t"}
            ]}}'
   ```

#### 3.5.7 Rollback verification

`filterx backend remove` for the Express backend is a **stub**: it
prints an error telling you to use `filterx rollback` instead. The
correct sequence is:

```powershell
filterx rollback --project-root . --config filterx.yaml --list
# Pick the patch id whose description is "backend.install.express-prisma"
filterx rollback --project-root . --config filterx.yaml --patch-id <id>
```

After rollback:

- `src/filterx-generated/` is gone.
- `src/app.ts` is restored (the `import` and `app.use(...)` lines
  added by FilterX are removed).
- `package.json` is restored to its pre-install state (added
  `helmet`, `zod`, `exceljs`, `express-rate-limit`, `pino`,
  `pino-http` are removed).

#### 3.5.8 Known gaps

- **`backend remove` is a stub.** Use `filterx rollback`.
- **Group-by on a relationship field is not supported** and raises
  `GROUP_FIELD_UNSUPPORTED` (this is intentional — Prisma
  relationship aggregation is not portable). The Angular UI does
  not know this; if you select a relationship field in the
  group-by dropdown, you will see a 400.
- **Sort by a relationship field through a collection** (e.g.
  `books.name` when `books` is one-to-many) raises
  `SORT_FIELD_UNSUPPORTED`.
- **Sort/grouping on a relationship field name is not supported**
  through the IR pipeline. The Express renderer explicitly
  refuses it.
- The **hooks_module is resolved relative to the
  generated `index.ts`** (the `_ts_import` helper in
  `express_prisma.py`). If your hooks live elsewhere, adjust the
  relative path accordingly.

---

### 3.6 Express + Prisma + React (Vite)

Identical to 3.5 for the backend, and 3.2 for the frontend. The
filterx.yaml differs only in `frontend.framework: react-vite` and
the `frontend.react_vite` block.

Steps to verify:

1. Backend scaffold: as in 3.5.2 (Express + Prisma).
2. Frontend scaffold: as in 3.2.2 (Vite + React), but the
   workspace lives at `frontend/` next to the Express project.
3. Combine: keep `backend.framework: express-prisma` and set
   `frontend.framework: react-vite`. The Vite dev proxy must point
   at the Express port.

Failure indicators: same as 3.5.3 and 3.2.3.

#### 3.6.7 Rollback

Roll back the backend with `filterx rollback --patch-id <id>` (the
Express remove stub still applies). Roll back the frontend with
`filterx frontend remove`.

---

### 3.7 Express + Prisma + Next.js

Identical to 3.5 for the backend, and 3.3 for the frontend. The
filterx.yaml differs only in `frontend.framework: nextjs` and the
`frontend.nextjs` block.

`frontend/next.config.ts` must include a `rewrites()` block that
forwards `/api/:path*` to the Express port (see 3.3.4).

#### 3.7.7 Rollback

Roll back the backend with `filterx rollback --patch-id <id>`.
Roll back the frontend with `filterx frontend remove`.

---

### 3.8 Express + Prisma + Vue

Identical to 3.5 for the backend, and 3.4 for the frontend. The
filterx.yaml differs only in `frontend.framework: vue` and the
`frontend.vue` block.

The Vite dev proxy must point at the Express port.

#### 3.8.7 Rollback

Same as 3.5.7 (backend) and 3.4.7 (frontend).

---

### 3.9 Spring Boot JPA + Angular

> This is the combination exercised by
> `tests/test_spring_boot_jpa_e2e.py` and the unit tests under
> `test_spring_boot_jpa_install.py`. It is the only non-Node, non-Python
> backend.

#### 3.9.1 Prerequisites

- JDK 21 (matches the test fixture `pom.xml` `<java.version>21</java.version>`)
- **Maven** on PATH (`mvn -v`) **or** Gradle on PATH (`gradle -v`).
  The JPA scanner compiles a small helper class and inspects its
  bytecode, so you cannot skip this.
- An existing Spring Boot 3.4.x project that:
  - uses `spring-boot-starter-data-jpa`
  - already has Spring Security on the classpath (the generated
    controller uses `@PreAuthorize`)
  - has at least one `@Entity` class
- Node.js ≥ 18, npm ≥ 9 (for the Angular frontend)

Verify:

```powershell
java -version
mvn -v
node --version
npm --version
```

#### 3.9.2 Fresh scaffold

```text
workspace/
├── backend/                          # Spring Boot project root
│   ├── pom.xml
│   ├── src/main/java/com/example/
│   │   ├── FilterxFixtureApplication.java
│   │   ├── FixtureSecurityConfiguration.java
│   │   └── model/
│   │       ├── Author.java
│   │       ├── Book.java
│   │       └── BookStatus.java
│   └── src/main/resources/
│       ├── application.properties
│       └── data.sql
├── frontend/                         # Angular workspace
│   └── src/app/{app.routes.ts, app.config.ts, ...}
└── filterx.yaml
```

`backend/pom.xml` (minimum) — must include the Spring Boot parent
(`3.4.7` in the test fixture), `spring-boot-starter-data-jpa`, and
`spring-boot-starter-security` (or your preferred security starter):

```xml
<parent>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-parent</artifactId>
  <version>3.4.7</version>
</parent>
<properties><java.version>21</java.version></properties>
<dependencies>
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-jpa</artifactId>
  </dependency>
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-security</artifactId>
  </dependency>
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
  </dependency>
  <dependency>
    <groupId>com.h2database</groupId>
    <artifactId>h2</artifactId>
    <scope>runtime</scope>
  </dependency>
</dependencies>
<build>
  <plugins>
    <plugin>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-maven-plugin</artifactId>
    </plugin>
  </plugins>
</build>
```

`backend/src/main/java/com/example/FilterxFixtureApplication.java`:

```java
package com.example;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class FilterxFixtureApplication {
  public static void main(String[] args) {
    SpringApplication.run(FilterxFixtureApplication.class, args);
  }
}
```

`backend/src/main/resources/application.properties`:

```properties
spring.datasource.url=jdbc:h2:mem:filterx;DB_CLOSE_DELAY=-1
spring.jpa.hibernate.ddl-auto=create-drop
spring.jpa.defer-datasource-initialization=true
spring.sql.init.mode=always
spring.jpa.open-in-view=false
```

`filterx.yaml`:

```yaml
version: 1
project:
  name: spring_fixture
  root: .
  backend_root: backend
  frontend_root: frontend
  alembic_ini: backend/alembic.ini
python:
  app_import: app.main:app
  base_class_import: app.database:Base
  models_package: app.models
  session_dependency_import: app.database:get_db
  sqlalchemy_url_env: DATABASE_URL
backend:
  enabled: true
  framework: spring-boot-jpa
  api_prefix: /api
  spring:
    module_path: .
    build_tool: maven # or "gradle"
    maven_command: null # defaults to "mvn" on PATH
    gradle_command: null # defaults to "gradle" on PATH
    source_root: src/main/java
    generated_package: com.example.filterx.generated
    application_class: com.example.FilterxFixtureApplication
    pom_file: pom.xml
    gradle_file: null
    use_records: true
    jpa_provider: hibernate
    springdoc_version: 2.8.9
    resilience4j_version: 2.3.0
    poi_version: 5.4.1
    rate_limit_per_minute: 120
    max_query_cost: 100
    compile_timeout_seconds: 180
    maven_args: []
    gradle_args: []
frontend:
  enabled: true
  framework: angular
  workspace_root: frontend
  generated_root: frontend/src/app/filterx-generated
  routes_file: frontend/src/app/app.routes.ts
  routes_anchor: "// FILTERX:ROUTES"
  app_config_file: frontend/src/app/app.config.ts
  app_config_anchor: "// FILTERX:PROVIDERS"
  entity_style: kebab
database:
  enabled: false
  provider: alembic
  migration_dir: backend/alembic/versions
  features:
    saved_filters: true
    shared_filters: false
    auditing: false
scan:
  framework: jpa
  emit_ir: false
  max_relationship_depth: 3
  include_views: false
  include_hybrid_properties: false
  respect_soft_delete: true
  jpa:
    module_path: .
    build_tool: maven
    java_command: java
    maven_command: null
    gradle_command: null
    helper_source: null
    classes_dir: null
    classpath: null
    compile_timeout_seconds: 120
    helper_timeout_seconds: 60
    maven_args: []
    gradle_args: []
safety:
  dry_run_default: true
  require_anchor_comments: true
  idempotency_manifest: .filterx/manifest.json
  allow_overwrite_generated: true
  strict_conflict_mode: true
output:
  scan_file: .filterx/scan.json
  ir_file: .filterx/ir.json
  plan_file: .filterx/plan.json
  diagnostics_file: .filterx/diagnostics.json
  patch_dir: .filterx/patches
```

> **No backend anchor is required.** The generated package
> `com.example.filterx.generated` is picked up automatically by
> Spring's component scan because it is a sub-package of
> `com.example.FilterxFixtureApplication` (the
> `application_class`). If you place the generated package in a
> sibling tree, you'll need to add `@ComponentScan(...)` or
> `@SpringBootApplication(scanBasePackages = ...)` to your main
> class.

#### 3.9.3 Running scan / install / validate

The Spring JPA scan is the most invasive because it shells out to
Maven to compile a small Java helper that introspects your entities:

```powershell
# 1) Make sure the project compiles (the scanner needs the classes
#    on disk before it can introspect them)
cd backend
mvn -DskipTests compile
cd ..

# 2) Scan
filterx scan --project-root . --config filterx.yaml --no-dry-run --json
# Expect: "entity_count": 2 (Author, Book), and an ir_file key

# 3) Backend install
filterx backend install --project-root . --config filterx.yaml --no-dry-run --yes --json
# Expect: src/main/java/com/example/filterx/generated/*.java
#         (FilterxConfiguration, FilterxController, FilterxDtos,
#          FilterxErrorHandler, FilterxMetadata, FilterxQueryService,
#          FilterxExportService, FilterxRequests, FilterxSecurity,
#          FilterxSpecifications)
# Expect: pom.xml gained spring-boot-starter-data-jpa,
#         springdoc-openapi-starter-webmvc-ui,
#         resilience4j-spring-boot3, poi-ooxml

# 4) Frontend install
filterx frontend install --project-root . --config filterx.yaml --no-dry-run --yes --json

# 5) Validate
filterx validate --project-root . --config filterx.yaml --json
```

**`filterx backend validate`** for Spring is special: it actually
**runs** `mvn -DskipTests compile` (or `gradle compileJava`) to
confirm that the generated Java compiles against your entities. If
the compile fails, you get a `SPRING_COMPILE_FAILED` error and exit
code 4.

**Failure indicators**:

- exit code 2 with `"code": "JPA_PROJECT_INVALID"` — the scanner
  cannot find `pom.xml` / `build.gradle` or the helper class
  cannot be compiled.
- exit code 2 with `"code": "EXPRESS_CONFIGURATION_INVALID"` — no,
  this is the Express error. The Spring equivalent is
  `"code": "SPRING_PROJECT_INVALID"` (raised in
  `renderers/spring_boot_jpa.py` when the application class is
  missing or the generated package layout is invalid).
- exit code 4 from `filterx backend validate` with
  `"code": "SPRING_COMPILE_FAILED"` — the generated Java did not
  compile.

#### 3.9.4 Starting both

Backend (terminal 1):

```powershell
cd backend
mvn -DskipTests spring-boot:run
```

Default port: 8080. Override in `application.properties` with
`server.port=8080`.

Sanity:

```powershell
curl http://127.0.0.1:8080/api/filterx/metadata
```

Frontend (terminal 2): same as 3.1.4 (Angular dev server, port
4200), with `proxy.conf.cjs` updated to point at port 8080.

#### 3.9.5 Functional test checklist

Same endpoints as 3.1.5. The Spring implementation:

- Uses **records** (`@Configuration`-friendly) for request/response
  DTOs.
- Uses **Spring Data JPA Specifications** for filtering — not JPQL
  string concat.
- Streams exports via `StreamingResponseBody` and Apache POI's
  `SXSSFWorkbook` for `.xlsx`.
- The `group-by` endpoint enforces that the group field does not
  contain a dot (relationship grouping is not portable; the Spring
  version also rejects it).

#### 3.9.6 Security checks

1. Implement Spring beans in
   `backend/src/main/java/com/example/FixtureSecurityConfiguration.java`:

   ```java
   package com.example;
   import com.example.filterx.generated.FilterxSecurity;
   import org.springframework.context.annotation.Bean;
   import org.springframework.context.annotation.Configuration;

   @Configuration
   public class FixtureSecurityConfiguration {
     @Bean FilterxSecurity.IdentityExtractor fixtureIdentity() {
       return request -> request.getHeader("x-genre");
     }
     @Bean FilterxSecurity.RowLevelSecurity fixtureRows() {
       return (principal, entity, action, request) -> {
         if (principal == null || !"Book".equals(entity.path("name").asText())) return null;
         return (root, query, cb) -> cb.equal(root.get("genre"), principal);
       };
     }
     @Bean FilterxSecurity.FieldVisibility fixtureFields() {
       return (principal, entity, field, action, request) -> !"price".equals(field);
     }
   }
   ```

2. Re-run `filterx backend install`.

3. With the server running:

   ```powershell
   # Without x-genre: empty principal → row predicate is null → all rows
   curl http://127.0.0.1:8080/api/filterx/books

   # With x-genre=Tech: only Tech books, "price" hidden
   curl -H "x-genre: Tech" http://127.0.0.1:8080/api/filterx/books
   ```

4. **Rate limit**: the Spring renderer wires a Resilience4j
   `RateLimiter` bean (`filterx-api`) with the
   `rate_limit_per_minute` you set in `filterx.yaml`. The
   `filterxRateLimitFilter` enforces it. To verify, set
   `rate_limit_per_minute: 5` in `filterx.yaml`, re-run
   `filterx backend install`, restart the server, and
   `curl` the metadata endpoint in a loop. The 6th call returns 429.

5. **Query-cost guard**: set `max_query_cost: 5` in
   `filterx.yaml`, re-run install, restart, and POST a deeply
   nested filter tree to `/api/filterx/books/filter`. The 400
   response will be:

   ```json
   {
     "error": {
       "code": "QUERY_COST_EXCEEDED",
       "message": "Query cost N exceeds limit 5."
     }
   }
   ```

   (Note: the Spring error envelope format differs from the Express
   one — the Spring error is raised from `FilterxQueryService::guardCost`
   and surfaces through the global `FilterxErrorHandler`.)

#### 3.9.7 Rollback verification

```powershell
filterx rollback --project-root . --config filterx.yaml --list
filterx rollback --project-root . --config filterx.yaml --patch-id <id>
```

After rollback:

- `src/main/java/com/example/filterx/generated/` is gone.
- `pom.xml` is restored to its pre-install state (the merged
  dependencies are removed).
- The `frontend/src/app/filterx-generated/` and Angular
  `app.routes.ts` / `app.config.ts` are restored to their
  pre-install state (this happens automatically when the
  `frontend.install` patch is also rolled back; you may need to
  roll back both patch ids if you ran them separately).

#### 3.9.8 Known gaps

- **Spring Security must already be on the classpath.** The
  generated `@PreAuthorize("@filterxAuthorization.authorize(...)")`
  annotations only work if Spring Security is present. The renderer
  does **not** add `spring-boot-starter-security` to `pom.xml`
  automatically. You must add it yourself or
  `filterx backend validate` will fail with a compile error.
- **The rate limit only applies to `GET /api/filterx/metadata` and
  `GET /api/filterx/{entity}`** (the routes registered before the
  filter chain). If you have a custom `SecurityFilterChain` that
  re-orders the filter chain, verify the FilterX filter is in
  front of your auth filters.
- **CORS is not configured by the renderer.** If your Angular dev
  server is on `localhost:4200` and the Spring app is on
  `localhost:8080`, you need a CORS config. FilterX does not write
  one.
- **`@SpringBootApplication` component scanning must cover the
  generated package.** In the test fixture, the generated package
  is `com.example.filterx.generated`, which is a sub-package of
  `com.example.FilterxFixtureApplication` — fine. If your
  application class is `com.acme.app.Main` and the generated
  package is `com.example.filterx.generated`, the controller and
  services will not be picked up. Move the generated package
  under your application root, or add
  `@SpringBootApplication(scanBasePackages = {...})`.

---

### 3.10 Spring Boot JPA + React (Vite)

Identical to 3.9 for the backend, and 3.2 for the frontend.

`filterx.yaml` differs only in the `frontend` block: set
`framework: react-vite` and the `frontend.react_vite` config.

Verify the Vite dev proxy in `frontend/vite.config.ts` points at
the Spring port (default 8080).

#### 3.10.7 Rollback

Roll back the backend with `filterx rollback --patch-id <id>`.
Roll back the frontend with `filterx frontend remove`.

---

### 3.11 Spring Boot JPA + Next.js

Identical to 3.9 for the backend, and 3.3 for the frontend.

Add `rewrites()` to `frontend/next.config.ts` so that
`/api/:path*` is forwarded to `http://127.0.0.1:8080/api/:path*`.

#### 3.11.7 Rollback

Same as 3.10.7.

---

### 3.12 Spring Boot JPA + Vue

Identical to 3.9 for the backend, and 3.4 for the frontend.

Verify the Vite dev proxy in `frontend/vite.config.ts` points at
the Spring port (default 8080).

#### 3.12.7 Rollback

Same as 3.10.7.

---

## Cross-combination parity check (manual)

The automated test suite (`test_express_prisma_e2e.py` and
`test_spring_boot_jpa_e2e.py`) already runs the **same** requests
against the FastAPI, Express, and Spring backends in the same
process and asserts that the responses are byte-equal. To do the
**same check by hand** so you can see the responses with your own
eyes, follow this procedure.

You need two (or three) backends running in parallel on different
ports, all seeded with **identical data** (Author = "Ada", Books =
"Alpha Filtering"/Tech/10, "Beta Search"/Tech/30, "Gamma
Grouping"/Business/40, plus optional relationship rows so the cycle
test works).

1. **Start the FastAPI backend** (port 8000) and the **Express
   backend** (port 3000) — both pointing at the same database if
   you can, otherwise at two different databases seeded with the
   same SQL. (For the FastAPI vs. Express comparison, the easiest
   setup is a single Prisma database and an adapter that exposes
   the same models through SQLAlchemy — but if that's too much
   work, two H2 instances with the same `data.sql` work too.)

2. **Pick the SAME filter, sort, pagination, and group request**
   for both. The hand-rolled request that gives the most coverage
   is:

   ```
   GET /api/filterx/books?genre_eq=Tech&price_gte=10&price_lte=50&sort_by=price&order=desc&page=1&size=10
   ```

   Then the group request:

   ```
   GET /api/filterx/books/group-by/genre
   ```

   Then a relationship-spanning filter (this is the one that
   exercises the join path):

   ```
   GET /api/filterx/books?author.name_eq=Ada
   ```

   Then a custom nested tree (FastAPI uses POST `/filter`; the
   body shape is the same on all backends):

   ```bash
   curl -X POST http://127.0.0.1:8000/api/filterx/books/filter \
        -H "content-type: application/json" \
        -d '{"filter_tree":{"node_type":"operator","operator":"OR","children":[
              {"node_type":"condition","field":"genre","operation":"eq","value":"Tech"},
              {"node_type":"condition","field":"price","operation":"lt","value":15}
            ]}}'
   ```

3. **Diff the responses** field by field. Expected outcomes:
   - The `data` arrays should contain the same titles in the same
     order.
   - The `meta.total_items` should be identical.
   - The `meta.total_pages` should be identical.
   - The relationship filter should return the same rows; the
     `author` field (when present) should serialize the same way
     (the Express renderer flattens, the FastAPI one flattens, the
     Spring one flattens — but the FastAPI serializer is
     `BeanWrapperImpl`-based, the Express one is a manual loop, and
     the Spring one is `BeanWrapperImpl` too, so a one-off
     `JSON.stringify()` comparison is the right check).
   - For the group-by, the array of `[{key, count}, ...]` should
     be identical.

4. **Now add a third backend to the comparison**: Spring Boot on
   port 8080. The same `curl`s should produce the same
   `data[*].title` and `meta` fields.

5. **Document any divergence** you see. If the FastAPI version
   includes a `joined_at` field that the Express one does not,
   that is a known limitation of the Express serializer (it
   `select`s a specific set of columns). If the ordering of
   `relationships` differs, that is the IR's `cycle_memberships`
   being re-evaluated — file a bug.

6. **Cycle / relationship test** (if your fixture has a
   self-referential relationship like `Author.follows`):
   the Spring backend's `FilterxQueryService` uses
   `cb.equal` and the `from.join()` chain, so a self-referential
   `follows` join must not break the response. The Express
   backend uses Prisma's `is` / `some` operators, which it
   supports natively. The FastAPI backend uses `aliased()` per
   join path, so a self-referential join through the same
   relationship twice would create two aliases and a `DISTINCT`
   issue. Verify the request:

   ```
   GET /api/filterx/authors?follows.name_eq=Ada
   ```

   returns the same `data` on all three backends.

---

## Known gaps and partial support

The implementation has clear gaps versus the spec. They are
enumerated below, with the evidence for each.

1. **`frontend.route_prefix` is documented in README but is not
   honored by the source.** The README tells you to set
   `route_prefix: filterx` to dodge route collisions; the
   implementation does not consume that key. If you need to
   remount the generated pages, edit your host routes by hand
   or use the `frontend.<target>.host_file` switch.

2. **No `filterx backend remove` for Express** — the command is a
   stub. Use `filterx rollback --patch-id <id>` instead. The
   Angular frontend has a real `filterx frontend remove` command;
   so do `react-vite`, `nextjs`, and `vue`.

3. **Spring Boot requires Spring Security to already be on the
   classpath** for `@PreAuthorize` to work. The renderer does not
   add `spring-boot-starter-security` to `pom.xml`.

4. **Spring Boot's generated package must be a sub-package of
   the `application_class`** for component scanning to find the
   controller, services, and metadata. The renderer does not
   validate this — it silently emits the files and lets Spring
   throw at startup.

5. **The Prisma scanner requires a generated Prisma client**
   (`node_modules/.prisma/client/index.js`) to exist BEFORE
   `filterx scan`. There is a `scan.prisma.allow_stale_client`
   escape hatch for inspection-only use, but the install/validate
   steps will fail without a real client.

6. **The JPA scanner compiles a Java helper class** and inspects
   its bytecode. This requires Maven or Gradle on PATH before
   scan can succeed. The CLI does not check for them up-front;
   it just fails when it tries to run the helper.

7. **Group-by and sort on a relationship field is rejected by
   the Express backend** (`GROUP_FIELD_UNSUPPORTED`,
   `SORT_FIELD_UNSUPPORTED`) and by the Spring backend
   (`GROUP_FIELD_UNSUPPORTED`). The FastAPI backend allows it
   but only through `aliased()` joins.

8. **The `react-vite`, `nextjs`, and `vue` renderers do not
   configure your dev-server proxy.** You must edit
   `vite.config.ts` (Vite) or `next.config.ts` (Next.js)
   yourself. Only the Angular renderer writes
   `proxy.conf.cjs` and updates `angular.json`.

9. **The Vue renderer's filter builder is split into a separate
   `.vue` file** (`FilterxFilterBuilder.vue`). If your Vue
   project's lint config disallows `.vue` files outside of
   `pages/`, you will need to adjust it.

10. **No `app-skeleton generator` for the non-Angular
    frontends.** The Angular renderer copies a large reference
    runtime (under `src/app/core/**` and `src/app/shared/**`).
    The React/Vite, Next.js, and Vue renderers only write
    `src/filterx-generated/*`. You bring your own `App.tsx`,
    `App.vue`, `main.tsx`, etc.

11. **Field visibility is opt-in on FastAPI.** The generated
    `_serialize_row` function calls the hook only if
    `field_visibility_hook_import` is set; otherwise it
    serializes every field. The Express and Spring renderers
    always call their respective `fieldVisible` hooks, but
    those hooks are no-op defaults unless overridden.

12. **The Express backend is ESM-only** (the renderer writes
    `.js` import suffixes when `tsconfig.compilerOptions.module`
    is `NodeNext` or `node16`). If your project uses CommonJS
    (`module: "commonjs"`), the imports will resolve correctly
    but you will see a TypeScript warning about not being able
    to resolve the extensions.

---

## Appendix A — endpoints every backend exposes

All three backends expose the same routes under `<api_prefix>/filterx`
(default `<api_prefix>` = `/api`). Verified by reading
`renderers/express_prisma.py::_render_router`,
`renderers/spring_boot_jpa.py::_render_controller`, and
`commands/backend.py::_render_router_factory_py_legacy` /
`render_router_factory_py`.

| Method | Path                                      | What it does                          |
| ------ | ----------------------------------------- | ------------------------------------- |
| GET    | `/metadata`                               | List all entities                     |
| GET    | `/{entity}/metadata`                      | Per-entity metadata                   |
| GET    | `/{entity}` and `/{entity}/query`         | Paginated/filtered query (URL params) |
| POST   | `/{entity}/filter`                        | Paginated/filtered query (body)       |
| POST   | `/{entity}/export?format=csv\|xlsx\|json` | Streaming export                      |
| GET    | `/{entity}/group-by/{field}`              | Group-by buckets (URL params)         |
| POST   | `/{entity}/group-by/{field}/filter`       | Group-by buckets (body)               |

`{entity}` is the entity's **name** (`Author`, `Book`, ...) or
**table** (`authors`, `books`, ...). The Express and Spring
renderers also accept pluralized names (`books` matches the `Book`
entity, etc.) — see
`renderers/express_prisma.py::entityFor` and
`renderers/spring_boot_jpa.py::FilterxMetadata.entity`.

URL filter operators: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`,
`like`, `ilike`, `starts_with`, `ends_with`, `in`, `not_in`,
`is_null`, `is_not_null`, `between`. Suffix the field name with
`_<op>` and pass the value as the query string. Multiple filter
parameters are AND-combined by the URL parser. For OR / nested
AND, use the POST `/filter` body with a `filter_tree`.

Reserved URL keys (not treated as filters):
`page`, `size`, `sort_by`, `order`, `search`.

---

## Appendix B — filter operators supported by every backend

`eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `like`, `ilike`,
`starts_with`, `ends_with`, `in`, `not_in`, `is_null`,
`is_not_null`, `between`.

The IR records per-field which of those are allowed (see
`core/ir.py::FieldIR.operations`). The FastAPI backend enforces
this via `_apply_filter`; the Express backend via `scalarCondition`;
the Spring backend via `FilterxSpecifications::condition`. The
end result is the same: sending an unsupported operator for a field
returns HTTP 400 with `OPERATION_UNSUPPORTED`.
