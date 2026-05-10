# FilterX

FilterX is a CLI that injects a generic filtering layer into your existing project.
You configure where your app and models live, then FilterX generates safe integration files and patches only where you explicitly allow it.

## Why this approach exists

Most teams rewrite the same filtering logic for every model and every list screen.
FilterX centralizes that boilerplate into generation, so teams keep control but stop repeating low-value plumbing work.

## Start here in 5 minutes

This is the fastest first run for backend integration.
You can add frontend and DB generation later.

1. Install the CLI in your project environment.

```powershell
pip install "git+https://github.com/RaedNine8/generic_filter_api.git#subdirectory=tools/filterx"
filterx --help
```

2. Create filterx.yaml at your project root.

filterx.yaml is the map that tells FilterX:

- what to scan,
- where to generate files,
- where it is allowed to patch host code.

Minimal backend-first template:

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
  enabled: false
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

3. Add one backend anchor comment.

Anchor comments are mandatory only for enabled patch operations.
They are safety markers so FilterX never inserts code into unknown places.

In the file configured by backend.mount_file, add:

```python
# FILTERX:ROUTER_MOUNT
```

4. Run preview, apply, then validate.

```powershell
filterx install --project-root . --config filterx.yaml --dry-run --json
filterx install --project-root . --config filterx.yaml --no-dry-run --yes --json
filterx validate --project-root . --config filterx.yaml --json
```

5. Runtime sanity check.

```text
GET /api/filterx/metadata
```

## Add frontend later (optional)

Enable frontend when you are ready to generate UI integration files and route snippets.
If frontend.enabled is true, add these anchors in your configured host files:

```ts
// FILTERX:ROUTES
// FILTERX:PROVIDERS
```

## Do I need the same folder structure as this repo?

No.
Your project can use any structure, as long as the paths and imports in filterx.yaml are correct.

## What commands should I remember?

- filterx scan: discover models and routes, writes .filterx scan artifacts
- filterx install: orchestrates scan + enabled installs + validate
- filterx validate: health check for generated integration
- filterx rollback: restore previous state from patch bundles

## What is the .filterx folder?

It is FilterX operational state, not business data.
It stores scan output, plan, diagnostics, manifest, and rollback metadata.

## Common first-run issues

- SCAN_FILE_MISSING: run install or scan with writes enabled first
- ANCHOR_NOT_FOUND: add the configured anchor in the configured file
- Route conflict on /api/filterx/metadata: change backend.api_prefix or remove conflicting host route

## Need full CLI reference?

See tools/filterx/README.md for complete command reference and advanced flows.
