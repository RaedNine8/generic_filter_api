"""Real CLI/filesystem updates; no mocked lifecycle or renderer implementations."""
import json
from pathlib import Path

import pytest

from filterx.cli import main
from filterx.core.config import default_config


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def scan(root, fields=("id", "title"), entities=True, relationship="author"):
    payload = {"entities": [{"model": "Book", "table": "books", "primary_keys": ["id"],
        "fields": [{"name": name, "type": "integer" if name == "id" else "string", "ops": ["eq"]} for name in fields],
        "relationships": [{"name": relationship, "related_model": "Book", "related_table": "books", "uselist": False, "cardinality": "m2o"}]
    }] if entities else []}
    write(root / ".filterx/scan.json", json.dumps(payload))


@pytest.fixture(params=["angular", "react-vite", "nextjs", "vue"])
def project(tmp_path, request):
    framework = request.param
    cfg = default_config()
    cfg["frontend"]["framework"] = framework
    cfg["safety"]["dry_run_default"] = False
    write(tmp_path / "filterx.yaml", json.dumps(cfg))
    write(tmp_path / "frontend/package.json", '{"dependencies":{"@angular/core":"^18.0.0"}}')
    if framework == "angular":
        write(tmp_path / "frontend/src/app/app.routes.ts", "import { Routes } from '@angular/router';\nexport const routes: Routes = [\n// FILTERX:ROUTES\n];\n")
    elif framework == "react-vite":
        write(tmp_path / "frontend/src/App.tsx", "export default function App(){return <main>\n// FILTERX:APP\n</main>}\n")
    elif framework == "vue":
        write(tmp_path / "frontend/src/App.vue", "<template><!-- FILTERX:APP --></template>\n")
    scan(tmp_path)
    return tmp_path, framework


def invoke(root, command="install", *options):
    return main(["frontend", command, "--project-root", str(root), "--config", str(root / "filterx.yaml"), "--json", *options])


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def generated(root, framework):
    return root / ("frontend/src/app/filterx-generated" if framework == "angular" else "frontend/src/filterx-generated")


def test_diagnostics_and_reinstall_are_read_only_when_requested(project, capsys):
    root, framework = project
    before = snapshot(root)
    assert invoke(root, "diff", "--no-dry-run") == 0
    report = json.loads(capsys.readouterr().out)
    assert any(change["diff"] for change in report["changes"] if change["action"] == "create")
    assert snapshot(root) == before
    assert invoke(root) == 0
    capsys.readouterr()
    before = snapshot(root)
    assert invoke(root, "doctor", "--no-dry-run") == 0
    assert json.loads(capsys.readouterr().out)["ok"]
    assert snapshot(root) == before
    assert invoke(root) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["applied_ops"] == 0


def test_modified_core_blocks_entire_write_even_with_force(project, capsys):
    root, framework = project
    assert invoke(root) == 0
    capsys.readouterr()
    core = (root / "frontend/src/app/core/services/generic-query.service.ts" if framework == "angular" else generated(root, framework) / "api.ts")
    core.write_bytes(core.read_bytes() + b"\n// local query edit\n")
    scan(root, fields=("id", "isbn"))
    before = snapshot(root)
    for command, options in [("diff", ()), ("doctor", ()), ("install", ("--force",))]:
        assert invoke(root, command, *options) == 3
        report = json.loads(capsys.readouterr().out)
        assert "CONFLICT_FRONTEND_MODIFIED" in {issue["code"] for issue in report["issues"]}
        assert snapshot(root) == before


def test_schema_and_relationship_changes_preserve_presentation(project, capsys):
    root, framework = project
    assert invoke(root) == 0
    capsys.readouterr()
    custom = root / ("frontend/src/app/filterx-custom" if framework == "angular" else "frontend/src/filterx-custom")
    write(custom / "presentation.json", '{"Book":{"label":"Library","columns":["title"],"labels":{"title":"Caption"}}}')
    shell = next(custom.glob("*Shell*"), None) or custom / "filterx-shell.component.ts"
    shell.write_bytes(shell.read_bytes() + b"\n// my layout\n")
    custom_before = snapshot(custom)
    runtime = (root / "frontend/src/app/core/services/generic-query.service.ts" if framework == "angular" else generated(root, framework) / "api.ts")
    runtime_before = (runtime.read_bytes(), runtime.stat().st_mtime_ns)
    scan(root, fields=("id", "isbn"), relationship="publisher")
    before = snapshot(root)
    assert invoke(root, "diff") == 0
    report = json.loads(capsys.readouterr().out)
    assert any(c.get("member") == "title" and c["breaking"] for c in report["schema_changes"])
    assert any(c.get("category") == "relationships" for c in report["schema_changes"])
    assert any(w["code"] == "PRESENTATION_FIELD_REMOVED" for w in report["warnings"])
    assert snapshot(root) == before
    assert invoke(root) == 0
    capsys.readouterr()
    assert snapshot(custom) == custom_before
    assert (runtime.read_bytes(), runtime.stat().st_mtime_ns) == runtime_before
    assert "Caption" not in (generated(root, framework) / "presentation.ts").read_text()
    assert "Library" in (generated(root, framework) / "presentation.ts").read_text()


def test_presentation_cannot_override_query_contract(project, capsys):
    root, framework = project
    assert invoke(root) == 0
    capsys.readouterr()
    custom = root / ("frontend/src/app/filterx-custom" if framework == "angular" else "frontend/src/filterx-custom")
    write(custom / "presentation.json", '{"Book":{"apiEndpoint":"/bypass","columns":["id"]}}')
    before = snapshot(root)
    assert invoke(root) == 2
    assert snapshot(root) == before


def test_edited_obsolete_file_blocks_pruning(project, capsys):
    root, framework = project
    assert invoke(root) == 0
    capsys.readouterr()
    if framework != "angular":
        # All web entities share one schema file; an edit to it must also block
        # replacement when the final model is removed.
        path = generated(root, framework) / "entities.ts"
    else:
        path = generated(root, framework) / "pages/book.page.ts"
    path.write_bytes(path.read_bytes() + b"\n// user edit\n")
    scan(root, entities=False)
    before = snapshot(root)
    assert invoke(root) == 3
    assert snapshot(root) == before


def test_angular_route_block_protects_guards_not_unrelated_host_edits(tmp_path, capsys):
    # Use a real Angular project, not a fake patch plan.
    cfg = default_config()
    cfg["safety"]["dry_run_default"] = False
    write(tmp_path / "filterx.yaml", json.dumps(cfg))
    route = tmp_path / "frontend/src/app/app.routes.ts"
    write(route, "import { Routes } from '@angular/router';\nexport const routes: Routes = [\n// FILTERX:ROUTES\n];\n")
    write(tmp_path / "frontend/package.json", '{"dependencies":{"@angular/core":"^18.0.0"}}')
    scan(tmp_path)
    assert invoke(tmp_path) == 0
    capsys.readouterr()
    route.write_bytes(route.read_bytes() + b"\n// unrelated host customization\n")
    scan(tmp_path, fields=("id", "isbn"))
    assert invoke(tmp_path) == 0
    capsys.readouterr()
    write(route, route.read_text().replace("path: 'books',", "path: 'books', canActivate: [myGuard],"))
    scan(tmp_path, entities=False)
    before = snapshot(tmp_path)
    assert invoke(tmp_path) == 3
    assert snapshot(tmp_path) == before


def test_existing_host_versions_and_theme_are_preserved(project, capsys):
    root, framework = project
    assert invoke(root) == 0
    capsys.readouterr()
    if framework == "angular":
        config = root / "frontend/src/app/app.config.ts"
        source = ("import {ApplicationConfig} from '@angular/core';\n"
                  "import {providePrimeNG} from 'primeng/config';\n"
                  "import {provideFilterx} from './core/config/filterx-config';\n"
                  "import {provideAnimationsAsync} from '@angular/platform-browser/animations/async';\n"
                  "import MyTheme from './my-theme';\n"
                  "export const appConfig: ApplicationConfig = { providers: [\n"
                  "provideFilterx(), provideAnimationsAsync(), providePrimeNG({theme:{preset:MyTheme}}),\n"
                  "// FILTERX:PROVIDERS\n]};\n")
        write(config, source)
        assert invoke(root) == 0
        assert config.read_text() == source
    else:
        package = root / "frontend/package.json"
        data = json.loads(package.read_text())
        name = "vue" if framework == "vue" else "react"
        data["dependencies"][name] = "99.0.0-host-selection"
        write(package, json.dumps(data, indent=2) + "\n")
        assert invoke(root) == 0
        assert json.loads(package.read_text())["dependencies"][name] == "99.0.0-host-selection"


def test_rollback_refuses_custom_edits_then_restores_baseline(project, capsys):
    root, framework = project
    assert invoke(root) == 0
    first = json.loads(capsys.readouterr().out)["patch_id"]
    scan(root, fields=("id", "isbn"))
    assert invoke(root) == 0
    second = json.loads(capsys.readouterr().out)["patch_id"]
    command = ["rollback", "--project-root", str(root), "--config", str(root / "filterx.yaml"), "--json", "--patch-id"]
    assert main(command + [second]) == 0
    capsys.readouterr()
    scan(root)
    # The installed hashes must correspond to the restored first generation.
    assert invoke(root, "doctor") == 0
    capsys.readouterr()
    custom = root / ("frontend/src/app/filterx-custom" if framework == "angular" else "frontend/src/filterx-custom")
    theme = custom / "theme.css"
    original = theme.read_bytes()
    theme.write_bytes(original + b"\n/* Later user edit */\n")
    before = snapshot(root)
    assert main(command + [first]) == 3
    capsys.readouterr()
    assert snapshot(root) == before
    theme.write_bytes(original)
    assert main(command + [first]) == 0
    assert not generated(root, framework).joinpath("presentation.ts").exists()