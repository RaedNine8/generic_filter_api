"""Generate safe VS Code debugger definitions for FilterX host projects."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Mapping

from filterx.core.config import load_effective_config


STATE_PATH = ".filterx/debug.json"
WORKSPACE_PATH = "filterx-debug.code-workspace"


def _hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _relative(value: str | Path) -> str:
    normalized = Path(value).as_posix().strip("/")
    return "" if normalized in {"", "."} else normalized


def _workspace_path(relative: str) -> str:
    return "${workspaceFolder}" + (f"/{relative}" if relative else "")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"'{path}' must contain a JSON object")
    return value


def _package(project_root: Path, relative: str) -> dict[str, Any]:
    path = project_root / relative
    return _read_json(path) if path.exists() else {}


def _frontend_settings(cfg: Mapping[str, Any]) -> tuple[str, str]:
    frontend = cfg["frontend"]
    framework = str(frontend.get("framework", "angular"))
    if framework == "angular":
        return framework, _relative(str(frontend.get("workspace_root", "frontend")))
    target = frontend.get(framework.replace("-", "_"), {})
    return framework, _relative(str(target.get("workspace_root", frontend.get("workspace_root", "frontend"))))


def _frontend_url(framework: str, port: int) -> str:
    return f"http://127.0.0.1:{port}"


def _frontend_default_port(framework: str) -> int:
    return {"angular": 4200, "nextjs": 3000}.get(framework, 5173)


def _python_working_root(project_root: Path, cfg: Mapping[str, Any]) -> str:
    backend_root = _relative(str(cfg["project"].get("backend_root", ".")))
    module = str(cfg["python"].get("app_import", "app.main:app")).split(":", 1)[0]
    module_path = Path(*module.split("."))
    candidates = (module_path.with_suffix(".py"), module_path / "__init__.py")
    if any((project_root / candidate).exists() for candidate in candidates):
        return ""
    if any((project_root / backend_root / candidate).exists() for candidate in candidates):
        return backend_root
    return backend_root


def _config_reference(project_root: Path, config_path: Path) -> str:
    try:
        return config_path.relative_to(project_root).as_posix()
    except ValueError:
        return config_path.as_posix()


def _task(label: str, command: str, args: list[str], cwd: str, *, background: bool = False) -> dict[str, Any]:
    task: dict[str, Any] = {
        "label": label,
        "type": "shell",
        "command": command,
        "args": args,
        "options": {"cwd": cwd},
        "presentation": {"reveal": "always", "panel": "dedicated"},
        "problemMatcher": [],
    }
    if background:
        task["isBackground"] = True
        task["problemMatcher"] = [{
            "owner": "filterx-dev-server",
            "pattern": [{"regexp": "^(.*)$", "message": 1}],
            "background": {
                "activeOnStart": True,
                "beginsPattern": ".+",
                "endsPattern": "(Local:.*https?://|Application bundle generation complete|Compiled successfully|ready - started server|Ready in)",
            },
        }]
    return task


def _backend_debug(project_root: Path, cfg: Mapping[str, Any], backend_port: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], list[dict[str, str]]]:
    backend = cfg["backend"]
    framework = str(backend.get("framework", "fastapi-sqlalchemy"))
    configurations: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []
    extensions: list[str] = []
    warnings: list[dict[str, str]] = []
    if not backend.get("enabled", True):
        return configurations, tasks, extensions, warnings

    if framework == "fastapi-sqlalchemy":
        root = _python_working_root(project_root, cfg)
        cwd = _workspace_path(root)
        app = str(cfg["python"].get("app_import", "app.main:app"))
        launch: dict[str, Any] = {
            "name": "FilterX: FastAPI backend",
            "type": "debugpy",
            "request": "launch",
            "module": "uvicorn",
            "args": [app, "--host", "127.0.0.1", "--port", str(backend_port)],
            "cwd": cwd,
            "env": {"PYTHONPATH": cwd},
            "console": "integratedTerminal",
            "justMyCode": False,
            "subProcess": True,
        }
        env_file = project_root / root / ".env"
        if env_file.exists():
            launch["envFile"] = _workspace_path(f"{root}/.env" if root else ".env")
        configurations.extend([launch, {
            "name": "FilterX: Attach Python backend",
            "type": "debugpy",
            "request": "attach",
            "connect": {"host": "127.0.0.1", "port": 5678},
            "justMyCode": False,
        }])
        extensions.extend(["ms-python.python", "ms-python.debugpy"])
    elif framework == "express-prisma":
        express = backend.get("express", {})
        package_rel = _relative(str(express.get("package_json", "package.json")))
        root = _relative(Path(package_rel).parent)
        cwd = _workspace_path(root)
        package = _package(project_root, package_rel)
        scripts = package.get("scripts", {}) if isinstance(package.get("scripts"), dict) else {}
        start = str(scripts.get("start", ""))
        program_match = re.fullmatch(r"node\s+(?:--[^ ]+\s+)*([^ ]+)(?:\s+.*)?", start.strip())
        launch: dict[str, Any] = {
            "name": "FilterX: Express backend",
            "type": "node",
            "request": "launch",
            "cwd": cwd,
            "console": "integratedTerminal",
            "internalConsoleOptions": "neverOpen",
            "sourceMaps": True,
            "env": {"PORT": str(backend_port)},
            "outFiles": [f"{cwd}/dist/**/*.js"],
            "skipFiles": ["<node_internals>/**", f"{cwd}/node_modules/**"],
        }
        if program_match:
            launch["program"] = f"{cwd}/{program_match.group(1)}"
        else:
            launch.update(runtimeExecutable="npm", runtimeArgs=["run", "start"], autoAttachChildProcesses=True)
            if not start:
                warnings.append({"code": "DEBUG_EXPRESS_START_MISSING", "message": f"No start script found in {package_rel}; edit the generated Express launch configuration."})
        prisma = _relative(str(cfg.get("scan", {}).get("prisma", {}).get("schema", "prisma/schema.prisma")))
        prisma_task = "FilterX: generate Prisma client"
        if (project_root / prisma).exists():
            tasks.append(_task(prisma_task, "npm", ["exec", "prisma", "generate", "--", "--schema", _workspace_path(prisma)], cwd))
        if "build" in scripts:
            build = _task("FilterX: build Express backend", "npm", ["run", "build"], cwd)
            if (project_root / prisma).exists():
                build["dependsOn"] = prisma_task
                build["dependsOrder"] = "sequence"
            tasks.append(build)
            launch["preLaunchTask"] = build["label"]
        else:
            warnings.append({"code": "DEBUG_EXPRESS_BUILD_MISSING", "message": f"No build script found in {package_rel}."})
        configurations.extend([launch, {
            "name": "FilterX: Attach Node backend",
            "type": "node",
            "request": "attach",
            "address": "127.0.0.1",
            "port": 9229,
            "restart": True,
            "skipFiles": ["<node_internals>/**"],
        }])
    elif framework == "spring-boot-jpa":
        spring = backend.get("spring", {})
        root = _relative(str(spring.get("module_path", ".")))
        cwd = _workspace_path(root)
        main_class = str(spring.get("application_class") or "${input:filterxSpringMainClass}")
        configurations.extend([{
            "name": "FilterX: Spring Boot backend",
            "type": "java",
            "request": "launch",
            "mainClass": main_class,
            "cwd": cwd,
            "args": f"--server.port={backend_port}",
            "console": "integratedTerminal",
        }, {
            "name": "FilterX: Attach Java backend",
            "type": "java",
            "request": "attach",
            "hostName": "127.0.0.1",
            "port": 5005,
        }])
        extensions.append("vscjava.vscode-java-pack")
        if not spring.get("application_class"):
            warnings.append({"code": "DEBUG_SPRING_MAIN_CLASS_PROMPT", "message": "backend.spring.application_class is unset; VS Code will prompt for the fully qualified main class."})
    else:
        warnings.append({"code": "DEBUG_BACKEND_UNSUPPORTED", "message": f"No debugger renderer is registered for backend '{framework}'."})
    return configurations, tasks, extensions, warnings


def _frontend_debug(project_root: Path, cfg: Mapping[str, Any], port: int | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], list[dict[str, str]]]:
    frontend = cfg["frontend"]
    if not frontend.get("enabled", True):
        return [], [], [], []
    framework, root = _frontend_settings(cfg)
    port = port or _frontend_default_port(framework)
    cwd = _workspace_path(root)
    package_rel = f"{root}/package.json" if root else "package.json"
    package = _package(project_root, package_rel)
    scripts = package.get("scripts", {}) if isinstance(package.get("scripts"), dict) else {}
    preferred = "start" if framework == "angular" else "dev"
    script = preferred if preferred in scripts else "start" if "start" in scripts else preferred
    warnings: list[dict[str, str]] = []
    extensions: list[str] = []
    if script not in scripts:
        warnings.append({"code": "DEBUG_FRONTEND_SCRIPT_MISSING", "message": f"Expected npm script '{script}' in {package_rel}."})
    if framework == "nextjs":
        return [{
            "name": "FilterX: Next.js frontend",
            "type": "node",
            "request": "launch",
            "runtimeExecutable": "npm",
            "runtimeArgs": ["run", script, "--", "-p", str(port)],
            "cwd": cwd,
            "console": "integratedTerminal",
            "skipFiles": ["<node_internals>/**", f"{cwd}/node_modules/**"],
            "serverReadyAction": {
                "pattern": "- Local:\\s+(https?://\\S+)",
                "uriFormat": "%s",
                "action": "debugWithChrome",
            },
        }], [], extensions, warnings

    label = f"FilterX: start {framework} frontend"
    task = _task(label, "npm", ["run", script, "--", "--host", "127.0.0.1", "--port", str(port)], cwd, background=True)
    web_root = f"{cwd}/src"
    browser: dict[str, Any] = {
        "name": f"FilterX: {framework} frontend",
        "type": "pwa-chrome",
        "request": "launch",
        "url": _frontend_url(framework, port),
        "webRoot": web_root,
        "sourceMaps": True,
        "preLaunchTask": label,
    }
    if framework == "angular":
        browser["sourceMapPathOverrides"] = {"webpack:///./*": f"{web_root}/*", "webpack:///src/*": f"{web_root}/*"}
        extensions.append("angular.ng-template")
    elif framework == "vue":
        extensions.append("Vue.volar")
    return [browser], [task], extensions, warnings


def _documents(
    project_root: Path,
    cfg: Mapping[str, Any],
    backend_port: int,
    frontend_port: int | None,
    config_reference: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, str]]]:
    backend, backend_tasks, backend_extensions, warnings = _backend_debug(project_root, cfg, backend_port)
    frontend, frontend_tasks, frontend_extensions, frontend_warnings = _frontend_debug(project_root, cfg, frontend_port)
    cli = {
        "name": "FilterX: Debug CLI validate",
        "type": "debugpy",
        "request": "launch",
        "module": "filterx.cli",
        "args": ["validate", "--project-root", ".", "--config", config_reference, "--json"],
        "cwd": "${workspaceFolder}",
        "console": "integratedTerminal",
        "justMyCode": False,
    }
    configurations = [cli, *backend, *frontend]
    backend_names = [item["name"] for item in backend if not item["name"].startswith("FilterX: Attach")]
    frontend_names = [item["name"] for item in frontend]
    compounds = []
    if backend_names and frontend_names:
        compounds.append({"name": "FilterX: Full stack", "configurations": [backend_names[0], frontend_names[0]], "stopAll": True})
    inputs = []
    if any(item.get("mainClass") == "${input:filterxSpringMainClass}" for item in configurations):
        inputs.append({"id": "filterxSpringMainClass", "type": "promptString", "description": "Fully qualified Spring Boot main class"})
    launch: dict[str, Any] = {"version": "0.2.0", "configurations": configurations, "compounds": compounds}
    if inputs:
        launch["inputs"] = inputs
    tasks = {"version": "2.0.0", "tasks": [*backend_tasks, *frontend_tasks]}
    extensions = {"recommendations": sorted(set(["ms-python.python", "ms-python.debugpy", *backend_extensions, *frontend_extensions]))}
    return launch, tasks, extensions, [*warnings, *frontend_warnings]


def _load_state(project_root: Path) -> dict[str, Any] | None:
    path = project_root / STATE_PATH
    return _read_json(path) if path.exists() else None


def _select_mode(project_root: Path, requested: str, state: dict[str, Any] | None) -> str:
    if state:
        mode = str(state.get("mode"))
        if requested != "auto" and requested != mode:
            raise ValueError(f"Debug configuration is already installed in '{mode}' mode; remove it before changing mode")
        return mode
    if requested != "auto":
        return requested
    return "workspace" if any((project_root / path).exists() for path in (".vscode/launch.json", ".vscode/tasks.json")) else "vscode"


def _desired(
    project_root: Path,
    cfg: Mapping[str, Any],
    mode: str,
    backend_port: int,
    frontend_port: int | None,
    config_reference: str,
    owned_files: Mapping[str, str] | None = None,
) -> tuple[dict[str, bytes], list[dict[str, str]]]:
    launch, tasks, extensions, warnings = _documents(project_root, cfg, backend_port, frontend_port, config_reference)
    if mode == "workspace":
        document = {"folders": [{"path": "."}], "settings": {}, "extensions": extensions, "launch": launch, "tasks": tasks}
        return {WORKSPACE_PATH: _json_bytes(document)}, warnings
    if mode != "vscode":
        raise ValueError("--mode must be auto, vscode, or workspace")
    desired = {".vscode/launch.json": _json_bytes(launch), ".vscode/tasks.json": _json_bytes(tasks)}
    extension_path = project_root / ".vscode/extensions.json"
    if not extension_path.exists() or ".vscode/extensions.json" in (owned_files or {}):
        desired[".vscode/extensions.json"] = _json_bytes(extensions)
    else:
        warnings.append({"code": "DEBUG_EXTENSIONS_FILE_PRESERVED", "message": "Existing .vscode/extensions.json was preserved; install the recommendations listed by debug validate if needed."})
    return desired, warnings


def _conflicts(project_root: Path, desired: Mapping[str, bytes], state: dict[str, Any] | None) -> list[dict[str, str]]:
    owned = state.get("files", {}) if state else {}
    issues = []
    for relative, content in desired.items():
        path = project_root / relative
        expected = owned.get(relative)
        if path.exists() and expected is None:
            issues.append({"code": "DEBUG_FILE_USER_OWNED", "path": relative, "message": "The destination already exists and is not owned by FilterX."})
        elif path.exists() and _hash(path.read_bytes()) != expected:
            issues.append({"code": "DEBUG_FILE_MODIFIED", "path": relative, "message": "Generated debugger file was modified after installation."})
    for relative, expected in owned.items():
        path = project_root / relative
        if relative not in desired and path.exists() and _hash(path.read_bytes()) != expected:
            issues.append({"code": "DEBUG_FILE_MODIFIED", "path": relative, "message": "Obsolete debugger file was modified and cannot be removed safely."})
    return issues


def _payload(args: Any, payload: dict[str, Any]) -> None:
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2))
    else:
        print(f"FilterX debug {payload['action']}: {'ok' if payload['ok'] else 'blocked'}")
        for item in payload.get("files", []):
            print(f"- {item['action']}: {item['path']}")
        for issue in [*payload.get("issues", []), *payload.get("warnings", [])]:
            print(f"- {issue['code']}: {issue.get('message', issue.get('path', ''))}")


def run_install(args: Any) -> int:
    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config).resolve() if args.config else project_root / "filterx.yaml"
    cfg = load_effective_config(project_root, config_path).raw
    state = _load_state(project_root)
    try:
        mode = _select_mode(project_root, str(getattr(args, "mode", "auto")), state)
        backend_port = int(args.backend_port)
        frontend_port = args.frontend_port
        if not 1 <= backend_port <= 65535 or (frontend_port is not None and not 1 <= int(frontend_port) <= 65535):
            raise ValueError("Debugger ports must be between 1 and 65535")
        config_reference = _config_reference(project_root, config_path)
        desired, warnings = _desired(project_root, cfg, mode, backend_port, frontend_port, config_reference, state.get("files", {}) if state else None)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        _payload(args, {"action": "install", "ok": False, "issues": [{"code": "DEBUG_CONFIG_INVALID", "message": str(exc)}]})
        return 2
    issues = _conflicts(project_root, desired, state)
    dry_run = bool(getattr(args, "check", False)) or bool(cfg["safety"].get("dry_run_default", True) if args.dry_run is None else args.dry_run)
    files = [{"path": relative, "action": "unchanged" if (project_root / relative).exists() and (project_root / relative).read_bytes() == content else "update" if (project_root / relative).exists() else "create"} for relative, content in desired.items()]
    if not issues and not dry_run:
        old_files = state.get("files", {}) if state else {}
        for relative in set(old_files) - set(desired):
            path = project_root / relative
            if path.exists():
                path.unlink()
        for relative, content in desired.items():
            path = project_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_name(path.name + ".tmp")
            temporary.write_bytes(content)
            os.replace(temporary, path)
        next_state = {"version": 1, "mode": mode, "config": config_reference, "backend_port": args.backend_port, "frontend_port": args.frontend_port,
                      "files": {relative: _hash(content) for relative, content in desired.items()}}
        state_path = project_root / STATE_PATH
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_bytes(_json_bytes(next_state))
    code = 3 if issues or (getattr(args, "fail_on_warning", False) and warnings) else 0
    _payload(args, {"action": "install", "ok": code == 0, "dry_run": dry_run, "mode": mode, "files": files, "issues": issues, "warnings": warnings})
    return code


def run_validate(args: Any) -> int:
    project_root = Path(args.project_root).resolve()
    state = _load_state(project_root)
    if not state:
        _payload(args, {"action": "validate", "ok": False, "issues": [{"code": "DEBUG_NOT_INSTALLED", "message": "Run 'filterx debug install' first."}]})
        return 4
    stored_config = Path(str(state.get("config", "filterx.yaml")))
    config_path = Path(args.config).resolve() if args.config else (stored_config if stored_config.is_absolute() else project_root / stored_config)
    cfg = load_effective_config(project_root, config_path).raw
    try:
        desired, warnings = _desired(
            project_root,
            cfg,
            str(state["mode"]),
            int(state.get("backend_port", 8000)),
            state.get("frontend_port"),
            _config_reference(project_root, config_path),
            state.get("files", {}),
        )
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        _payload(args, {"action": "validate", "ok": False, "issues": [{"code": "DEBUG_CONFIG_INVALID", "message": str(exc)}]})
        return 4
    issues = _conflicts(project_root, desired, state)
    for relative, content in desired.items():
        path = project_root / relative
        if path.exists() and path.read_bytes() != content and not any(item.get("path") == relative for item in issues):
            issues.append({"code": "DEBUG_CONFIG_STALE", "path": relative, "message": "Debugger definitions do not match the current filterx.yaml."})
        if path.exists():
            try:
                _read_json(path)
            except (ValueError, json.JSONDecodeError) as exc:
                issues.append({"code": "DEBUG_JSON_INVALID", "path": relative, "message": str(exc)})
    code = 4 if issues or (getattr(args, "fail_on_warning", False) and warnings) else 0
    _payload(args, {"action": "validate", "ok": code == 0, "mode": state["mode"], "files": [{"path": path, "action": "validate"} for path in desired], "issues": issues, "warnings": warnings})
    return code


def run_remove(args: Any) -> int:
    project_root = Path(args.project_root).resolve()
    state = _load_state(project_root)
    if not state:
        _payload(args, {"action": "remove", "ok": False, "issues": [{"code": "DEBUG_NOT_INSTALLED", "message": "No FilterX debugger files are installed."}]})
        return 2
    issues = []
    for relative, expected in state.get("files", {}).items():
        path = project_root / relative
        if path.exists() and _hash(path.read_bytes()) != expected:
            issues.append({"code": "DEBUG_FILE_MODIFIED", "path": relative, "message": "Modified debugger file will not be removed."})
    dry_run = bool(getattr(args, "check", False)) or bool(state and (args.dry_run if args.dry_run is not None else True))
    if not issues and not dry_run:
        for relative in state.get("files", {}):
            (project_root / relative).unlink(missing_ok=True)
        (project_root / STATE_PATH).unlink(missing_ok=True)
    code = 3 if issues else 0
    _payload(args, {"action": "remove", "ok": code == 0, "dry_run": dry_run, "mode": state["mode"],
                    "files": [{"path": path, "action": "remove"} for path in state.get("files", {})], "issues": issues, "warnings": []})
    return code