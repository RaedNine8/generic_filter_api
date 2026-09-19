from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest


REPO = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parents[1] / "filterx"
DEFAULT_ROOT = "frontend/src/app/filterx-generated"
DEFAULT_CUSTOM = "frontend/src/app/filterx-custom"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _entity(name: str = "Book", fields: tuple[str, ...] = ("id", "title")) -> dict:
    return {
        "model": name, "table": name.lower() + "s", "primary_keys": ["id"],
        "fields": [{"name": name, "type": "integer" if name == "id" else "string"} for name in fields],
        "relationships": [],
    }


def _scan(root: Path, entities: list[dict]) -> None:
    _write(root / ".filterx/scan.json", json.dumps({"entities": entities}))


def _project(root: Path, **frontend_settings: str) -> SimpleNamespace:
    config = {
        "version": 1,
        "backend": {"enabled": False},
        "frontend": {
            "framework": "angular", "workspace_root": "frontend",
            "generated_root": DEFAULT_ROOT, "routes_file": "frontend/src/app/app.routes.ts",
            "routes_anchor": "// FILTERX:ROUTES", **frontend_settings,
        },
        "safety": {"dry_run_default": False, "strict_conflict_mode": True},
    }
    _write(root / "filterx.yaml", json.dumps(config))
    _write(root / "frontend/package.json", json.dumps({"dependencies": {"@angular/core": "^18.0.0"}}))
    _write(root / config["frontend"]["routes_file"],
           "import { Routes } from '@angular/router';\n"
           "export const routes: Routes = [\n"
           "  { path: 'home', redirectTo: '', pathMatch: 'full' },\n"
           "  // FILTERX:ROUTES\n];\n// Host-owned footer.\n")
    _scan(root, [_entity()])
    return SimpleNamespace(
        project_root=str(root), config=str(root / "filterx.yaml"),
        dry_run=False, check=False, json=True, force=False, fail_on_warning=False,
        frontend_command="install", no_route_patch=False,
    )


def _install(args: SimpleNamespace) -> None:
    # Import the real lifecycle/PatchOp contract. No temporary modules or mocks.
    from filterx.commands import frontend

    assert frontend._run_angular_install(args) == 0


def _runtime_snapshot(root: Path) -> dict[str, bytes]:
    from filterx.commands import frontend

    return {op.path: (root / op.path).read_bytes() for op in frontend._copy_reference_runtime_ops("frontend")}


def test_create_once_shell_theme_and_presentation_survive_schema_evolution(tmp_path: Path) -> None:
    args = _project(tmp_path)
    _install(args)
    custom = tmp_path / DEFAULT_CUSTOM
    shell = custom / "filterx-shell.component.ts"
    theme = custom / "theme.css"
    presentation = custom / "presentation.json"
    assert shell.exists() and theme.exists() and presentation.exists()
    assert "/entities/" not in shell.read_text(encoding="utf-8")
    assert "/pages/" not in shell.read_text(encoding="utf-8")
    shell.write_bytes(shell.read_bytes() + b"\r\n// Host custom header and layout.\r\n")
    theme.write_bytes(b":host { --color-primary: purple; }\r\n")
    # Preserve the seeded JSON contract while adding a harmless host annotation.
    presentation.write_bytes(presentation.read_bytes() + b"\r\n ")
    original_custom = {path.name: path.read_bytes() for path in custom.iterdir()}
    original_runtime = _runtime_snapshot(tmp_path)
    config = tmp_path / DEFAULT_ROOT / "entities/book.config.ts"
    original_config = config.read_bytes()

    _scan(tmp_path, [_entity(fields=("id", "isbn")), _entity("Author", ("id", "name"))])
    _install(args)
    assert original_custom == {path.name: path.read_bytes() for path in custom.iterdir()}
    assert original_runtime == _runtime_snapshot(tmp_path)
    assert config.read_bytes() != original_config
    assert "'isbn'" in config.read_text(encoding="utf-8")
    assert "'title'" not in config.read_text(encoding="utf-8")
    assert (tmp_path / DEFAULT_ROOT / "pages/author.page.ts").exists()

    _scan(tmp_path, [_entity("Author", ("id", "name"))])
    _install(args)
    assert not config.exists()
    assert not (tmp_path / DEFAULT_ROOT / "pages/book.page.ts").exists()
    assert original_custom == {path.name: path.read_bytes() for path in custom.iterdir()}
    assert original_runtime == _runtime_snapshot(tmp_path)
    assert "Book" not in (tmp_path / DEFAULT_ROOT / "entities/index.ts").read_text(encoding="utf-8")


def test_all_models_removed_clears_routes_but_preserves_customization(tmp_path: Path) -> None:
    args = _project(tmp_path)
    route = tmp_path / "frontend/src/app/app.routes.ts"
    before = route.read_bytes()
    _install(args)
    assert b"FILTERX GENERATED ROUTES START" in route.read_bytes()
    custom = tmp_path / DEFAULT_CUSTOM / "filterx-shell.component.ts"
    shell_before = custom.read_bytes()
    _scan(tmp_path, [])
    _install(args)
    assert route.read_bytes() == before
    assert custom.read_bytes() == shell_before
    assert not (tmp_path / DEFAULT_ROOT / "pages/book.page.ts").exists()
    assert "Book" not in (tmp_path / DEFAULT_ROOT / "routes.ts").read_text(encoding="utf-8")
    assert (tmp_path / DEFAULT_ROOT / "entities/index.ts").read_text(encoding="utf-8") == "export {};\n"
    # Empty reinstall must not introduce a new generated route block or an anchor conflict.
    _install(args)
    assert route.read_bytes() == before


def test_no_route_patch_leaves_host_routes_untouched_on_empty_schema(tmp_path: Path) -> None:
    args = _project(tmp_path)
    args.no_route_patch = True
    route = tmp_path / "frontend/src/app/app.routes.ts"
    before = route.read_bytes()
    _install(args)
    assert route.read_bytes() == before
    args.no_route_patch = False
    _install(args)
    installed = route.read_bytes()
    assert installed != before
    args.no_route_patch = True
    _scan(tmp_path, [])
    _install(args)
    assert route.read_bytes() == installed


def test_configured_paths_have_resolvable_relative_imports(tmp_path: Path) -> None:
    generated = "frontend/src/generated/deep/filterx"
    custom = "frontend/src/custom/ui"
    routes = "frontend/src/app/navigation/routes.ts"
    args = _project(tmp_path, generated_root=generated, customization_root=custom, routes_file=routes)
    _install(args)
    shell = tmp_path / custom / "filterx-shell.component.ts"
    sources = [* (tmp_path / generated).rglob("*.ts"), shell, tmp_path / routes]
    for source in sources:
        for relative in re.findall(r"(?:from\s+|import\()['\"](\.[^'\"]+)['\"]", source.read_text(encoding="utf-8")):
            target = source.parent / relative
            assert Path(str(target) + ".ts").exists() or (target / "index.ts").exists(), (source, relative)
    page = (tmp_path / generated / "pages/book.page.ts").read_text(encoding="utf-8")
    assert "FilterxShellComponent" in page and "<filterx-shell" in page
    assert "EntityListComponent" not in page
    assert not (tmp_path / DEFAULT_CUSTOM).exists()


def test_runtime_and_custom_operations_are_schema_independent() -> None:
    from filterx.commands import frontend

    runtime = frontend._copy_reference_runtime_ops("frontend")
    assert runtime and all(op.metadata.get("layer") == "runtime" for op in runtime)
    custom = frontend._angular_customization_ops("frontend", DEFAULT_ROOT, DEFAULT_CUSTOM)
    assert custom and all(op.write_policy == "create_once" and op.metadata.get("layer") == "custom" for op in custom)
    shell = next(op.content for op in custom if op.path.endswith(".ts"))
    assert "FILTERX_PRESENTATION" in shell
    assert '[copilotEnabled]="copilotEnabled"' in shell
    assert '[cellTemplate]="cellTemplate || projectedCellTemplate"' in shell
    disabled = next(op.content for op in runtime if op.path.endswith("entity-list.component.ts"))
    assert "@Input() copilotEnabled = false;" in disabled
    assert "app-copilot-panel" not in disabled


def test_route_block_removal_preserves_crlf_and_host_text(tmp_path: Path) -> None:
    from filterx.commands import frontend

    routes = tmp_path / "routes.ts"
    before = "import { Routes } from '@angular/router';\r\nexport const routes: Routes = [\r\n// FILTERX:ROUTES\r\n];\r\n// host\r\n"
    routes.write_bytes(before.encode())
    snippet = "// FILTERX GENERATED ROUTES START\n{ path: 'books' },\n// FILTERX GENERATED ROUTES END"
    installed = frontend._build_routes_file_with_generated_block(routes, snippet, "// FILTERX:ROUTES")
    assert installed is not None
    routes.write_bytes(installed.encode())
    assert frontend._build_routes_file_with_generated_block(routes, "", "// FILTERX:ROUTES") == before


def _node_tools() -> tuple[str, Path]:
    node = shutil.which("node")
    modules = REPO / "frontend/node_modules"
    if not node or not (modules / "typescript/bin/tsc").exists():
        pytest.skip("Node and the frontend fixture's TypeScript installation are needed")
    return node, modules


def test_presentation_mapping_is_display_only_and_drops_unknown_columns(tmp_path: Path) -> None:
    node, modules = _node_tools()
    source = PACKAGE / "reference_runtime/app/core/config/filterx-presentation.ts"
    output = tmp_path / "compiled"
    result = subprocess.run(
        [node, str(modules / "typescript/bin/tsc"), str(source), "--outDir", str(output),
         "--module", "commonjs", "--target", "ES2020", "--strict", "--skipLibCheck"],
        capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    helper = next(output.rglob("filterx-presentation.js"))
    script = r"""
const assert = require('node:assert/strict');
const { applyFilterxPresentation } = require(process.argv[1]);
const config = { name: 'Book', pluralLabel: 'Books', singularLabel: 'Book', apiEndpoint: '/api/filterx/books',
  defaults: { sortField: 'id' }, fields: [{ name: 'id', label: 'ID', type: 'number' }, { name: 'title', label: 'Title', type: 'text' }],
  columns: [{ field: 'id', header: 'ID' }, { field: 'title', header: 'Title' }], groupByOptions: [{ field: 'title', label: 'Title' }] };
const before = JSON.stringify(config);
const overrides = { Book: { label: 'Library', columns: ['missing', 'title', 'title'], labels: { title: 'Caption', missing: 'Hidden' }, apiEndpoint: '/evil', name: 'Other' } };
const view = applyFilterxPresentation(config, overrides);
assert.equal(view.pluralLabel, 'Library');
assert.deepEqual(view.columns, [{ field: 'title', header: 'Caption' }]);
assert.equal(view.fields[1].name, 'title');
assert.equal(view.fields[1].label, 'Caption');
assert.equal(view.groupByOptions[0].label, 'Caption');
assert.equal(view.apiEndpoint, config.apiEndpoint);
assert.equal(view.name, config.name);
assert.equal(view.defaults, config.defaults);
assert.equal(JSON.stringify(config), before);
assert.equal(applyFilterxPresentation(config, {}), config);
assert.deepEqual(applyFilterxPresentation(config, { Book: { columns: [] } }).columns, []);
const evolved = { ...config, columns: [{ field: 'id', header: 'ID' }] };
assert.deepEqual(applyFilterxPresentation(evolved, overrides).columns, []);
"""
    result = subprocess.run([node, "-e", script, str(helper)], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("copilot", [False, True])
def test_generated_angular_templates_compile_with_custom_paths(tmp_path: Path, copilot: bool) -> None:
    node, modules = _node_tools()
    compiler = modules / "@angular/compiler-cli/bundles/src/bin/ngc.js"
    if not compiler.exists():
        pytest.skip("The frontend fixture's Angular compiler is needed")
    args = _project(tmp_path, generated_root="frontend/src/generated/filterx", customization_root="frontend/src/ui/filterx")
    config = json.loads((tmp_path / "filterx.yaml").read_text(encoding="utf-8"))
    config["agent"] = {"enabled": copilot}
    config["backend"]["enabled"] = copilot
    _write(tmp_path / "filterx.yaml", json.dumps(config))
    _install(args)
    tsconfig = tmp_path / "tsconfig.json"
    _write(tsconfig, json.dumps({
        "compilerOptions": {"target": "ES2022", "module": "ES2022", "moduleResolution": "node",
                            "experimentalDecorators": True, "strict": True, "skipLibCheck": True,
                            "lib": ["ES2022", "DOM"], "baseUrl": str(tmp_path),
                            "paths": {"*": [modules.as_posix() + "/*"]}, "outDir": str(tmp_path / "compiled")},
        "angularCompilerOptions": {"strictTemplates": True},
        "files": [str(tmp_path / "frontend/src/app/app.routes.ts")],
    }))
    result = subprocess.run([node, str(compiler), "-p", str(tsconfig)], capture_output=True, text=True, timeout=180)
    assert result.returncode == 0, result.stdout + result.stderr