# FilterX standalone 12-combination qualification report

## Outcome

- Standalone projects qualified: **12/12**
- External project root: `C:\Users\raedn\OneDrive\Bureau\FILES\DEV FILES\MAIN_PROJECTS\generic_filter_api\filterx-matrix-20260820\projects`
- Each project was scaffolded from an empty directory and received one complete, validated `filterx.yaml` before any FilterX lifecycle command.
- Every FastAPI project used its own `.venv`; Maven was isolated under the matrix root.
- A passing result requires host builds/runtime before integration, CLI install/validation/idempotency, integrated builds/runtime/contract checks, reverse rollback, and post-rollback host verification.

## Matrix

| Backend | Frontend | Status | Checks | Commands | Evidence |
| --- | --- | --- | ---: | ---: | --- |
| `fastapi-sqlalchemy` | `angular` | passed | 22 | 22 | [projects/fastapi-sqlalchemy__angular/result.json](projects/fastapi-sqlalchemy__angular/result.json) |
| `fastapi-sqlalchemy` | `react-vite` | passed | 22 | 22 | [projects/fastapi-sqlalchemy__react-vite/result.json](projects/fastapi-sqlalchemy__react-vite/result.json) |
| `fastapi-sqlalchemy` | `nextjs` | passed | 22 | 22 | [projects/fastapi-sqlalchemy__nextjs/result.json](projects/fastapi-sqlalchemy__nextjs/result.json) |
| `fastapi-sqlalchemy` | `vue` | passed | 22 | 22 | [projects/fastapi-sqlalchemy__vue/result.json](projects/fastapi-sqlalchemy__vue/result.json) |
| `express-prisma` | `angular` | passed | 22 | 29 | [projects/express-prisma__angular/result.json](projects/express-prisma__angular/result.json) |
| `express-prisma` | `react-vite` | passed | 22 | 29 | [projects/express-prisma__react-vite/result.json](projects/express-prisma__react-vite/result.json) |
| `express-prisma` | `nextjs` | passed | 22 | 29 | [projects/express-prisma__nextjs/result.json](projects/express-prisma__nextjs/result.json) |
| `express-prisma` | `vue` | passed | 22 | 29 | [projects/express-prisma__vue/result.json](projects/express-prisma__vue/result.json) |
| `spring-boot-jpa` | `angular` | passed | 22 | 21 | [projects/spring-boot-jpa__angular/result.json](projects/spring-boot-jpa__angular/result.json) |
| `spring-boot-jpa` | `react-vite` | passed | 22 | 21 | [projects/spring-boot-jpa__react-vite/result.json](projects/spring-boot-jpa__react-vite/result.json) |
| `spring-boot-jpa` | `nextjs` | passed | 22 | 21 | [projects/spring-boot-jpa__nextjs/result.json](projects/spring-boot-jpa__nextjs/result.json) |
| `spring-boot-jpa` | `vue` | passed | 22 | 21 | [projects/spring-boot-jpa__vue/result.json](projects/spring-boot-jpa__vue/result.json) |

## Required checks represented by each passing project

- `alternate-principal-row-security`
- `csv-export`
- `filtered-grouping`
- `filterx-idempotent-reinstall`
- `frontend-page-and-proxy`
- `grouping`
- `hidden-field-grouping-rejected`
- `host-before-filterx-runtime`
- `json-export`
- `metadata`
- `nested-and-or-in-null-filter`
- `nested-filter`
- `pagination-boundaries`
- `post-rollback-host-runtime`
- `rollback-exact-host-restore`
- `row-and-field-security`
- `search`
- `sort-descending`
- `url-equality`
- `url-in`
- `url-null`
- `xlsx-export`

Runtime contract checks cover metadata, URL equality/`in`/null grammar, search, descending sorting, pagination boundaries, relationship filters, nested AND/OR trees, grouping and filtered grouping, hidden-field rejection, row/field security, alternate principals, CSV/JSON/XLSX exports, and frontend page/proxy behavior.

## Product regressions found and fixed

1. Angular standalone config could call `provideAnimationsAsync()` without importing it.
2. Patch rollback used text mode and changed LF bytes to CRLF on Windows.
3. Cross-layer validation incorrectly required FastAPI and Angular files for every renderer.
4. Web frontend install JSON omitted operation counts needed to prove idempotency.
5. Spring and Express grouping could expose a field hidden by the field-visibility hook.
6. The JPA scanner emitted noncanonical `neq`/`contains`/`icontains` operations that the generated API and typed web clients did not support.

## Reproduction

Each project contains `COMMANDS.md` with PowerShell and POSIX commands in the same order as qualification. Raw subprocess evidence is under `.filterx/cli-logs/`; `result.json` records command, working directory, exit code, output, duration, checks, host baseline, and final status.

## Qualification boundary

These are deterministic local dummy applications using SQLite for FastAPI/Prisma and file-backed H2 for Spring. They prove generator integration and backend/frontend parity for the supported matrix; they do not replace testing against an application's production database, authentication provider, deployment proxy, or domain-specific hooks.
