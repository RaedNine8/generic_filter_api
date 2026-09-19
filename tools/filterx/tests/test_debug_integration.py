"""Real filesystem coverage for generated VS Code debugger integrations."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from filterx.cli import main
from filterx.core.config import default_config


BACKENDS = ("fastapi-sqlalchemy", "express-prisma", "spring-boot-jpa")
FRONTENDS = ("angular", "react-vite", "nextjs", "vue")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def configure(root: Path, backend: str, frontend: str) -> None:
    cfg = default_config()
    cfg["project"]["root"] = "."
    cfg["project"]["backend_root"] = "."
    cfg["backend"]["framework"] = backend
    cfg["frontend"]["framework"] = frontend
    cfg["safety"]["dry_run_default"] = False
    if backend == "express-prisma":
        write(root / "package.json", json.dumps({
            "scripts": {"build": "tsc", "start": "node dist/server.js"},
            "dependencies": {"@prisma/client": "latest"},
            "devDependencies": {"prisma": "latest", "typescript": "latest"},
        }))
        write(root / "prisma/schema.prisma", "generator client { provider = \"prisma-client-js\" }\n")
    elif backend == "spring-boot-jpa":
        cfg["backend"]["spring"]["application_class"] = "com.example.Application"
        write(root / "pom.xml", "<project/>")
    scripts = {"start": "ng serve"} if frontend == "angular" else {"dev": "next dev" if frontend == "nextjs" else "vite"}
    write(root / "frontend/package.json", json.dumps({"scripts": scripts}))
    write(root / "filterx.yaml", json.dumps(cfg, indent=2))


def invoke(root: Path, action: str, *options: str) -> int:
    return main([
        "debug", action,
        "--project-root", str(root),
        "--config", str(root / "filterx.yaml"),
        "--json",
        *options,
    ])


@pytest.mark.parametrize("backend", BACKENDS)
@pytest.mark.parametrize("frontend", FRONTENDS)
def test_install_validate_and_remove_every_framework(tmp_path, capsys, backend, frontend):
    root = tmp_path / f"{backend}__{frontend}"
    configure(root, backend, frontend)

    assert invoke(root, "install", "--no-dry-run", "--backend-port", "8100", "--frontend-port", "4300") == 0
    report = json.loads(capsys.readouterr().out)
    assert report["mode"] == "vscode"
    assert report["ok"]

    launch_path = root / ".vscode/launch.json"
    tasks_path = root / ".vscode/tasks.json"
    extensions_path = root / ".vscode/extensions.json"
    state_path = root / ".filterx/debug.json"
    launch = json.loads(launch_path.read_text(encoding="utf-8"))
    tasks = json.loads(tasks_path.read_text(encoding="utf-8"))
    extensions = json.loads(extensions_path.read_text(encoding="utf-8"))
    names = {item["name"] for item in launch["configurations"]}

    assert "FilterX: Debug CLI validate" in names
    assert launch["compounds"] == [{
        "name": "FilterX: Full stack",
        "configurations": [
            {"fastapi-sqlalchemy": "FilterX: FastAPI backend", "express-prisma": "FilterX: Express backend", "spring-boot-jpa": "FilterX: Spring Boot backend"}[backend],
            {"angular": "FilterX: angular frontend", "react-vite": "FilterX: react-vite frontend", "nextjs": "FilterX: Next.js frontend", "vue": "FilterX: vue frontend"}[frontend],
        ],
        "stopAll": True,
    }]
    assert state_path.exists()
    assert isinstance(tasks["tasks"], list)
    assert "ms-python.debugpy" in extensions["recommendations"]

    backend_launch = next(item for item in launch["configurations"] if item["name"] == launch["compounds"][0]["configurations"][0])
    if backend == "fastapi-sqlalchemy":
        assert backend_launch["type"] == "debugpy"
        assert backend_launch["args"][-1] == "8100"
        assert backend_launch["cwd"] == "${workspaceFolder}"
    elif backend == "express-prisma":
        assert backend_launch["type"] == "node"
        assert backend_launch["env"]["PORT"] == "8100"
        labels = {item["label"] for item in tasks["tasks"]}
        assert "FilterX: generate Prisma client" in labels
        assert "FilterX: build Express backend" in labels
    else:
        assert backend_launch["type"] == "java"
        assert backend_launch["mainClass"] == "com.example.Application"
        assert backend_launch["args"] == "--server.port=8100"
        assert "vscjava.vscode-java-pack" in extensions["recommendations"]

    frontend_launch = next(item for item in launch["configurations"] if item["name"] == launch["compounds"][0]["configurations"][1])
    if frontend == "nextjs":
        assert frontend_launch["type"] == "node"
        assert frontend_launch["runtimeArgs"][-1] == "4300"
    else:
        assert frontend_launch["type"] == "pwa-chrome"
        assert frontend_launch["url"] == "http://127.0.0.1:4300"
        frontend_task = next(item for item in tasks["tasks"] if item["label"] == frontend_launch["preLaunchTask"])
        assert frontend_task["args"][-1] == "4300"

    first = {path: path.read_bytes() for path in (launch_path, tasks_path, extensions_path, state_path)}
    assert invoke(root, "install", "--no-dry-run", "--backend-port", "8100", "--frontend-port", "4300") == 0
    capsys.readouterr()
    assert {path: path.read_bytes() for path in first} == first
    assert invoke(root, "validate") == 0
    assert json.loads(capsys.readouterr().out)["ok"]
    assert invoke(root, "remove", "--no-dry-run") == 0
    capsys.readouterr()
    assert not launch_path.exists()
    assert not tasks_path.exists()
    assert not extensions_path.exists()
    assert not state_path.exists()


def test_auto_mode_preserves_existing_vscode_files(tmp_path, capsys):
    configure(tmp_path, "fastapi-sqlalchemy", "angular")
    write(tmp_path / ".vscode/settings.json", '{"editor.formatOnSave":true}\n')
    write(tmp_path / ".vscode/launch.json", '{\n  // user JSONC\n  "version": "0.2.0",\n  "configurations": [],\n}\n')
    settings = (tmp_path / ".vscode/settings.json").read_bytes()
    launch = (tmp_path / ".vscode/launch.json").read_bytes()

    assert invoke(tmp_path, "install", "--no-dry-run") == 0
    report = json.loads(capsys.readouterr().out)
    assert report["mode"] == "workspace"
    workspace = json.loads((tmp_path / "filterx-debug.code-workspace").read_text(encoding="utf-8"))
    assert workspace["launch"]["configurations"]
    assert workspace["tasks"]["tasks"]
    assert (tmp_path / ".vscode/settings.json").read_bytes() == settings
    assert (tmp_path / ".vscode/launch.json").read_bytes() == launch
    assert not (tmp_path / ".vscode/tasks.json").exists()


def test_post_install_edit_blocks_update_and_remove(tmp_path, capsys):
    configure(tmp_path, "express-prisma", "vue")
    assert invoke(tmp_path, "install", "--no-dry-run") == 0
    capsys.readouterr()
    launch = tmp_path / ".vscode/launch.json"
    launch.write_bytes(launch.read_bytes() + b"\n// my debugger edit\n")
    before = launch.read_bytes()

    assert invoke(tmp_path, "install", "--no-dry-run") == 3
    install_report = json.loads(capsys.readouterr().out)
    assert "DEBUG_FILE_MODIFIED" in {item["code"] for item in install_report["issues"]}
    assert launch.read_bytes() == before
    assert invoke(tmp_path, "validate") == 4
    capsys.readouterr()
    assert invoke(tmp_path, "remove", "--no-dry-run") == 3
    remove_report = json.loads(capsys.readouterr().out)
    assert "DEBUG_FILE_MODIFIED" in {item["code"] for item in remove_report["issues"]}
    assert launch.read_bytes() == before
    assert (tmp_path / ".filterx/debug.json").exists()


def test_explicit_vscode_mode_refuses_unowned_destination(tmp_path, capsys):
    configure(tmp_path, "fastapi-sqlalchemy", "react-vite")
    write(tmp_path / ".vscode/tasks.json", '{"version":"2.0.0","tasks":[{"label":"host"}]}')
    before = (tmp_path / ".vscode/tasks.json").read_bytes()

    assert invoke(tmp_path, "install", "--mode", "vscode", "--no-dry-run") == 3
    report = json.loads(capsys.readouterr().out)
    assert "DEBUG_FILE_USER_OWNED" in {item["code"] for item in report["issues"]}
    assert (tmp_path / ".vscode/tasks.json").read_bytes() == before
    assert not (tmp_path / ".filterx/debug.json").exists()


def test_invalid_ports_are_rejected_without_writes(tmp_path, capsys):
    configure(tmp_path, "fastapi-sqlalchemy", "angular")
    assert invoke(tmp_path, "install", "--backend-port", "70000", "--no-dry-run") == 2
    report = json.loads(capsys.readouterr().out)
    assert report["issues"][0]["code"] == "DEBUG_CONFIG_INVALID"
    assert not (tmp_path / ".vscode/launch.json").exists()


def test_fastapi_cwd_supports_backend_container_and_custom_config(tmp_path, capsys):
    configure(tmp_path, "fastapi-sqlalchemy", "angular")
    config_path = tmp_path / "config/filterx-custom.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_bytes((tmp_path / "filterx.yaml").read_bytes())
    (tmp_path / "filterx.yaml").unlink()
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    cfg["project"]["backend_root"] = "backend"
    write(config_path, json.dumps(cfg))
    write(tmp_path / "backend/app/main.py", "app = object()\n")

    assert main(["debug", "install", "--project-root", str(tmp_path), "--config", str(config_path), "--no-dry-run", "--json"]) == 0
    capsys.readouterr()
    launch = json.loads((tmp_path / ".vscode/launch.json").read_text(encoding="utf-8"))
    fastapi = next(item for item in launch["configurations"] if item["name"] == "FilterX: FastAPI backend")
    cli = next(item for item in launch["configurations"] if item["name"] == "FilterX: Debug CLI validate")
    assert fastapi["cwd"] == "${workspaceFolder}/backend"
    assert cli["args"][4] == "config/filterx-custom.yaml"
    assert main(["debug", "validate", "--project-root", str(tmp_path), "--json"]) == 0
