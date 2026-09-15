# Reproducible commands: fastapi-sqlalchemy + vue

Replace `<PROJECT_ROOT>` and `<REPO_ROOT>`. Commands are ordered exactly as qualification ran them; runtime commands marked as separate terminals must run concurrently.

## PowerShell

```powershell
Set-Location <PROJECT_ROOT>
# Verify the untouched host first
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e <REPO_ROOT>\tools\filterx fastapi sqlalchemy uvicorn httpx
.\.venv\Scripts\python.exe seed.py
Push-Location frontend
npm install --no-audit --no-fund
npm run build
Pop-Location
# Integrate FilterX and repeat installs to prove idempotency
.\.venv\Scripts\filterx.exe scan --project-root . --config filterx.yaml --yes --json
.\.venv\Scripts\filterx.exe backend install --project-root . --config filterx.yaml --yes --json
.\.venv\Scripts\filterx.exe frontend install --project-root . --config filterx.yaml --yes --json
.\.venv\Scripts\filterx.exe validate --project-root . --config filterx.yaml --yes --json
.\.venv\Scripts\filterx.exe backend install --project-root . --config filterx.yaml --yes --json
.\.venv\Scripts\filterx.exe frontend install --project-root . --config filterx.yaml --yes --json
# Reconcile generated dependencies and rebuild
Push-Location frontend
npm install --no-audit --no-fund
npm run build
Pop-Location
# Backend terminal
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# Frontend terminal (from <PROJECT_ROOT>/frontend)
npm run dev
# Roll back frontend then backend in reverse patch order
.\.venv\Scripts\filterx.exe rollback --project-root . --config filterx.yaml --yes --json
.\.venv\Scripts\filterx.exe rollback --project-root . --config filterx.yaml --yes --json
```

## POSIX shell

```sh
cd <PROJECT_ROOT>
# Verify the untouched host first
python3 -m venv .venv
./.venv/bin/python -m pip install -e <REPO_ROOT>/tools/filterx fastapi sqlalchemy uvicorn httpx
./.venv/bin/python seed.py
(cd frontend && npm install --no-audit --no-fund && npm run build)
# Integrate FilterX and repeat installs to prove idempotency
./.venv/bin/filterx scan --project-root . --config filterx.yaml --yes --json
./.venv/bin/filterx backend install --project-root . --config filterx.yaml --yes --json
./.venv/bin/filterx frontend install --project-root . --config filterx.yaml --yes --json
./.venv/bin/filterx validate --project-root . --config filterx.yaml --yes --json
./.venv/bin/filterx backend install --project-root . --config filterx.yaml --yes --json
./.venv/bin/filterx frontend install --project-root . --config filterx.yaml --yes --json
# Reconcile generated dependencies and rebuild
(cd frontend && npm install --no-audit --no-fund && npm run build)
# Backend terminal
./.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# Frontend terminal (from <PROJECT_ROOT>/frontend)
npm run dev
# Roll back frontend then backend in reverse patch order
./.venv/bin/filterx rollback --project-root . --config filterx.yaml --yes --json
./.venv/bin/filterx rollback --project-root . --config filterx.yaml --yes --json
```

## Exact recorded qualification subprocesses

### `python-venv`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m venv .venv
```

### `python-dependencies`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue
C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\.venv\Scripts\python.exe -m pip install -e "C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\tools\filterx" fastapi sqlalchemy uvicorn httpx
```

### `frontend-host-npm-install`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\frontend
"C:\Program Files\nodejs\npm.CMD" install --no-audit --no-fund
```

### `host-before-filterx-seed`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue
C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\.venv\Scripts\python.exe seed.py
```

### `host-before-filterx-frontend-build`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\frontend
"C:\Program Files\nodejs\npm.CMD" run build
```

### `scan`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue
C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\.venv\Scripts\filterx.exe scan --project-root C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue --config C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\filterx.yaml --yes --json
```

### `backend-install`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue
C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\.venv\Scripts\filterx.exe backend install --project-root C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue --config C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\filterx.yaml --yes --json
```

### `frontend-install`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue
C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\.venv\Scripts\filterx.exe frontend install --project-root C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue --config C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\filterx.yaml --yes --json
```

### `validate`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue
C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\.venv\Scripts\filterx.exe validate --project-root C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue --config C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\filterx.yaml --yes --json
```

### `backend-reinstall`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue
C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\.venv\Scripts\filterx.exe backend install --project-root C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue --config C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\filterx.yaml --yes --json
```

### `frontend-reinstall`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue
C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\.venv\Scripts\filterx.exe frontend install --project-root C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue --config C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\filterx.yaml --yes --json
```

### `host-after-filterx-seed`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue
C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\.venv\Scripts\python.exe seed.py
```

### `frontend-npm-install`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\frontend
"C:\Program Files\nodejs\npm.CMD" install --no-audit --no-fund
```

### `host-after-filterx-frontend-build`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\frontend
"C:\Program Files\nodejs\npm.CMD" run build
```

### `rollback-list`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue
C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\.venv\Scripts\filterx.exe rollback --list --project-root C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue --config C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\filterx.yaml --yes --json
```

### `rollback-01`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue
C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\.venv\Scripts\filterx.exe rollback --patch-id patch-20260820T193513.490102Z-47f00e99 --project-root C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue --config C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\filterx.yaml --yes --json
```

### `rollback-02`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue
C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\.venv\Scripts\filterx.exe rollback --patch-id patch-20260820T193513.202469Z-ca37c7d6 --project-root C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue --config C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\filterx.yaml --yes --json
```

### `rollback-03`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue
C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\.venv\Scripts\filterx.exe rollback --patch-id patch-20260820T193512.570323Z-a7649347 --project-root C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue --config C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\filterx.yaml --yes --json
```

### `rollback-04`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue
C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\.venv\Scripts\filterx.exe rollback --patch-id patch-20260820T193512.273391Z-bfdf3c0e --project-root C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue --config C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\filterx.yaml --yes --json
```

### `post-rollback-frontend-npm-install`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\frontend
"C:\Program Files\nodejs\npm.CMD" install --no-audit --no-fund
```

### `host-before-filterx-seed`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue
C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\.venv\Scripts\python.exe seed.py
```

### `host-before-filterx-frontend-build`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\fastapi-sqlalchemy__vue\frontend
"C:\Program Files\nodejs\npm.CMD" run build
```
