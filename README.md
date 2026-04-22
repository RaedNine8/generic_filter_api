# FilterX - Plug-In Filtering For Your Own Models

FilterX is a bootstrap CLI that injects a generic filtering layer into your existing app.  
You point it to your FastAPI app and SQLAlchemy models, and it generates the plumbing for you.

## 1) What This File Is For

This README is the fastest path to get a new user working in minutes.  
It explains only what is required, what is optional, and why each step exists.

## 2) Do I Need A Specific Project Structure?

No, your project does not need to match this repository folders.  
You only need importable Python paths and a few target files configured in `filterx.yaml`.

Minimum backend contract:

- An importable FastAPI app object
- An importable SQLAlchemy Base
- An importable models package
- A DB session dependency function

Optional frontend contract:

- Angular project with a routes file
- Optional Angular app config file (if provider patching is enabled)

Optional DB contract:

- Alembic migration directory (if DB generation is enabled)

## 3) Install The CLI

Install FilterX into your target project environment.  
This gives you the `filterx` command.

```powershell
pip install "https://github.com/RaedNine8/generic_filter_api.git"
filterx --help
```

## 4) Create `filterx.yaml` (Required)

`filterx.yaml` is the map between FilterX and your project.  
FilterX reads it to know what to scan, where to generate code, and where to patch host files.

Use this minimal template and replace the values with your own paths:

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

## 5) Add Anchor Comments (Only Where Needed)

Anchors are explicit insertion points so FilterX patches safely instead of rewriting random code.  
They are mandatory only for enabled patch operations, and the file paths are configurable in `filterx.yaml`.

Backend mount anchor (in the file set by `backend.mount_file`):

```python
# FILTERX:ROUTER_MOUNT
```

Frontend anchors (only if `frontend.enabled: true`):

```ts
// FILTERX:ROUTES
// FILTERX:PROVIDERS
```

Important:

- Anchors do not need to be in these exact filenames.
- They must exist in whichever files you configured.

## 6) Run Install In 3 Commands

This flow is the safest and quickest for first-time integration.  
First preview, then apply, then validate.

```powershell
filterx install --project-root . --config filterx.yaml --dry-run --json
filterx install --project-root . --config filterx.yaml --no-dry-run --yes --json
filterx validate --project-root . --config filterx.yaml --json
```

Runtime sanity check:

```text
GET /api/filterx/metadata
```

## 7) Fast Modes

Use backend-only to get started faster, then add frontend/DB later.  
You can enable each layer independently.

- Backend only: set `frontend.enabled: false`, `database.enabled: false`
- Backend + Frontend: set `frontend.enabled: true`
- Full stack: set all enabled flags to true

## 8) Most Common Errors

These are usually configuration or anchor placement issues.  
Fix the item and rerun install/validate.

- `SCAN_FILE_MISSING`: run scan/install with non-dry-run first
- `ANCHOR_NOT_FOUND`: add the configured anchor in the configured target file
- Route conflict on `/api/filterx/metadata`: change `backend.api_prefix` or remove conflicting route

## 9) Local-Only Testing Note

If you are testing books/authors locally, keep them as local sandbox artifacts and avoid committing them.  
See `.gitignore` rules in this repository for sample local exclusions.
