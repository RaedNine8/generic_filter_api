# FilterX

FilterX injects a generic filtering system into **your existing FastAPI + SQLAlchemy + Angular project**.

It generates both sides of the feature:

- a backend API for metadata, search, filtering, grouping, sorting, and pagination
- an Angular UI with list pages, advanced search, filter trees, grouping, tables, and pagination

Frontend integration is part of the standard flow and is included in the steps below.

## What FilterX does

FilterX is a generator, not a framework replacement.

1. It scans your SQLAlchemy models.
2. It generates `/api/filterx/...` backend endpoints.
3. It copies the reusable Angular filtering UI runtime.
4. It generates one Angular page/config per model.
5. It patches only the host files where you added explicit anchor comments.

The goal is to avoid rebuilding the same filtering/list-screen logic for every model.

## Before you start

You need a project with:

- Python 3.10+
- FastAPI
- SQLAlchemy models
- an importable SQLAlchemy `Base`
- an importable DB session dependency
- Alembic if you want migration support
- Angular frontend
- Node.js + npm
- PostgreSQL or another database supported by your app

All commands below are written so they can be run from **your target project root**.

## 0. Go to your target project

Go to the project where you want to inject FilterX.

```bash
cd path/to/your-project
```

From this point on, `.` means your project root.

## 1. Activate/use the Python environment

Use your project virtual environment.

Windows PowerShell example:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux example:

```bash
source .venv/bin/activate
```

Install your project dependencies if needed:

```bash
python -m pip install -e .
```

Install the FilterX CLI:

```bash
python -m pip install "git+https://github.com/RaedNine8/generic_filter_api.git#subdirectory=tools/filterx"
filterx --help
```

If you cloned this repository and are developing FilterX locally, install the CLI in editable mode from the cloned repo instead:

```bash
python -m pip install -e path/to/generic_filter_api/tools/filterx
filterx --help
```

This gives you:

- your project dependencies
- the `filterx` command
- access to the generated backend and frontend installers

## 2. Configure the database

Create your `.env` file if your project uses one.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Open `.env` and make sure `DATABASE_URL` points to your database.

Example:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/my_project_db
```

Create the database if it does not exist yet.

Example with `psql`:

```sql
CREATE DATABASE my_project_db;
```

Use your own database name, user, password, host, and port.

## 3. Generate/apply your normal domain tables

Before adding FilterX, your normal application tables should exist.

If your project uses Alembic and needs a first migration:

```bash
alembic revision --autogenerate -m "init_domain_models"
alembic upgrade head
```

If your project already has migrations:

```bash
alembic upgrade head
```

Expected:

- your normal domain tables exist in the database
- your SQLAlchemy models can be imported successfully

## 4. Seed data

Filter/search/group endpoints are easier to verify with real data.

Run your project seed script if you have one:

```bash
python seed_data.py
```

If your project does not have a seed script, insert a few rows manually or use your existing app flow.

## 5. Create `filterx.yaml`

Create `filterx.yaml` at your project root.

This file tells FilterX where your backend, models, frontend, and patch locations are.

Start with this template and edit the paths/imports to match your project:

```yaml
version: 1

project:
  name: my_project
  root: .
  backend_root: app
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
  api_prefix: /api
  generated_package: app/filterx_generated
  mount_file: app/main.py
  mount_anchor: "# FILTERX:ROUTER_MOUNT"
  entities: []
  exclude_entities: []
  global_predicate_hooks: []

frontend:
  enabled: true
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
  plan_file: .filterx/plan.json
  diagnostics_file: .filterx/diagnostics.json
  patch_dir: .filterx/patches
```

Important path rules:

- Use paths relative to your project root.
- Use forward slashes in `filterx.yaml`; they work on Windows, Linux, and macOS.
- If your backend is under `backend/app`, use paths such as `backend/app/main.py`.
- If your Angular app is under `client`, set `frontend.workspace_root: client` and update the frontend paths.
- If your models package is not `app.models`, set `python.models_package` to the actual Python import path.

## 6. Add the required anchors

Anchors are mandatory. They are the exact places where FilterX is allowed to patch your files.

### 6.1 Backend router mount anchor

Open the file configured by `backend.mount_file`.

Example from the template:

```text
app/main.py
```

Add this comment where the generated FilterX router should be mounted:

```python
# FILTERX:ROUTER_MOUNT
```

Example shape:

```python
from fastapi import FastAPI

app = FastAPI()

# your existing routers here

# FILTERX:ROUTER_MOUNT
```

FilterX will mount the generated `/api/filterx` router at this anchor.

### 6.2 Frontend route anchor

Open the file configured by `frontend.routes_file`.

Example from the template:

```text
frontend/src/app/app.routes.ts
```

Add this comment inside the Angular `Routes` array:

```ts
// FILTERX:ROUTES
```

Example shape:

```ts
import { Routes } from "@angular/router";

export const routes: Routes = [
  { path: "", redirectTo: "your-default-page", pathMatch: "full" },
  // FILTERX:ROUTES
];
```

FilterX will insert generated model routes at this anchor.

### 6.3 Frontend provider anchor

Open the file configured by `frontend.app_config_file`.

Example from the template:

```text
frontend/src/app/app.config.ts
```

Add this comment inside the Angular providers array:

```ts
// FILTERX:PROVIDERS
```

Example shape:

```ts
export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    // FILTERX:PROVIDERS
  ],
};
```

FilterX will add required Angular providers at this anchor.

## 7. Scan your project

This reads `filterx.yaml`, imports your app/models, and writes `.filterx` artifacts.

```bash
filterx scan --project-root . --config filterx.yaml --no-dry-run --json
```

Expected:

- your SQLAlchemy entities are discovered
- `.filterx/scan.json` is created
- `.filterx/diagnostics.json` is created
- `.filterx/plan.json` is created

Warnings can be normal if your model graph has cycles, composite keys, or relationships FilterX intentionally skips.

## 8. Generate the backend FilterX API

This creates the generated backend package and mounts it in your FastAPI app.

```bash
filterx backend install --project-root . --config filterx.yaml --no-dry-run --yes --json
```

Generated under `backend.generated_package`:

- `entities.py`
- `metadata.py`
- `router_factory.py`
- `router.py`
- `predicates.py`

Patched:

- the file configured by `backend.mount_file`
- the patch is applied around `backend.mount_anchor`

## 9. Validate backend integration

```bash
filterx backend validate --project-root . --config filterx.yaml --json
```

Start your backend.

Example:

```bash
uvicorn app.main:app --reload
```

Use your actual FastAPI import path if it is different.

Check the generated metadata endpoint:

```text
GET http://localhost:8000/api/filterx/metadata
```

With the default `backend.api_prefix: /api`, generated endpoints include:

- `GET /api/filterx/metadata`
- `GET /api/filterx/{entity}/metadata`
- `GET /api/filterx/{entity}`
- `GET /api/filterx/{entity}/query`
- `POST /api/filterx/{entity}/filter`
- `GET /api/filterx/{entity}/group-by/{field}`
- `POST /api/filterx/{entity}/group-by/{field}/filter`

Keep the backend running for frontend testing.

## 10. Generate the frontend FilterX UI

This step is mandatory for the standard FilterX integration.

```bash
filterx frontend install --project-root . --config filterx.yaml --no-dry-run --yes --json
```

Generated/copied under your configured Angular workspace:

- `src/app/core/**`
- `src/app/shared/**`
- `src/app/filterx-generated/entities/*.config.ts`
- `src/app/filterx-generated/pages/*.page.ts`
- `src/app/filterx-generated/routes.ts`

Patched under your Angular workspace:

- `package.json`
- `angular.json`
- `proxy.conf.cjs`
- `src/styles.css`
- `src/app/app.routes.ts`
- `src/app/app.config.ts`

If your Angular workspace is not named `frontend`, use the directory configured by `frontend.workspace_root`.

## 11. Install frontend dependencies

The frontend generator updates `package.json` with UI dependencies such as PrimeNG and PrimeIcons.

If your Angular workspace is `frontend`:

```bash
cd frontend
npm install
cd ..
```

If your Angular workspace is `client`:

```bash
cd client
npm install
cd ..
```

## 12. Validate full FilterX integration

```bash
filterx validate --project-root . --config filterx.yaml --json
```

Expected shape:

```json
{
  "errors": [],
  "warnings": [],
  "error_count": 0,
  "warning_count": 0
}
```

If warnings appear, read them. Some warnings may be acceptable; errors must be fixed.

## 13. Build the frontend

If your Angular workspace is `frontend`:

```bash
cd frontend
npm run build
cd ..
```

If your Angular workspace is `client`:

```bash
cd client
npm run build
cd ..
```

Expected:

- Angular build completes successfully
- generated pages are included in the build
- non-blocking Angular warnings may appear depending on your project

## 14. Run backend and frontend together

Terminal 1, from project root:

```bash
uvicorn app.main:app --reload
```

Terminal 2, from your Angular workspace:

```bash
cd frontend
npm start
```

Open the Angular dev server URL, usually:

```text
http://localhost:4200
```

Then open one of the generated entity routes. The route names are based on your tables/entities, for example:

```text
http://localhost:4200/<your-entity-route>
```

You should see the generated list UI with search, filter tree, grouping, sorting, pagination, and relationship fields.

## 15. Rollback visibility

List rollback bundles:

```bash
filterx rollback --project-root . --config filterx.yaml --list
```

Rollback a specific bundle:

```bash
filterx rollback --project-root . --config filterx.yaml --patch-id <patch-id>
```

## One-command install alternative

After `filterx.yaml` and anchors are correct, this command runs scan, enabled installs, and validation together:

```bash
filterx install --project-root . --config filterx.yaml --no-dry-run --yes --json
```

For first-time integration, the numbered manual path above is easier to debug.

## What the generated UI calls

The Angular UI talks to the generated backend through `/api/filterx`:

- list pages call `GET /api/filterx/{entity}`
- metadata panels call `GET /api/filterx/{entity}/metadata`
- filter trees call `POST /api/filterx/{entity}/filter`
- grouping calls `/api/filterx/{entity}/group-by/{field}`

The CLI also creates `proxy.conf.cjs` so local Angular dev requests can reach your backend.

## Common issues

- `ANCHOR_NOT_FOUND`: the configured anchor is missing from the configured file.
- `SCAN_FILE_MISSING`: run `filterx scan` or `filterx install` with writes enabled.
- Route conflict on `/api/filterx/...`: change `backend.api_prefix` or remove the conflicting host route.
- Angular icons appear as empty circles: restart `npm start`; `angular.json` must include `node_modules/primeicons/primeicons.css`.
- Frontend API calls fail: confirm the backend is running and `proxy.conf.cjs` targets the correct backend URL.

## Can this README include GIFs?

Not automatically. The commands above are text-first so they work on every OS and in CI. If you want terminal GIFs later, record them locally with a tool such as VHS or asciinema, then add the generated media under a docs/assets folder.

## Full CLI reference

See [tools/filterx/README.md](tools/filterx/README.md).
