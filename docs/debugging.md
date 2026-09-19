# Debugging FilterX

FilterX provides VS Code debugger definitions for the CLI and for every supported host combination:

| Target                       | VS Code debugger                     |    Typical port |
| ---------------------------- | ------------------------------------ | --------------: |
| FilterX CLI, pytest, FastAPI | Python Debugger (`debugpy`)          | 5678 for attach |
| Express and Next.js          | Built-in JavaScript/Node debugger    | 9229 for attach |
| Spring Boot                  | Java debugger/JDWP                   | 5005 for attach |
| Angular, React/Vite, Vue     | Built-in JavaScript browser debugger | application URL |

## Debug this repository

Open the repository root in VS Code, select **Run and Debug**, and choose one of the committed `FilterX Repo:` or `FilterX Matrix:` launchers.

Useful launchers include:

- `FilterX Repo: CLI validate matrix project` to step through CLI parsing, configuration, scanning, renderers, patching, and validation.
- `FilterX Repo: all CLI tests` or `FilterX Repo: current pytest file` to debug tests.
- `FilterX Repo: FastAPI + Angular` to launch the main backend and frontend together.
- Matrix compounds for Express/React and Spring/Vue, plus a Next.js launcher.
- Attach configurations for externally launched Python, Node, and Java processes.

The repository recommends Python/debugpy, Java, Angular, and Vue extensions in `.vscode/extensions.json`. VS Code already includes the JavaScript and browser debugger.

Set breakpoints in `tools/filterx/filterx/` to inspect the generator. Set breakpoints in a matrix project's generated files to inspect generated host runtime behavior. Python launchers use `justMyCode: false`, so an editable FilterX installation can be stepped into from a host project.

## Install debuggers into an integrated project

Run from the shared project root containing `filterx.yaml`:

```powershell
filterx debug install --project-root . --config filterx.yaml --no-dry-run --yes --json
filterx debug validate --project-root . --config filterx.yaml --json
```

FilterX reads the effective backend/frontend frameworks and paths from `filterx.yaml`. It emits only the relevant launchers, tasks, extension recommendations, and a `FilterX: Full stack` compound.

The default application ports are:

- Backend: 8000
- Angular: 4200
- React/Vite and Vue/Vite: 5173
- Next.js: 3000

Override ports when required:

```powershell
filterx debug install --project-root . --config filterx.yaml --backend-port 8100 --frontend-port 4300 --no-dry-run --yes --json
```

Re-run `debug install` after changing framework or path configuration. It is idempotent and updates only files recorded in `.filterx/debug.json`.

## Existing VS Code configuration

The default `--mode auto` is deliberately conservative:

- If the host has no debugger files, FilterX writes `.vscode/launch.json`, `.vscode/tasks.json`, and, when available, `.vscode/extensions.json`.
- If the host already owns launch/tasks files, FilterX writes `filterx-debug.code-workspace` instead. Open that workspace to use FilterX launchers while leaving the host's JSON/JSONC and comments unchanged.
- An existing `.vscode/settings.json` is never modified.
- An existing `.vscode/extensions.json` is preserved.

You can select a mode explicitly:

```powershell
filterx debug install --mode vscode --no-dry-run
filterx debug install --mode workspace --no-dry-run
```

Explicit `vscode` mode refuses to overwrite an unowned destination. Remove or rename the existing files, or use workspace mode.

## Launch and attach workflows

### FastAPI

The generated launcher runs the configured `python.app_import` with Uvicorn and sets `PYTHONPATH` to `project.backend_root`. If the backend root contains `.env`, it is loaded. Put breakpoints in host routes, generated FilterX modules, security hooks, or the installed editable FilterX package.

To attach to a separately launched process, start it with debugpy listening on localhost port 5678 and select `FilterX: Attach Python backend`.

### Express + Prisma

The generated launch builds TypeScript first and runs the JavaScript program extracted from the host `start` script. It enables source maps, sets the configured backend port through `PORT`, and runs Prisma client generation first when a schema is present.

For an external process started with Node inspector on port 9229, select `FilterX: Attach Node backend`.

### Spring Boot + JPA

The generated Java launcher uses `backend.spring.application_class`, the configured module directory, and the selected backend port. If the main class is absent, VS Code prompts for its fully qualified name.

For Maven/Gradle or container launches exposing JDWP on localhost port 5005, select `FilterX: Attach Java backend`.

### Frontends

Angular, React/Vite, and Vue launch the configured npm development script as a background task and start a Chrome debugging session against the framework's URL. Next.js starts its Node dev process and opens a browser debugger when the server is ready. TypeScript, TSX, and Vue breakpoints rely on each host's source maps.

If the server-ready detector does not recognize customized tool output, start the npm script manually and use a browser launch/attach definition without `preLaunchTask`.

## API keys and environment variables

Do not place secrets in launch files. FastAPI automatically uses the backend `.env` when present; other processes inherit the integrated terminal environment. Set `GROQ_API_KEY`, `GEMINI_API_KEY`, database credentials, and other secrets in the host's normal secret mechanism before launching. Keyless local OpenAI-compatible providers need no API key.

## Validation and safe removal

Validation is read-only:

```powershell
filterx debug validate --project-root . --config filterx.yaml --json
```

It detects missing, malformed, stale, or post-install edited generated files. Warnings can fail CI with `--fail-on-warning`.

Removal defaults to preview mode. Apply it explicitly:

```powershell
filterx debug remove --project-root . --dry-run --json
filterx debug remove --project-root . --no-dry-run --yes --json
```

FilterX removes only paths recorded in `.filterx/debug.json`. If a generated debugger file was edited after installation, removal is blocked rather than deleting those edits.

## Troubleshooting

- **Python debugger unavailable:** install the recommended Python and Python Debugger extensions, select the host virtual environment, and ensure Uvicorn/pytest is installed there.
- **TypeScript breakpoint is unbound:** verify the host builds source maps and that generated `outFiles`/`webRoot` point at the configured backend/frontend root.
- **Prisma build fails:** run dependency installation and Prisma generation in the host first.
- **Java launcher fails:** install JDK 17+, the Extension Pack for Java, and set `backend.spring.application_class`.
- **Port already in use:** regenerate with `--backend-port` and/or `--frontend-port`.
- **Full-stack launch races:** frontend API calls may briefly fail while the backend starts; retry after the backend is listening.
