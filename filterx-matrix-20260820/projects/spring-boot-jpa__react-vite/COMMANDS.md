# Reproducible commands: spring-boot-jpa + react-vite

Replace `<PROJECT_ROOT>` and `<REPO_ROOT>`. Commands are ordered exactly as qualification ran them; runtime commands marked as separate terminals must run concurrently.

## PowerShell

```powershell
Set-Location <PROJECT_ROOT>
# Verify the untouched host first
& "C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\filterx-matrix-20260820\_tooling\apache-maven-3.9.11\bin\mvn.cmd" -q -DskipTests compile
& "C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\filterx-matrix-20260820\_tooling\apache-maven-3.9.11\bin\mvn.cmd" -q -DskipTests package
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
& "C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\filterx-matrix-20260820\_tooling\apache-maven-3.9.11\bin\mvn.cmd" -q -DskipTests package
Push-Location frontend
npm install --no-audit --no-fund
npm run build
Pop-Location
# Backend terminal
java -jar target/filterx-matrix-1.0.0.jar --server.port=8000
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
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\filterx-matrix-20260820\_tooling\apache-maven-3.9.11\bin\mvn.cmd" -q -DskipTests compile
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\filterx-matrix-20260820\_tooling\apache-maven-3.9.11\bin\mvn.cmd" -q -DskipTests package
(cd frontend && npm install --no-audit --no-fund && npm run build)
# Integrate FilterX and repeat installs to prove idempotency
filterx scan --project-root . --config filterx.yaml --yes --json
filterx backend install --project-root . --config filterx.yaml --yes --json
filterx frontend install --project-root . --config filterx.yaml --yes --json
filterx validate --project-root . --config filterx.yaml --yes --json
filterx backend install --project-root . --config filterx.yaml --yes --json
filterx frontend install --project-root . --config filterx.yaml --yes --json
# Reconcile generated dependencies and rebuild
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\filterx-matrix-20260820\_tooling\apache-maven-3.9.11\bin\mvn.cmd" -q -DskipTests package
(cd frontend && npm install --no-audit --no-fund && npm run build)
# Backend terminal
java -jar target/filterx-matrix-1.0.0.jar --server.port=8000
# Frontend terminal (from <PROJECT_ROOT>/frontend)
npm run dev
# Roll back frontend then backend in reverse patch order
filterx rollback --project-root . --config filterx.yaml --yes --json
filterx rollback --project-root . --config filterx.yaml --yes --json
```

## Exact recorded qualification subprocesses

### `spring-host-compile`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite
C:/filterx-matrix-20260820/_tooling/apache-maven-3.9.11/bin/mvn.cmd -q -DskipTests compile
```

### `frontend-host-npm-install`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite\frontend
"C:\Program Files\nodejs\npm.CMD" install --no-audit --no-fund
```

### `host-before-filterx-package`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite
C:/filterx-matrix-20260820/_tooling/apache-maven-3.9.11/bin/mvn.cmd -q -DskipTests package
```

### `host-before-filterx-frontend-build`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite\frontend
"C:\Program Files\nodejs\npm.CMD" run build
```

### `scan`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli scan --project-root C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite --config C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite\filterx.yaml --yes --json
```

### `backend-install`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli backend install --project-root C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite --config C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite\filterx.yaml --yes --json
```

### `frontend-install`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli frontend install --project-root C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite --config C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite\filterx.yaml --yes --json
```

### `validate`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli validate --project-root C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite --config C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite\filterx.yaml --yes --json
```

### `backend-reinstall`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli backend install --project-root C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite --config C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite\filterx.yaml --yes --json
```

### `frontend-reinstall`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli frontend install --project-root C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite --config C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite\filterx.yaml --yes --json
```

### `host-after-filterx-package`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite
C:/filterx-matrix-20260820/_tooling/apache-maven-3.9.11/bin/mvn.cmd -q -DskipTests package
```

### `frontend-npm-install`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite\frontend
"C:\Program Files\nodejs\npm.CMD" install --no-audit --no-fund
```

### `host-after-filterx-frontend-build`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite\frontend
"C:\Program Files\nodejs\npm.CMD" run build
```

### `rollback-list`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli rollback --list --project-root C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite --config C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite\filterx.yaml --yes --json
```

### `rollback-01`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli rollback --patch-id patch-20260820T200822.521613Z-cb065afc --project-root C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite --config C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite\filterx.yaml --yes --json
```

### `rollback-02`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli rollback --patch-id patch-20260820T200822.249746Z-1c5a7385 --project-root C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite --config C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite\filterx.yaml --yes --json
```

### `rollback-03`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli rollback --patch-id patch-20260820T200821.673852Z-3efdec1a --project-root C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite --config C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite\filterx.yaml --yes --json
```

### `rollback-04`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite
"C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\.venv\Scripts\python.exe" -m filterx.cli rollback --patch-id patch-20260820T200821.429701Z-67c818b4 --project-root C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite --config C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite\filterx.yaml --yes --json
```

### `post-rollback-frontend-npm-install`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite\frontend
"C:\Program Files\nodejs\npm.CMD" install --no-audit --no-fund
```

### `host-before-filterx-package`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite
C:/filterx-matrix-20260820/_tooling/apache-maven-3.9.11/bin/mvn.cmd -q -DskipTests package
```

### `host-before-filterx-frontend-build`

```powershell
Set-Location C:\filterx-matrix-20260820\projects\spring-boot-jpa__react-vite\frontend
"C:\Program Files\nodejs\npm.CMD" run build
```
