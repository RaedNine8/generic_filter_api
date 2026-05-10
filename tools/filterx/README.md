# FilterX CLI

FilterX adds a reusable filtering layer to an existing project through safe code generation and anchor-based patching.
It is designed to remove repetitive filtering boilerplate while keeping changes explicit and reversible.

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

Optional:

- Angular workspace (only if frontend generation is enabled)
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
2. Add backend anchor in your configured mount file:

```python
# FILTERX:ROUTER_MOUNT
```

3. Run:

```powershell
filterx install --project-root . --config filterx.yaml --dry-run --json
filterx install --project-root . --config filterx.yaml --no-dry-run --yes --json
filterx validate --project-root . --config filterx.yaml --json
```

4. Verify endpoint:

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
