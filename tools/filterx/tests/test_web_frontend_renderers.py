from __future__ import annotations

import json
from pathlib import Path

import pytest

from filterx.commands import frontend
from filterx.core.config import default_config
from golden_support import command_args
from test_spring_boot_jpa_install import _spring_ir


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _project(root: Path, framework: str) -> tuple[Path, str]:
    root.mkdir()
    config = default_config()
    config["frontend"]["framework"] = framework
    config["frontend"]["workspace_root"] = "frontend"
    config["backend"]["enabled"] = False
    config["database"]["enabled"] = False
    config["safety"]["dry_run_default"] = False
    config_path = root / "filterx.yaml"
    _write(config_path, json.dumps(config, indent=2) + "\n")
    _write(root / ".filterx/ir.json", json.dumps(_spring_ir().to_dict(), indent=2) + "\n")
    original_package = json.dumps(
        {
            "name": f"filterx-{framework}-fixture",
            "private": True,
            "scripts": {"build": "host-build-command"},
            "dependencies": {"host-package": "1.2.3"},
            "devDependencies": {"host-dev-package": "4.5.6"},
        },
        indent=2,
    ) + "\n"
    _write(root / "frontend/package.json", original_package)
    if framework == "react-vite":
        _write(
            root / "frontend/src/App.tsx",
            "export default function App(){ return <main>// FILTERX:APP</main>; }\n",
        )
    elif framework == "vue":
        _write(
            root / "frontend/src/App.vue",
            '<script setup lang="ts">\nconst host = true;\n</script>\n<template><!-- FILTERX:APP --></template>\n',
        )
    return config_path, original_package


@pytest.mark.parametrize(
    ("framework", "component", "dependencies", "host_fragment"),
    [
        ("react-vite", "FilterxApp.tsx", {"react", "react-dom"}, "<FilterxApp />"),
        ("nextjs", "FilterxApp.tsx", {"next", "react", "react-dom"}, None),
        ("vue", "FilterxApp.vue", {"vue"}, "<FilterxApp />"),
    ],
)
def test_web_frontend_renderer_generates_full_ui_and_rolls_back(
    tmp_path: Path,
    framework: str,
    component: str,
    dependencies: set[str],
    host_fragment: str | None,
) -> None:
    project_root = tmp_path / framework
    config_path, original_package = _project(project_root, framework)
    args = command_args(project_root, config_path)

    preview = command_args(project_root, config_path, dry_run=True)
    assert frontend.run_install(preview) == 0
    assert not (project_root / "frontend/src/filterx-generated").exists()

    assert frontend.run_install(args) == 0
    generated = project_root / "frontend/src/filterx-generated"
    assert (generated / component).exists()
    assert (generated / "types.ts").exists()
    assert (generated / "entities.ts").exists()
    assert (generated / "api.ts").exists()
    assert (generated / "filterx.css").exists()

    types = (generated / "types.ts").read_text(encoding="utf-8")
    component_text = (generated / component).read_text(encoding="utf-8")
    if (generated / "FilterxFilterBuilder.vue").exists():
        component_text += (generated / "FilterxFilterBuilder.vue").read_text(encoding="utf-8")
    api = (generated / "api.ts").read_text(encoding="utf-8")
    assert "export interface Book" in types
    assert "authorId: number" in types
    for capability in ("Custom filters", "Search", "Group", "Previous"):
        assert capability in component_text
    assert ("CSV" in component_text and "Excel" in component_text and "JSON" in component_text) or "format.toUpperCase()" in component_text
    assert "/export?" in api
    assert "/group-by/${field}/filter" in api
    assert "filter_tree" in api

    package = json.loads((project_root / "frontend/package.json").read_text(encoding="utf-8"))
    assert package["scripts"] == {"build": "host-build-command"}
    assert package["dependencies"]["host-package"] == "1.2.3"
    assert dependencies <= set(package["dependencies"])
    assert package["devDependencies"]["host-dev-package"] == "4.5.6"

    if framework == "nextjs":
        assert (project_root / "frontend/src/app/filterx/page.tsx").exists()
    elif host_fragment:
        host = "App.vue" if framework == "vue" else "App.tsx"
        assert host_fragment in (project_root / "frontend/src" / host).read_text(encoding="utf-8")

    assert frontend.run_validate(args) == 0
    assert frontend.run_remove(args) == 0
    assert not (generated / component).exists()
    assert not (generated / "types.ts").exists()
    assert (project_root / "frontend/package.json").read_text(encoding="utf-8") == original_package


def test_unknown_frontend_renderer_lists_new_targets(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    project_root = tmp_path / "unknown"
    config_path, _ = _project(project_root, "unknown-ui")
    assert frontend.run_install(command_args(project_root, config_path)) == 2
    output = capsys.readouterr().out
    assert "react-vite" in output
    assert "nextjs" in output
    assert "vue" in output
