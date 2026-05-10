# FilterX

FilterX is a CLI that adds a generic filtering API **and a ready-to-use Angular filtering UI** to an existing FastAPI + SQLAlchemy + Angular project.

It scans your SQLAlchemy models, generates a backend query/filter router, copies the shared Angular UI runtime, generates model-specific Angular pages/configs, and patches only the host files where you placed explicit anchor comments.

## What problem does it solve?

Most apps rebuild the same list-screen plumbing for every model:

- search
- filters
- nested `AND` / `OR` filter trees
- sorting
- pagination
- grouping
- relationship fields such as `company.name`

FilterX turns that repeated work into generation. Your models stay yours; FilterX only creates integration code around them.

## How FilterX works

1. **Scan**: imports your FastAPI app, SQLAlchemy `Base`, and models package.
2. **Generate backend**: creates `/api/filterx/...` endpoints for metadata, query, filter, and grouping.
3. **Generate frontend**: installs the same reusable Angular list/filter UI and generates pages/configs for your models.
4. **Patch anchors only**: inserts router/routes/providers only where you added FilterX comments.
5. **Validate**: checks that generated files, routes, and config are coherent.

No blind rewrites. No hidden magic. The `.filterx` folder stores scan output, diagnostics, generated-file hashes, and rollback metadata.

## Requirements

- Python 3.10+
- FastAPI app object importable from Python
- SQLAlchemy `Base` importable from Python
- SQLAlchemy models package importable from Python
- Angular app with standalone routing
- Node.js + npm

Frontend generation is mandatory for the standard FilterX integration flow.

## Directory assumptions

The examples below use this common layout:

```text
your-project/
  app/
    main.py
    database.py
    models/
  frontend/
    src/app/app.routes.ts
    src/app/app.config.ts
  filterx.yaml
```

Your project does **not** need to match this layout. Update `filterx.yaml` paths/imports to match your project and OS.

Examples:

- If your backend is in `backend/app`, set `project.backend_root: backend/app` and paths like `backend/app/main.py`.
- If your Angular app is in `client`, set `project.frontend_root: client` and `frontend.workspace_root: client`.
- Use forward slashes in `filterx.yaml` paths; they work on Windows, Linux, and macOS.

## Step-by-step setup

Run all FilterX CLI commands from your own project root, the folder that contains `filterx.yaml`.

### 1. Install the CLI

```bash
python -m pip install "git+https://github.com/RaedNine8/generic_filter_api.git#subdirectory=tools/filterx"
filterx --help
```

For contributors working inside this repository:

```bash
python -m pip install -e tools/filterx
```

### 2. Create `filterx.yaml`

Place this file at your project root and adjust every path/import to your project.

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

### 3. Add required anchors

FilterX patches only these explicit locations.

In the file configured by `backend.mount_file`, usually your FastAPI entrypoint:

```python
# FILTERX:ROUTER_MOUNT
```

In the file configured by `frontend.routes_file`, inside the Angular `Routes` array:

```ts
// FILTERX:ROUTES
```

In the file configured by `frontend.app_config_file`, inside the Angular providers array:

```ts
// FILTERX:PROVIDERS
```

Example route file shape:

```ts
import { Routes } from "@angular/router";

export const routes: Routes = [
  { path: "", redirectTo: "companies", pathMatch: "full" },
  // FILTERX:ROUTES
];
```

Example app config shape:

```ts
export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    // FILTERX:PROVIDERS
  ],
};
```

### 4. Preview the generated changes

```bash
filterx install --project-root . --config filterx.yaml --dry-run --json
```

Review the output before applying. In strict mode, missing anchors or route conflicts block installation.

### 5. Apply backend + frontend generation

```bash
filterx install --project-root . --config filterx.yaml --no-dry-run --yes --json
```

This generates and patches both layers:

- backend FilterX package under `backend.generated_package`
- Angular runtime under `frontend.workspace_root/src/app/core` and `frontend.workspace_root/src/app/shared`
- model-specific Angular configs/pages under `frontend.generated_root`
- Angular routes/providers/proxy/style config

### 6. Install frontend dependencies

FilterX patches `package.json` with UI dependencies such as PrimeNG and PrimeIcons. Install them after generation.

```bash
cd frontend
npm install
cd ..
```

If your Angular folder is not `frontend`, replace `frontend` with your configured `frontend.workspace_root`.

### 7. Validate and build

```bash
filterx validate --project-root . --config filterx.yaml --json
```

Then build the Angular app from your frontend workspace:

```bash
cd frontend
npm run build
cd ..
```

### 8. Run the app

Terminal 1, from project root:

```bash
uvicorn app.main:app --reload
```

Change `app.main:app` if your FastAPI import path is different.

Terminal 2, from your Angular folder:

```bash
cd frontend
npm start
```

Open the Angular dev URL, usually `http://localhost:4200`, then visit a generated entity route such as `/companies`, `/employees`, or whatever route names match your tables.

## Expected generated API

With the default `backend.api_prefix: /api`, FilterX exposes:

- `GET /api/filterx/metadata`
- `GET /api/filterx/{entity}/metadata`
- `GET /api/filterx/{entity}`
- `GET /api/filterx/{entity}/query`
- `POST /api/filterx/{entity}/filter`
- `GET /api/filterx/{entity}/group-by/{field}`
- `POST /api/filterx/{entity}/group-by/{field}/filter`

The generated Angular UI calls these endpoints through the configured dev proxy.

## Useful commands

```bash
filterx scan --project-root . --config filterx.yaml --no-dry-run --json
filterx install --project-root . --config filterx.yaml --dry-run --json
filterx install --project-root . --config filterx.yaml --no-dry-run --yes --json
filterx validate --project-root . --config filterx.yaml --json
filterx rollback --project-root . --config filterx.yaml --list
```

Layer-specific commands are also available:

```bash
filterx backend install --project-root . --config filterx.yaml --no-dry-run --yes --json
filterx frontend install --project-root . --config filterx.yaml --no-dry-run --yes --json
filterx db install --project-root . --config filterx.yaml --no-dry-run --yes --json
```

Use layer-specific commands only when you intentionally want to operate on one layer.

## Common first-run issues

- `ANCHOR_NOT_FOUND`: add the configured anchor to the configured file.
- `SCAN_FILE_MISSING`: run `filterx install` or `filterx scan` with writes enabled first.
- Route conflict on `/api/filterx/...`: change `backend.api_prefix` or remove the conflicting host route.
- Angular icons appear as empty circles: restart `npm start` after generation; `angular.json` must load `node_modules/primeicons/primeicons.css`.
- Frontend API calls fail: confirm the backend is running and `frontend/proxy.conf.cjs` points to the right backend URL.

## Rollback

FilterX writes patch bundles under `.filterx/patches`.

```bash
filterx rollback --project-root . --config filterx.yaml --list
filterx rollback --project-root . --config filterx.yaml --patch-id <patch-id>
```

## Full CLI reference

See [tools/filterx/README.md](tools/filterx/README.md).
