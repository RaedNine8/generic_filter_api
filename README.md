# FilterX

FilterX adds a generic filtering backend **and a generated Angular filtering UI** to an existing FastAPI + SQLAlchemy + Angular project.

It is not a new framework. It is a generator:

1. It scans your SQLAlchemy models.
2. It generates `/api/filterx/...` query/filter/group endpoints.
3. It copies the reusable Angular list/filter UI runtime.
4. It generates one Angular page/config per model.
5. It patches only the files where you added explicit anchor comments.

Frontend integration is part of the standard flow. The guide below always includes it.

## Repository example

The clearest end-to-end example is `filterx_robustness_lab`, a dummy project with:

- FastAPI backend
- SQLAlchemy models
- Alembic migrations
- Angular frontend
- `filterx.yaml`
- all required FilterX anchors already present

The guide below is written for that dummy project, but every path can be changed through `filterx.yaml`.

## 0. Go to the target project

Use the project that contains `filterx.yaml` as your working directory.

For the included robustness lab:

```bash
cd ../filterx_robustness_lab
```

For your own project:

```bash
cd path/to/your-project
```

From this point on, commands assume the current directory is the project root.

## 1. Activate or use the Python environment

In this repository, the shared virtual environment is one level above the dummy project: `../.venv`.

Windows PowerShell:

```powershell
..\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m pip install -e ../filter_test_project/tools/filterx
filterx --help
```

macOS/Linux:

```bash
source ../.venv/bin/activate
python -m pip install -e .
python -m pip install -e ../filter_test_project/tools/filterx
filterx --help
```

If you are not using this repository layout, create or activate your own environment, then install your project and the CLI:

```bash
python -m pip install -e .
python -m pip install "git+https://github.com/RaedNine8/generic_filter_api.git#subdirectory=tools/filterx"
filterx --help
```

This gives you:

- your project dependencies
- the local/editable `filterx` CLI
- the `filterx` command available in the active environment

## 2. Configure the database

Create `.env` from `.env.example` if your project provides one.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Open `.env` and make sure `DATABASE_URL` points to your PostgreSQL database.

Example:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/filterx_robustness_lab
```

Create the database in pgAdmin or `psql`:

```sql
CREATE DATABASE filterx_robustness_lab;
```

For your own project, replace the database name, user, password, host, and port with your local values.

## 3. Generate and apply domain tables

This creates the normal application tables before FilterX is installed.

For `filterx_robustness_lab`, this means tables for:

- Company
- Department
- Employee
- Project
- ProjectAssignment
- Task

Commands:

```bash
alembic revision --autogenerate -m "init_domain_models"
alembic upgrade head
```

Expected result:

- a new migration file under `alembic/versions`
- all domain tables created in PostgreSQL

If your project already has migrations, you may only need:

```bash
alembic upgrade head
```

## 4. Seed test data

The query/filter/group endpoints need real data to test.

For the robustness lab:

```bash
python seed_data.py
```

For your own project, run your own seed script or insert data manually.

## 5. Check `filterx.yaml`

`filterx.yaml` is the contract between FilterX and your project. It tells the CLI:

- where the backend app is
- where SQLAlchemy models are
- where generated backend files go
- where the Angular app is
- where generated frontend files go
- which host files may be patched

For the robustness lab, the important paths are:

```yaml
python:
  app_import: app.main:app
  base_class_import: app.database:Base
  models_package: app.models
  session_dependency_import: app.database:get_db

backend:
  enabled: true
  api_prefix: /api
  generated_package: app/filterx_generated
  mount_file: app/main.py
  mount_anchor: "# FILTERX:ROUTER_MOUNT"

frontend:
  enabled: true
  workspace_root: frontend
  generated_root: frontend/src/app/filterx-generated
  routes_file: frontend/src/app/app.routes.ts
  routes_anchor: "// FILTERX:ROUTES"
  app_config_file: frontend/src/app/app.config.ts
  app_config_anchor: "// FILTERX:PROVIDERS"
```

For a different project layout, change these values. Examples:

- backend in `backend/app`: use paths like `backend/app/main.py`
- frontend in `client`: set `frontend.workspace_root: client`
- models in `backend/app/models`: set `python.models_package` to the actual import package

Use forward slashes in `filterx.yaml` paths. They work on Windows, Linux, and macOS.

## 6. Add the required anchors

Anchors are not optional. They are the exact locations where FilterX is allowed to patch host files.

### Backend router mount anchor

Open the file configured by `backend.mount_file`.

For the robustness lab:

```text
app/main.py
```

Add this comment after your FastAPI app and normal routers are defined:

```python
# FILTERX:ROUTER_MOUNT
```

FilterX will replace/expand code around that anchor to mount the generated `/api/filterx` router.

### Frontend route anchor

Open the file configured by `frontend.routes_file`.

For the robustness lab:

```text
frontend/src/app/app.routes.ts
```

Add this comment inside the `Routes` array:

```ts
// FILTERX:ROUTES
```

Example:

```ts
import { Routes } from "@angular/router";

export const routes: Routes = [
  { path: "", redirectTo: "companies", pathMatch: "full" },
  // FILTERX:ROUTES
];
```

FilterX will insert generated entity routes at that anchor.

### Frontend provider anchor

Open the file configured by `frontend.app_config_file`.

For the robustness lab:

```text
frontend/src/app/app.config.ts
```

Add this comment inside the `providers` array:

```ts
// FILTERX:PROVIDERS
```

Example:

```ts
export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    // FILTERX:PROVIDERS
  ],
};
```

FilterX will add Angular providers required by the generated UI, such as HTTP, animations, and PrimeNG configuration.

## 7. Scan the project

This reads `filterx.yaml`, imports your app/models, and writes `.filterx` artifacts.

```bash
filterx scan --project-root . --config filterx.yaml --no-dry-run --json
```

Expected for `filterx_robustness_lab`:

- 6 entities found
- cycle/composite-PK warnings may appear and are acceptable for this robustness lab

Generated:

- `.filterx/scan.json`
- `.filterx/diagnostics.json`
- `.filterx/plan.json`

## 8. Generate the backend FilterX API

This creates the generic query/filter/group backend and mounts it in your FastAPI app.

```bash
filterx backend install --project-root . --config filterx.yaml --no-dry-run --yes --json
```

Generated under `backend.generated_package`, which is `app/filterx_generated` in the robustness lab:

- `entities.py`
- `metadata.py`
- `router_factory.py`
- `router.py`
- `predicates.py`

Patched:

- the file configured by `backend.mount_file`
- for the robustness lab: `app/main.py`, around `# FILTERX:ROUTER_MOUNT`

## 9. Validate backend integration

```bash
filterx backend validate --project-root . --config filterx.yaml --json
```

Then start the backend:

```bash
uvicorn app.main:app --reload
```

Change `app.main:app` if your `python.app_import` uses a different import path.

Check in a browser or API client:

```text
GET http://localhost:8000/api/filterx/metadata
```

Expected API routes with default `backend.api_prefix: /api`:

- `GET /api/filterx/metadata`
- `GET /api/filterx/{entity}/metadata`
- `GET /api/filterx/{entity}`
- `GET /api/filterx/{entity}/query`
- `POST /api/filterx/{entity}/filter`
- `GET /api/filterx/{entity}/group-by/{field}`
- `POST /api/filterx/{entity}/group-by/{field}/filter`

Stop the backend only if you need the terminal for the next commands. Otherwise keep it running.

## 10. Generate the frontend FilterX UI

This step is mandatory for the full FilterX integration.

```bash
filterx frontend install --project-root . --config filterx.yaml --no-dry-run --yes --json
```

Generated/copied under the configured Angular workspace:

- `frontend/src/app/core/**`
- `frontend/src/app/shared/**`
- `frontend/src/app/filterx-generated/entities/*.config.ts`
- `frontend/src/app/filterx-generated/pages/*.page.ts`
- `frontend/src/app/filterx-generated/routes.ts`

Patched:

- `frontend/package.json`
- `frontend/angular.json`
- `frontend/proxy.conf.cjs`
- `frontend/src/styles.css`
- `frontend/src/app/app.routes.ts`
- `frontend/src/app/app.config.ts`

If your Angular workspace is not named `frontend`, replace `frontend` with `frontend.workspace_root` from your `filterx.yaml`.

## 11. Install frontend dependencies

The frontend generator adds Angular/PrimeNG dependencies to `package.json`. Install them now.

```bash
cd frontend
npm install
cd ..
```

If your Angular workspace is `client`, run:

```bash
cd client
npm install
cd ..
```

## 12. Validate full FilterX integration

```bash
filterx validate --project-root . --config filterx.yaml --json
```

Expected:

```json
{
  "errors": [],
  "warnings": [],
  "error_count": 0,
  "warning_count": 0
}
```

## 13. Build the frontend

```bash
cd frontend
npm run build
cd ..
```

Expected:

- Angular build completes successfully
- warnings about unused imports may appear and are not necessarily blocking

## 14. Run backend and frontend together

Terminal 1, project root:

```bash
uvicorn app.main:app --reload
```

Terminal 2, Angular workspace:

```bash
cd frontend
npm start
```

Open:

```text
http://localhost:4200
```

For the robustness lab, generated entity routes include:

- `http://localhost:4200/companies`
- `http://localhost:4200/departments`
- `http://localhost:4200/employees`
- `http://localhost:4200/projects`
- `http://localhost:4200/project-assignments`
- `http://localhost:4200/tasks`

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

After anchors and `filterx.yaml` are correct, this command runs scan, enabled installs, and validation together:

```bash
filterx install --project-root . --config filterx.yaml --no-dry-run --yes --json
```

For first-time debugging, the numbered manual path above is easier to understand.

## What the generated UI calls

The Angular UI talks to the generated backend through `/api/filterx`:

- the list screen calls `GET /api/filterx/{entity}`
- the advanced search panel calls `GET /api/filterx/{entity}/metadata`
- filter trees call `POST /api/filterx/{entity}/filter`
- grouping calls `/api/filterx/{entity}/group-by/{field}`

The CLI also creates `proxy.conf.cjs` so local Angular dev requests can reach your FastAPI server.

## Common issues

- `ANCHOR_NOT_FOUND`: the configured anchor is missing from the configured file.
- `SCAN_FILE_MISSING`: run `filterx scan` or `filterx install` with writes enabled.
- Route conflict on `/api/filterx/...`: change `backend.api_prefix` or remove the conflicting host route.
- Angular icons appear as empty circles: restart `npm start`; `angular.json` must include `node_modules/primeicons/primeicons.css`.
- Frontend API calls fail: confirm the backend is running and `proxy.conf.cjs` targets the correct backend URL.

## Can this README include GIFs?

Not automatically. The commands above are text-first so they work on every OS and in CI. If you want terminal GIFs later, record them with a local tool such as VHS or asciinema after the commands are stable, then add the generated media under a docs/assets folder.

## Full CLI reference

See [tools/filterx/README.md](tools/filterx/README.md).
