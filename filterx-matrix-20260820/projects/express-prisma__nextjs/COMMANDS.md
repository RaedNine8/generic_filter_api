# Reproducible commands: express-prisma + nextjs

Replace `<PROJECT_ROOT>` and `<REPO_ROOT>`. Commands are ordered exactly as qualification ran them; runtime commands marked as separate terminals must run concurrently.

## PowerShell

```powershell
Set-Location <PROJECT_ROOT>
# Verify the untouched host first
npm install --no-audit --no-fund
npm exec prisma generate
npm exec prisma db push -- --skip-generate
npm run seed
npm run build
Push-Location frontend
npm install --no-audit --no-fund
npm run build
Pop-Location
# Integrate FilterX and repeat installs to prove idempotency
filterx scan --project-root . --config filterx.yaml --yes --json
filterx backend install --project-root . --config filterx.yaml --yes --json
filterx frontend install --project-root . --config filterx.yaml --yes --json
filterx validate --project-root . --config filterx.yaml --yes --json
filterx backend install --project-root . --config filterx.yaml --yes --json
filterx frontend install --project-root . --config filterx.yaml --yes --json
# Reconcile generated dependencies and rebuild
npm install --no-audit --no-fund
npm exec prisma db push -- --skip-generate
npm run seed
npm run build
Push-Location frontend
npm install --no-audit --no-fund
npm run build
Pop-Location
# Backend terminal
npm start
# Frontend terminal (from <PROJECT_ROOT>/frontend)
npm run dev
# Roll back frontend then backend in reverse patch order
filterx rollback --project-root . --config filterx.yaml --yes --json
filterx rollback --project-root . --config filterx.yaml --yes --json
```

## POSIX shell

```sh
cd <PROJECT_ROOT>
# Verify the untouched host first
npm install --no-audit --no-fund
npm exec prisma generate
npm exec prisma db push -- --skip-generate
npm run seed
npm run build
(cd frontend && npm install --no-audit --no-fund && npm run build)
# Integrate FilterX and repeat installs to prove idempotency
filterx scan --project-root . --config filterx.yaml --yes --json
filterx backend install --project-root . --config filterx.yaml --yes --json
filterx frontend install --project-root . --config filterx.yaml --yes --json
filterx validate --project-root . --config filterx.yaml --yes --json
filterx backend install --project-root . --config filterx.yaml --yes --json
filterx frontend install --project-root . --config filterx.yaml --yes --json
# Reconcile generated dependencies and rebuild
npm install --no-audit --no-fund
npm exec prisma db push -- --skip-generate
npm run seed
npm run build
(cd frontend && npm install --no-audit --no-fund && npm run build)
# Backend terminal
npm start
# Frontend terminal (from <PROJECT_ROOT>/frontend)
npm run dev
# Roll back frontend then backend in reverse patch order
filterx rollback --project-root . --config filterx.yaml --yes --json
filterx rollback --project-root . --config filterx.yaml --yes --json
```

## Exact recorded qualification subprocesses

### `backend-npm-install`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs
"C:\Program Files\nodejs\npm.CMD" install --no-audit --no-fund
```

### `prisma-generate`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs
"C:\Program Files\nodejs\npm.CMD" exec prisma generate
```

### `frontend-host-npm-install`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs\frontend
"C:\Program Files\nodejs\npm.CMD" install --no-audit --no-fund
```

### `host-before-filterx-db-push`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs
"C:\Program Files\nodejs\npm.CMD" exec prisma db push -- --skip-generate
```

### `host-before-filterx-seed`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs
"C:\Program Files\nodejs\npm.CMD" run seed
```

### `host-before-filterx-build`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs
"C:\Program Files\nodejs\npm.CMD" run build
```

### `host-before-filterx-frontend-build`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs\frontend
"C:\Program Files\nodejs\npm.CMD" run build
```

### `scan`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli scan --project-root C:\filterx-matrix-20260820\projects\express-prisma__nextjs --config C:\filterx-matrix-20260820\projects\express-prisma__nextjs\filterx.yaml --yes --json
```

### `backend-install`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli backend install --project-root C:\filterx-matrix-20260820\projects\express-prisma__nextjs --config C:\filterx-matrix-20260820\projects\express-prisma__nextjs\filterx.yaml --yes --json
```

### `frontend-install`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli frontend install --project-root C:\filterx-matrix-20260820\projects\express-prisma__nextjs --config C:\filterx-matrix-20260820\projects\express-prisma__nextjs\filterx.yaml --yes --json
```

### `validate`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli validate --project-root C:\filterx-matrix-20260820\projects\express-prisma__nextjs --config C:\filterx-matrix-20260820\projects\express-prisma__nextjs\filterx.yaml --yes --json
```

### `backend-reinstall`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli backend install --project-root C:\filterx-matrix-20260820\projects\express-prisma__nextjs --config C:\filterx-matrix-20260820\projects\express-prisma__nextjs\filterx.yaml --yes --json
```

### `frontend-reinstall`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli frontend install --project-root C:\filterx-matrix-20260820\projects\express-prisma__nextjs --config C:\filterx-matrix-20260820\projects\express-prisma__nextjs\filterx.yaml --yes --json
```

### `backend-npm-install-after-filterx`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs
"C:\Program Files\nodejs\npm.CMD" install --no-audit --no-fund
```

### `host-after-filterx-db-push`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs
"C:\Program Files\nodejs\npm.CMD" exec prisma db push -- --skip-generate
```

### `host-after-filterx-seed`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs
"C:\Program Files\nodejs\npm.CMD" run seed
```

### `host-after-filterx-build`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs
"C:\Program Files\nodejs\npm.CMD" run build
```

### `frontend-npm-install`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs\frontend
"C:\Program Files\nodejs\npm.CMD" install --no-audit --no-fund
```

### `host-after-filterx-frontend-build`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs\frontend
"C:\Program Files\nodejs\npm.CMD" run build
```

### `rollback-list`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli rollback --list --project-root C:\filterx-matrix-20260820\projects\express-prisma__nextjs --config C:\filterx-matrix-20260820\projects\express-prisma__nextjs\filterx.yaml --yes --json
```

### `rollback-01`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli rollback --patch-id patch-20260820T200030.013572Z-005decfd --project-root C:\filterx-matrix-20260820\projects\express-prisma__nextjs --config C:\filterx-matrix-20260820\projects\express-prisma__nextjs\filterx.yaml --yes --json
```

### `rollback-02`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli rollback --patch-id patch-20260820T200029.673219Z-1ab20f7e --project-root C:\filterx-matrix-20260820\projects\express-prisma__nextjs --config C:\filterx-matrix-20260820\projects\express-prisma__nextjs\filterx.yaml --yes --json
```

### `rollback-03`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli rollback --patch-id patch-20260820T200029.199442Z-0c064771 --project-root C:\filterx-matrix-20260820\projects\express-prisma__nextjs --config C:\filterx-matrix-20260820\projects\express-prisma__nextjs\filterx.yaml --yes --json
```

### `rollback-04`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli rollback --patch-id patch-20260820T200028.953907Z-1e98925f --project-root C:\filterx-matrix-20260820\projects\express-prisma__nextjs --config C:\filterx-matrix-20260820\projects\express-prisma__nextjs\filterx.yaml --yes --json
```

### `post-rollback-frontend-npm-install`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs\frontend
"C:\Program Files\nodejs\npm.CMD" install --no-audit --no-fund
```

### `host-before-filterx-db-push`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs
"C:\Program Files\nodejs\npm.CMD" exec prisma db push -- --skip-generate
```

### `host-before-filterx-seed`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs
"C:\Program Files\nodejs\npm.CMD" run seed
```

### `host-before-filterx-build`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs
"C:\Program Files\nodejs\npm.CMD" run build
```

### `host-before-filterx-frontend-build`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__nextjs\frontend
"C:\Program Files\nodejs\npm.CMD" run build
```
