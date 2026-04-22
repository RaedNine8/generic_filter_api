# FilterX CLI

FilterX CLI bootstraps a generic filtering system into a project with safe, idempotent patching.

It can:

- scan SQLAlchemy models and API routes,
- generate backend integration files,
- generate frontend integration files,
- generate optional persistence migrations,
- validate integration health,
- rollback generated changes.

This guide is written for GitHub use: clear setup, clear commands, and a complete new-project path.

## What You Need

Minimum requirements:

- Python 3.10+
- FastAPI app importable from your project
- SQLAlchemy `Base` importable from your project
- SQLAlchemy models package importable from your project

Optional frontend requirements:

- Angular workspace with routes file and app config file
- Anchor comments where FilterX inserts generated route/provider snippets

Optional DB requirements:

- Alembic migration directory

## Install FilterX CLI

From repository root (editable install):

```powershell
python -m pip install -e tools/filterx
```

After install, the command is available as:

```powershell
filterx --help
```

## Quick Start (Existing Project)

1. Add required anchor comments in host files.
2. Create `filterx.yaml` in project root.
3. Run orchestrated install.
4. Run validation.

Commands:

```powershell
filterx install --project-root . --config filterx.yaml
filterx validate --project-root . --config filterx.yaml
```

## Full New Project Integration

This section shows how to inject FilterX into a brand new project.

### 1. Prepare Backend Structure

Your project must expose:

- FastAPI app object (example: `app.main:app`)
- SQLAlchemy Base (example: `app.database:Base`)
- models package (example: `app.models`)

Example expected structure:

```text
your_project/
	app/
		main.py
		database.py
		models/
			__init__.py
			book.py
			author.py
	filterx.yaml
```

### 2. Add Backend Anchor

In `app/main.py`, add this comment where router mount insertion should happen:

```python
# FILTERX:ROUTER_MOUNT
```

### 3. Prepare Frontend Files (Optional)

If frontend is enabled, add:

- in routes file (example `frontend/src/app/app.routes.ts`):

```ts
// FILTERX:ROUTES
```

- in app config file (example `frontend/src/app/app.config.ts`):

```ts
// FILTERX:PROVIDERS
```

If you do not have frontend yet, set `frontend.enabled: false` in config.

### 4. Create `filterx.yaml`

Use this baseline template:

```yaml
version: 1

project:
	name: your_project
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

### 5. Run Install

Start with dry-run behavior from config (`dry_run_default: true`), then run real install:

```powershell
filterx install --project-root . --config filterx.yaml --dry-run
filterx install --project-root . --config filterx.yaml --no-dry-run
```

### 6. Validate

```powershell
filterx validate --project-root . --config filterx.yaml
```

### 7. Verify Runtime

Expected backend endpoint after backend install:

```text
GET /api/filterx/metadata
```

Generated files are written under:

- `app/filterx_generated/` (backend)
- `frontend/src/app/filterx-generated/` (frontend)

## Command Guide

### Scan

```powershell
filterx scan --project-root . --config filterx.yaml
```

Writes:

- `.filterx/scan.json`
- `.filterx/diagnostics.json`
- `.filterx/plan.json`

### Orchestrated Install

```powershell
filterx install --project-root . --config filterx.yaml
```

Runs:

1. scan
2. backend install (if enabled)
3. frontend install (if enabled)
4. db install (if enabled)
5. validate

### Backend Commands

```powershell
filterx backend install --project-root . --config filterx.yaml
filterx backend validate --project-root . --config filterx.yaml
```

Useful options:

- `--entities Book,Author`
- `--no-mount`
- `--force`

Note: `filterx backend remove` is currently scaffolded; for safe revert use rollback.

### Frontend Commands

```powershell
filterx frontend install --project-root . --config filterx.yaml
filterx frontend validate --project-root . --config filterx.yaml
filterx frontend remove --project-root . --config filterx.yaml
```

Useful remove options:

- `--list` to list frontend install patch bundles
- `--patch-id <id>` to rollback a specific frontend patch bundle

### DB Commands

```powershell
filterx db install --project-root . --config filterx.yaml
filterx db validate --project-root . --config filterx.yaml
```

Feature flags at install time:

```powershell
filterx db install --project-root . --config filterx.yaml --saved-filters --shared-filters --auditing
```

You can also disable explicitly:

```powershell
filterx db install --project-root . --config filterx.yaml --no-shared-filters --no-auditing
```

Migration output file:

- `<migration_dir>/filterx_generated_persistence.py`

### Rollback

```powershell
filterx rollback --project-root . --config filterx.yaml --list
filterx rollback --project-root . --config filterx.yaml
filterx rollback --project-root . --config filterx.yaml --patch-id <patch-id>
```

Rollback restores previous file content from `.filterx/patches/*/backup`.

## Safety Model

FilterX writes are safe by design:

- anchor-based patching (does not blindly rewrite host files),
- strict conflict mode support,
- idempotency manifest (`.filterx/manifest.json`),
- patch bundles with rollback metadata (`.filterx/patches`).

## Typical CI Flow

```powershell
filterx scan --project-root . --config filterx.yaml --check
filterx validate --project-root . --config filterx.yaml
```

## Troubleshooting

### "SCAN_FILE_MISSING"

Run scan first:

```powershell
filterx scan --project-root . --config filterx.yaml
```

### "ANCHOR_NOT_FOUND"

Add missing anchor comment in configured host file:

- backend: `# FILTERX:ROUTER_MOUNT`
- frontend routes: `// FILTERX:ROUTES`
- frontend app config: `// FILTERX:PROVIDERS`

### Route conflict on `/api/filterx/metadata`

Adjust `backend.api_prefix` or remove conflicting host route.

### Patch rollback target not found

List bundles first:

```powershell
filterx rollback --project-root . --config filterx.yaml --list
```

## Development Notes

For local contributor workflow in this repository:

```powershell
python -m pip install -e tools/filterx
python -m pytest tools/filterx/tests -q
```

## License

Use the repository license.
