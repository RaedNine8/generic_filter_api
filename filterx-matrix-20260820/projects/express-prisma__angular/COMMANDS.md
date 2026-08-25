# Reproducible commands: express-prisma + angular

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
npm start
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
npm start
# Roll back frontend then backend in reverse patch order
filterx rollback --project-root . --config filterx.yaml --yes --json
filterx rollback --project-root . --config filterx.yaml --yes --json
```

## Exact recorded qualification subprocesses

### `backend-npm-install`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular
"C:\Program Files\nodejs\npm.CMD" install --no-audit --no-fund
```

### `prisma-generate`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular
"C:\Program Files\nodejs\npm.CMD" exec prisma generate
```

### `frontend-host-npm-install`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular\frontend
"C:\Program Files\nodejs\npm.CMD" install --no-audit --no-fund
```

### `host-before-filterx-db-push`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular
"C:\Program Files\nodejs\npm.CMD" exec prisma db push -- --skip-generate
```

### `host-before-filterx-seed`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular
"C:\Program Files\nodejs\npm.CMD" run seed
```

### `host-before-filterx-build`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular
"C:\Program Files\nodejs\npm.CMD" run build
```

### `host-before-filterx-frontend-build`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular\frontend
"C:\Program Files\nodejs\npm.CMD" run build
```

### `scan`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli scan --project-root C:\filterx-matrix-20260820\projects\express-prisma__angular --config C:\filterx-matrix-20260820\projects\express-prisma__angular\filterx.yaml --yes --json
```

### `backend-install`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli backend install --project-root C:\filterx-matrix-20260820\projects\express-prisma__angular --config C:\filterx-matrix-20260820\projects\express-prisma__angular\filterx.yaml --yes --json
```

### `frontend-install`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli frontend install --project-root C:\filterx-matrix-20260820\projects\express-prisma__angular --config C:\filterx-matrix-20260820\projects\express-prisma__angular\filterx.yaml --yes --json
```

### `validate`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli validate --project-root C:\filterx-matrix-20260820\projects\express-prisma__angular --config C:\filterx-matrix-20260820\projects\express-prisma__angular\filterx.yaml --yes --json
```

### `backend-reinstall`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli backend install --project-root C:\filterx-matrix-20260820\projects\express-prisma__angular --config C:\filterx-matrix-20260820\projects\express-prisma__angular\filterx.yaml --yes --json
```

### `frontend-reinstall`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli frontend install --project-root C:\filterx-matrix-20260820\projects\express-prisma__angular --config C:\filterx-matrix-20260820\projects\express-prisma__angular\filterx.yaml --yes --json
```

### `backend-npm-install-after-filterx`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular
"C:\Program Files\nodejs\npm.CMD" install --no-audit --no-fund
```

### `host-after-filterx-db-push`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular
"C:\Program Files\nodejs\npm.CMD" exec prisma db push -- --skip-generate
```

### `host-after-filterx-seed`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular
"C:\Program Files\nodejs\npm.CMD" run seed
```

### `host-after-filterx-build`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular
"C:\Program Files\nodejs\npm.CMD" run build
```

### `frontend-npm-install`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular\frontend
"C:\Program Files\nodejs\npm.CMD" install --no-audit --no-fund
```

### `host-after-filterx-frontend-build`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular\frontend
"C:\Program Files\nodejs\npm.CMD" run build
```

### `rollback-list`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli rollback --list --project-root C:\filterx-matrix-20260820\projects\express-prisma__angular --config C:\filterx-matrix-20260820\projects\express-prisma__angular\filterx.yaml --yes --json
```

### `rollback-01`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli rollback --patch-id patch-20260820T195607.771486Z-339203c6 --project-root C:\filterx-matrix-20260820\projects\express-prisma__angular --config C:\filterx-matrix-20260820\projects\express-prisma__angular\filterx.yaml --yes --json
```

### `rollback-02`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli rollback --patch-id patch-20260820T195607.343407Z-77ce9882 --project-root C:\filterx-matrix-20260820\projects\express-prisma__angular --config C:\filterx-matrix-20260820\projects\express-prisma__angular\filterx.yaml --yes --json
```

### `rollback-03`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli rollback --patch-id patch-20260820T195606.734861Z-7a39c26d --project-root C:\filterx-matrix-20260820\projects\express-prisma__angular --config C:\filterx-matrix-20260820\projects\express-prisma__angular\filterx.yaml --yes --json
```

### `rollback-04`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli rollback --patch-id patch-20260820T195606.443186Z-04c6bc66 --project-root C:\filterx-matrix-20260820\projects\express-prisma__angular --config C:\filterx-matrix-20260820\projects\express-prisma__angular\filterx.yaml --yes --json
```

### `post-rollback-frontend-npm-install`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular\frontend
"C:\Program Files\nodejs\npm.CMD" install --no-audit --no-fund
```

### `host-before-filterx-db-push`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular
"C:\Program Files\nodejs\npm.CMD" exec prisma db push -- --skip-generate
```

### `host-before-filterx-seed`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular
"C:\Program Files\nodejs\npm.CMD" run seed
```

### `host-before-filterx-build`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular
"C:\Program Files\nodejs\npm.CMD" run build
```

### `host-before-filterx-frontend-build`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\express-prisma__angular\frontend
"C:\Program Files\nodejs\npm.CMD" run build
```
