from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from filterx.core.config import default_config
from filterx.core.ir import EntityIR, EntityIdentityIR, FieldIR, FieldType, FilterxIR, IR_VERSION
from filterx.renderers import web_frontends


REPO = Path(__file__).resolve().parents[3]
TEMPLATES = Path(__file__).resolve().parents[1] / "filterx/reference_runtime/web_frontends"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def web():
    return web_frontends


@pytest.fixture
def ir() -> FilterxIR:
    def entity(name: str, table: str, names: tuple[str, ...]) -> EntityIR:
        return EntityIR(
            name=name, identity=EntityIdentityIR(module="models", table=table, primary_keys=("id",)),
            relationships=(),
            fields=tuple(FieldIR(name=key, type=FieldType.INTEGER if key == "id" else FieldType.STRING,
                                 source_type="test", nullable=False, primary_key=key == "id", unique=False,
                                 has_default=False, operations=("eq", "ne")) for key in names),
        )
    return FilterxIR(version=IR_VERSION, source_framework="sqlalchemy", entities=(
        entity("Author", "authors", ("id", "name", "secret")),
        entity("Book", "books", ("id", "title")),
    ), max_relationship_depth=1)


def _setup(tmp_path: Path, web, target, **settings):
    cfg = default_config()
    cfg["frontend"]["framework"] = target.name
    cfg["frontend"][target.config_key].update(settings)
    workspace = cfg["frontend"][target.config_key].get("workspace_root", "frontend")
    _write(tmp_path / workspace / "package.json", '{"private":true}\n')
    if target is not web.NEXTJS:
        host = web._target_config(cfg, target)["host_file"]
        _write(tmp_path / workspace / host, '<template><!-- FILTERX:APP --></template>' if target is web.VUE
               else 'export default function Host(){return <main>// FILTERX:APP</main>}')
    return cfg


@pytest.mark.parametrize("framework", ["REACT_VITE", "NEXTJS", "VUE"])
def test_runtime_and_contracts_are_schema_independent(tmp_path, web, ir, framework):
    target = getattr(web, framework)
    cfg = _setup(tmp_path, web, target)
    before, _ = web._operations(tmp_path, cfg, ir, target)
    changed = replace(ir, entities=(replace(ir.entities[1], fields=ir.entities[1].fields[:1]),))
    after, _ = web._operations(tmp_path, cfg, changed, target)
    runtime = {op.path: op.content for op in before if op.metadata.get("layer") == "runtime"}
    assert runtime == {op.path: op.content for op in after if op.metadata.get("layer") == "runtime"}
    assert any(path.endswith("contracts.ts") for path in runtime)
    for path, content in runtime.items():
        assert "from './types'" not in content or path.endswith("index.ts")
        assert "interface Book" not in content
    schemas = {Path(op.path).name: op for op in before if op.metadata.get("layer") == "schema"}
    assert {"types.ts", "entities.ts", "presentation.ts"} <= set(schemas)
    assert "export * from './contracts'" in schemas["types.ts"].content
    assert "export interface Book" in schemas["types.ts"].content
    custom = [op for op in before if op.metadata.get("layer") == "custom"]
    assert all(op.write_policy == "create_once" for op in custom)
    assert {Path(op.path).name for op in custom} == ({"FilterxShell.vue", "theme.css", "presentation.json"} if target is web.VUE else {"FilterxShell.tsx", "theme.css", "presentation.json"} | ({"page.tsx"} if target is web.NEXTJS else set()))
    shell = next(op for op in custom if "FilterxShell" in op.path)
    assert "import './theme.css'" in shell.content
    assert "FilterxApp" in shell.content
    assert "FILTERX_PRESENTATION" in schemas["presentation.ts"].content


@pytest.mark.parametrize("framework,host", [("REACT_VITE", "src/screens/admin/App.tsx"), ("VUE", "src/screens/admin/App.vue"), ("NEXTJS", "app/tools/filter/page.tsx")])
def test_custom_paths_use_relative_shell_and_runtime_imports(tmp_path, web, ir, framework, host):
    target = getattr(web, framework)
    cfg = _setup(tmp_path, web, target, workspace_root="apps/web", generated_root="generated/runtime", host_file=host)
    if target is not web.NEXTJS:
        text = '<template><!-- FILTERX:APP --></template>' if target is web.VUE else "export default function Host(){return <main>// FILTERX:APP</main>}"
        _write(tmp_path / "apps/web" / host, text)
    ops, _ = web._operations(tmp_path, cfg, ir, target)
    shell = next(op for op in ops if "FilterxShell." in op.path)
    assert "../../generated/runtime/FilterxApp" in shell.content
    mounted = next(op for op in ops if op.path == f"apps/web/{host}")
    assert "../../filterx-custom/FilterxShell" in mounted.content if target is not web.NEXTJS else "../../../src/filterx-custom/FilterxShell" in mounted.content
    assert "filterx-generated/FilterxApp" not in mounted.content
    assert mounted.owner == "host" if target is not web.NEXTJS else mounted.write_policy == "create_once"


@pytest.mark.parametrize("framework", ["REACT_VITE", "VUE", "NEXTJS"])
def test_exact_legacy_import_migration_preserves_host_edits_and_line_endings(tmp_path, web, framework):
    target = getattr(web, framework)
    host = "src/App.vue" if target is web.VUE else "src/app/filterx/page.tsx" if target is web.NEXTJS else "src/App.tsx"
    old_import = ("import FilterxApp from './filterx-generated/FilterxApp.vue';" if target is web.VUE else
                  "import { FilterxApp } from '../../filterx-generated/FilterxApp';" if target is web.NEXTJS else
                  "import { FilterxApp } from './filterx-generated/FilterxApp';")
    before = "// user-owned banner\r\n" + old_import + "\r\n// keep this exactly\r\n"
    before += '<template><aside>Custom</aside><FilterxApp /></template>\r\n' if target is web.VUE else "export default function Custom(){return <><aside>Custom</aside><FilterxApp /></>}\r\n"
    path = tmp_path / "frontend" / host
    path.parent.mkdir(parents=True)
    path.write_bytes(before.encode())
    op = web._patch_host(tmp_path, "frontend", host, "unused-anchor", target)
    assert op is not None and op.owner == "host"
    new_import = next(line for line in op.content.splitlines() if line.startswith("import "))
    assert "FilterxShell" in new_import
    assert op.content == before.replace(old_import, new_import)
    path.write_bytes(op.content.encode())
    assert web._patch_host(tmp_path, "frontend", host, "unused-anchor", target) is None
    path.write_bytes(before.replace(old_import, old_import.replace("'", '"')).encode())
    assert web._patch_host(tmp_path, "frontend", host, "unused-anchor", target) is None


def test_edited_next_page_is_create_once_not_replaced(tmp_path, web, ir):
    cfg = _setup(tmp_path, web, web.NEXTJS)
    page = "frontend/src/app/filterx/page.tsx"
    _write(tmp_path / page, "export default function MyPage(){return <p>My application</p>}\n")
    ops, _ = web._operations(tmp_path, cfg, ir, web.NEXTJS)
    page_op = next(op for op in ops if op.path == page)
    assert page_op.write_policy == "create_once"
    assert page_op.metadata == {"layer": "custom"}


def test_load_ir_respects_output_location(tmp_path, web, ir):
    cfg = default_config()
    cfg["output"]["ir_file"] = "artifacts/custom-ir.json"
    _write(tmp_path / ".filterx/ir.json", json.dumps(replace(ir, entities=()).to_dict()))
    _write(tmp_path / cfg["output"]["ir_file"], json.dumps(ir.to_dict()))
    assert web._load_ir(tmp_path, cfg) == ir


def _legacy_scan(ir):
    return {"entities": [{"model": entity.name, "table": entity.identity.table,
                          "primary_keys": list(entity.identity.primary_keys),
                          "fields": [{"name": field.name, "type": field.type.value, "nullable": field.nullable,
                                      "primary_key": field.primary_key, "ops": list(field.operations)} for field in entity.fields],
                          "relationships": []} for entity in ir.entities]}


@pytest.mark.parametrize("scan_newer,source", [(True, "sqlalchemy"), (False, "sqlalchemy"), (False, "prisma")])
def test_canonical_sqlalchemy_scan_is_not_shadowed_by_stale_ir(tmp_path, web, ir, scan_newer, source):
    cfg = default_config()
    cfg["output"].update(scan_file="artifacts/scan.json", ir_file="artifacts/ir.json")
    scan = tmp_path / cfg["output"]["scan_file"]
    artifact = tmp_path / cfg["output"]["ir_file"]
    _write(scan, json.dumps(_legacy_scan(replace(ir, entities=(ir.entities[1],)))))
    _write(artifact, json.dumps(replace(ir, source_framework=source).to_dict()))
    scan_time = 200 if scan_newer else 100
    os.utime(scan, (scan_time, scan_time))
    os.utime(artifact, (150, 150))
    result = web._load_ir(tmp_path, cfg)
    assert [entity.name for entity in result.entities] == (["Book"] if scan_newer or source != "sqlalchemy" else ["Author", "Book"])
    assert result.source_framework == "sqlalchemy"


@pytest.mark.parametrize("framework", ["prisma", "jpa"])
def test_non_sqlalchemy_requires_current_matching_ir(tmp_path, web, ir, framework):
    cfg = default_config()
    cfg["scan"]["framework"] = framework
    scan = tmp_path / cfg["output"]["scan_file"]
    artifact = tmp_path / cfg["output"]["ir_file"]
    _write(scan, json.dumps(_legacy_scan(ir)))
    with pytest.raises(ValueError, match="Missing IR.*filterx scan"):
        web._load_ir(tmp_path, cfg)
    _write(artifact, json.dumps(ir.to_dict()))
    with pytest.raises(ValueError, match="does not match scan.framework"):
        web._load_ir(tmp_path, cfg)
    expected = replace(ir, source_framework=framework)
    _write(artifact, json.dumps(expected.to_dict()))
    os.utime(scan, (100, 100))
    os.utime(artifact, (200, 200))
    assert web._load_ir(tmp_path, cfg) == expected
    os.utime(scan, (300, 300))
    with pytest.raises(ValueError, match="scan is newer.*filterx scan"):
        web._load_ir(tmp_path, cfg)


@pytest.mark.parametrize("framework", ["REACT_VITE", "NEXTJS", "VUE"])
@pytest.mark.parametrize("anchor", ["MISSING ANCHOR", ""])
def test_unmounted_host_is_preserved_with_actionable_warning(tmp_path, web, ir, framework, anchor):
    target = getattr(web, framework)
    cfg = _setup(tmp_path, web, target, host_anchor=anchor)
    host = tmp_path / "frontend" / web._target_config(cfg, target)["host_file"]
    source = "<!-- Custom host, no anchor -->" if target is web.VUE else "// Custom host, no anchor\n"
    _write(host, source)
    ops, settings = web._operations(tmp_path, cfg, ir, target)
    assert host.read_text(encoding="utf-8") == source
    assert all(op.write_policy == "create_once" for op in ops if op.path == host.relative_to(tmp_path).as_posix())
    assert settings["warnings"][0]["code"] == "FRONTEND_HOST_NOT_MOUNTED"
    assert "Import" in settings["warnings"][0]["message"]
    assert "FilterxShell" in settings["warnings"][0]["message"]


def test_install_uses_real_shared_lifecycle(tmp_path, web, ir):
    cfg = _setup(tmp_path, web, web.REACT_VITE)
    _write(tmp_path / "filterx.yaml", json.dumps(cfg))
    _write(tmp_path / ".filterx/ir.json", json.dumps(ir.to_dict()))
    args = SimpleNamespace(project_root=str(tmp_path), config=str(tmp_path / "filterx.yaml"), dry_run=False, json=True)
    assert web.ReactViteRenderer().install(args) == 0
    state = json.loads((tmp_path / ".filterx/frontend-react-vite.json").read_text())
    assert state["schema"] == web.schema_from_ir(ir)
    assert "frontend/src/filterx-custom/FilterxShell.tsx" in state["files"]


def test_css_is_scoped_and_extension_contracts_are_typed():
    css = (TEMPLATES / "filterx.css").read_text()
    assert ":root" not in css and "!important" not in css
    selectors = re.findall(r"(?:^|\})([^{}]+)\{", css, re.MULTILINE)
    assert all(selector.strip().startswith((".fx-", "@media")) for group in selectors for selector in group.split(","))
    react = (TEMPLATES / "FilterxApp.tsx").read_text(encoding="utf-8")
    for prop in ("renderHeader", "renderToolbar", "renderCell"):
        assert f"{prop}?: (context: Filterx" in react
    assert "key={entity.route}" in react
    vue = (TEMPLATES / "FilterxApp.vue").read_text(encoding="utf-8")
    for name in ("header", "toolbar", "cell"):
        assert f'<slot name="{name}"' in vue
    assert "defineSlots<" in vue


@pytest.mark.parametrize("framework", ["react-vite", "nextjs", "vue"])
@pytest.mark.parametrize("artifact", ["ir", "scan"])
def test_real_reinstall_preserves_custom_files(tmp_path, framework, ir, artifact):
    from filterx.renderers import web_frontends as renderer
    target = {"react-vite": renderer.REACT_VITE, "nextjs": renderer.NEXTJS, "vue": renderer.VUE}[framework]
    cfg = _setup(tmp_path, renderer, target)
    cfg["safety"]["dry_run_default"] = False
    config = tmp_path / "filterx.yaml"
    _write(config, json.dumps(cfg))
    _write(tmp_path / ".filterx/ir.json", json.dumps(ir.to_dict()))
    _write(tmp_path / "frontend/package.json", '{"private":true}')
    args = SimpleNamespace(project_root=str(tmp_path), config=str(config), dry_run=False, check=False, json=True)
    instance = renderer.WebFrontendRenderer(target)
    assert instance.install(args) == 0
    custom = tmp_path / renderer.customization_root(cfg, framework)
    paths = [custom / ("FilterxShell.vue" if framework == "vue" else "FilterxShell.tsx"), custom / "theme.css"]
    if framework == "nextjs":
        paths.append(tmp_path / "frontend/src/app/filterx/page.tsx")
    originals = {}
    for path in paths:
        path.write_bytes(path.read_bytes() + b"\n/* user customization */\n")
        originals[path] = path.read_bytes()
    presentation = custom / "presentation.json"
    _write(presentation, json.dumps({"Book": {"label": "Library", "columns": ["title"], "labels": {"title": "Book title"}}}))
    originals[presentation] = presentation.read_bytes()
    runtime = tmp_path / "frontend/src/filterx-generated"
    runtime_files = {path: path.read_bytes() for path in runtime.iterdir() if path.name not in {"types.ts", "entities.ts", "presentation.ts"}}
    changed = replace(ir, entities=(ir.entities[1],))
    if artifact == "scan":
        _write(tmp_path / ".filterx/scan.json", json.dumps(_legacy_scan(changed)))
        old_ir = tmp_path / ".filterx/ir.json"
        os.utime(old_ir, (100, 100))
    else:
        _write(tmp_path / ".filterx/ir.json", json.dumps(changed.to_dict()))
    assert instance.install(args) == 0
    assert all(path.read_bytes() == contents for path, contents in originals.items())
    assert all(path.read_bytes() == contents for path, contents in runtime_files.items())
    assert "Author" not in (runtime / "entities.ts").read_text(encoding="utf-8")
    assert "Library" in (runtime / "presentation.ts").read_text(encoding="utf-8")


def _node_modules(framework: str) -> Path:
    override = REPO / "filterx-matrix-20260820/projects" / f"express-prisma__{framework}" / "frontend/node_modules"
    if not shutil.which("node") or not (override / "typescript/lib/tsc.js").exists():
        pytest.skip("Optional local Node/TypeScript matrix dependencies are not installed")
    return override


def _runtime_project(tmp_path, web, ir, framework):
    """Compile and browse a real install, never hand-built runtime/template copies."""
    target = {"react-vite": web.REACT_VITE, "nextjs": web.NEXTJS, "vue": web.VUE}[framework]
    cfg = _setup(tmp_path, web, target)
    cfg["safety"]["dry_run_default"] = False
    config = tmp_path / "filterx.yaml"
    _write(config, json.dumps(cfg))
    _write(tmp_path / ".filterx/ir.json", json.dumps(ir.to_dict()))
    custom = tmp_path / web.customization_root(cfg, framework)
    _write(custom / "theme.css", ".fx-shell { border-top: 7px solid rgb(12, 34, 56); }\n")
    _write(custom / "presentation.json", json.dumps({
        "Author": {"label": "People", "columns": ["name", "removed", "secret", "name"], "labels": {"name": "Display name"}},
        "Book": {"label": "Library", "columns": ["title"], "labels": {"title": "Book title"}},
    }))
    args = SimpleNamespace(project_root=str(tmp_path), config=str(config), dry_run=False, check=False, json=True)
    assert web.WebFrontendRenderer(target).install(args) == 0
    return tmp_path / "frontend"


@pytest.mark.parametrize("framework", ["react-vite", "nextjs", "vue"])
def test_generated_runtime_typechecks(tmp_path, web, ir, framework):
    deps = _node_modules(framework)
    project = _runtime_project(tmp_path, web, ir, framework)
    paths = ({"vue": [str(deps / "vue/dist/vue.d.ts")]} if framework == "vue" else {
        "react": [str(deps / "@types/react/index.d.ts")],
        "react/jsx-runtime": [str(deps / "@types/react/jsx-runtime.d.ts")],
    })
    _write(project / "tsconfig.json", json.dumps({"compilerOptions": {
        "target": "ES2020", "module": "ESNext", "moduleResolution": "Bundler", "strict": True,
        "skipLibCheck": True, "noEmit": True, "jsx": "react-jsx", "lib": ["ES2020", "DOM"], "paths": paths,
    }, "include": ["src/**/*.ts", "src/**/*.tsx", "src/**/*.vue"]}))
    executable = deps / ("vue-tsc/bin/vue-tsc.js" if framework == "vue" else "typescript/lib/tsc.js")
    result = subprocess.run(["node", str(executable), "-p", str(project / "tsconfig.json")], capture_output=True, text=True, encoding="utf-8", timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr


def test_next_client_boundary_production_build(tmp_path, web, ir):
    deps = _node_modules("nextjs")
    project = _runtime_project(tmp_path, web, ir, "nextjs")
    # A server route imports a client shell, which imports the interactive runtime.
    # Checking the installed output also catches omitted or misplaced directives.
    for relative in ("src/filterx-generated/FilterxApp.tsx", "src/filterx-custom/FilterxShell.tsx"):
        assert (project / relative).read_text(encoding="utf-8").startswith("'use client';\n")
    page = project / "src/app/filterx/page.tsx"
    assert "use client" not in page.read_text(encoding="utf-8")
    _write(project / "src/app/layout.tsx", "import type {ReactNode} from 'react';\nexport default function Layout({children}: {children: ReactNode}) {return <html><body>{children}</body></html>}\n")
    _write(project / "next.config.mjs", "export default {experimental: {cpus: 1}};\n")
    modules = project / "node_modules"
    if os.name == "nt":
        link = subprocess.run(["cmd", "/d", "/c", "mklink", "/J", str(modules), str(deps)], capture_output=True, text=True, timeout=20)
        assert link.returncode == 0, link.stdout + link.stderr
    else:
        modules.symlink_to(deps, target_is_directory=True)
    try:
        env = {**os.environ, "NEXT_TELEMETRY_DISABLED": "1"}
        result = subprocess.run(["node", str(deps / "next/dist/bin/next"), "build", "--no-lint"], cwd=project, env=env,
                                capture_output=True, text=True, encoding="utf-8", timeout=240)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "/filterx" in result.stdout
    finally:
        # Remove only the temporary link, never recurse into matrix dependencies.
        modules.rmdir() if os.name == "nt" else modules.unlink()


_BROWSER_CHECK = r"""
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const [root, deps, playwrightPath, vueCompiler, framework, executablePath, esbuildPath] = process.argv.slice(2);
const { build } = require(esbuildPath);
const { chromium } = require(playwrightPath);
const plugins = framework === 'vue' ? [{name:'vue',setup(build){build.onLoad({filter:/\.vue$/}, async args => {
  const { parse, compileScript } = require(vueCompiler);
  const { descriptor } = parse(fs.readFileSync(args.path,'utf8'), {filename:args.path});
  const script = compileScript(descriptor, {id:args.path,inlineTemplate:true});
  return {contents:script.content,loader:'ts',resolveDir:path.dirname(args.path)};
});}}] : [];
(async () => {
    const result = await build({entryPoints:[path.join(root,'entry.tsx')],outdir:path.join(root,'bundle'),bundle:true,write:false,platform:'browser',format:'iife',jsx:'automatic',nodePaths:[deps],plugins,define:{'process.env.NODE_ENV':'"development"'}});
    const browserPath = executablePath || chromium.executablePath();
    if (!fs.existsSync(browserPath)) { console.log('Optional Chromium binary is not installed'); process.exitCode=77; return; }
    const browser = await chromium.launch({headless:true,executablePath:browserPath});
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(String(error)));
    await page.setContent('<div id="root"></div>');
    await page.evaluate(() => {
      window.pending = [];
      window.fetch = (url, init) => new Promise(resolve => window.pending.push({url,init,resolve,done:false}));
    });
    await page.addStyleTag({content:result.outputFiles.find(file=>file.path.endsWith('.css')).text});
    await page.addScriptTag({content:result.outputFiles.find(file=>file.path.endsWith('.js')).text});
    const waitFor = async fragment => { await page.waitForFunction(fragment => window.pending.some(p => !p.done && p.url.includes(fragment)),fragment); };
        const resolve = async (fragment, data, status=200) => {
      await waitFor(fragment);
            await page.evaluate(({fragment,data,status}) => { const p=window.pending.find(p=>!p.done&&p.url.includes(fragment));p.done=true;p.resolve(new Response(JSON.stringify(data),{status})); },{fragment,data,status});
    };
    const response = data => ({data,meta:{page:1,size:20,total_items:60,total_pages:3}});
    await resolve('/authors?',response([{id:1,name:'Alice'}]));
    await page.getByText('ALICE',{exact:true}).waitFor();
    assert.equal(await page.locator('.fx-shell').evaluate(el=>getComputedStyle(el).borderTopWidth),'7px');
    assert.equal(await page.locator('th').count(),1); // removed, duplicate and redacted columns excluded
    assert.match(await page.locator('th').innerText(),/Display name/);
    await page.getByRole('button',{name:'Display name'}).click();
    await resolve('sort_by=name',response([{id:1,name:'Alice'}]));
    await page.locator('.fx-pagination select').selectOption('50');
    await resolve('size=50',response([{id:1,name:'Alice'}]));
    await page.getByRole('button',{name:'Next',exact:true}).click();
    await resolve('page=2',response([{id:1,name:'Alice'}]));
    await page.getByRole('button',{name:'+ condition',exact:true}).click();
    await page.locator('.fx-condition select').first().selectOption('name');
    await page.locator('.fx-condition input').fill('obsolete');
    await page.getByRole('button',{name:'Apply filters',exact:true}).click();
    await waitFor('/authors/filter?'); // leave old query pending
    await page.locator('.fx-toolbar select').selectOption('name');
    await page.getByRole('button',{name:'Group',exact:true}).click();
    await waitFor('/authors/group-by/name/filter'); // leave old grouping pending
    const bodies = await page.evaluate(() => window.pending.filter(p=>p.url.includes('/authors/')&&p.init?.method==='POST').map(p=>JSON.parse(p.init.body)));
    assert.ok(bodies.length>=2);
    assert.ok(bodies.every(body=>body.filter_tree.children[0].field==='name'));
    await page.getByRole('button',{name:'Library',exact:true}).click();
    await waitFor('/books?');
    const request = await page.evaluate(() => window.pending.find(p=>!p.done&&p.url.includes('/books?')).url);
    assert.match(request,/page=1&size=20/);
    assert.match(request,/sort_by=id&order=asc/);
    assert.equal(await page.locator('.fx-condition').count(),0);
    assert.equal(await page.locator('.fx-toolbar select').inputValue(),'');
    assert.equal(await page.getByLabel('Search',{exact:true}).inputValue(),'');
    assert.equal(await page.locator('tbody tr').count(),0);
    await resolve('/books?',response([{id:2,title:'Fresh'}]));
    await page.getByText('FRESH',{exact:true}).waitFor();
    await resolve('/authors/filter?',response([{id:3,name:'Obsolete'}]));
    await resolve('/authors/group-by/name/filter',[{key:'Obsolete group',count:4}]);
    // Two animation frames let both framework update queues flush without a time delay.
    await page.evaluate(() => new Promise(done=>requestAnimationFrame(()=>requestAnimationFrame(done))));
    assert.equal(await page.getByText('FRESH',{exact:true}).count(),1);
    assert.equal(await page.locator('.fx-groups').count(),0);
    assert.equal(await page.locator('[data-custom-header]').innerText(),'Book:1');
    assert.equal(await page.locator('[data-custom-cell]').innerText(),'FRESH');
    assert.equal(await page.getByRole('button',{name:'CSV',exact:true}).count(),1);
    assert.equal(await page.getByRole('button',{name:'Apply filters',exact:true}).count(),1);
    await page.locator('.fx-toolbar select').selectOption('title');
    await page.getByRole('button',{name:'Group',exact:true}).click();
    await waitFor('/books/group-by/title');
    await page.getByRole('button',{name:'Refresh custom',exact:true}).click();
    await resolve('/books?',response([{id:2,title:'Reloaded'}]));
    await page.getByText('RELOADED',{exact:true}).waitFor();
    await resolve('/books/group-by/title',[{key:'Stale before refresh',count:3}]);
    await page.evaluate(() => new Promise(done=>requestAnimationFrame(()=>requestAnimationFrame(done))));
    assert.equal(await page.locator('.fx-groups').count(),0);
    await page.getByLabel('Search',{exact:true}).fill('slow'); await waitFor('search=slow');
    await page.getByLabel('Search',{exact:true}).fill('fast'); await waitFor('search=fast');
    await resolve('search=fast',response([{id:2,title:'Newest'}]));
    await page.getByText('NEWEST',{exact:true}).waitFor();
    await resolve('search=slow',response([{id:2,title:'Old query'}]));
    await page.evaluate(() => new Promise(done=>requestAnimationFrame(()=>requestAnimationFrame(done))));
    assert.equal(await page.getByText('NEWEST',{exact:true}).count(),1);
    await page.getByRole('button',{name:'Book title',exact:true}).click();
    await resolve('sort_by=title',response([{id:2,title:'Newest'}]));
    await page.getByRole('button',{name:'CSV',exact:true}).click();
    await waitFor('/books/export?');
    const exported = await page.evaluate(() => {const p=window.pending.find(p=>!p.done&&p.url.includes('/books/export?'));return {url:p.url,init:p.init};});
    assert.match(exported.url,/sort_by=title/);
    assert.match(exported.url,/search=fast/);
    assert.equal(exported.init.method,'POST');
    assert.deepEqual(JSON.parse(exported.init.body),{filter_tree:null});
    await resolve('/books/export?',{error:{message:'Export denied'}},403);
    await page.locator('.fx-error').filter({hasText:'Export denied'}).waitFor();
    await page.getByLabel('Search',{exact:true}).fill('denied');
    await resolve('search=denied',{error:{message:'Query denied'}},403);
    await page.locator('.fx-error').filter({hasText:'Query denied'}).waitFor();
    assert.equal(await page.locator('th').count(),1); // no schema/local fallback restores redacted data
    assert.deepEqual(errors,[]);
    console.log(framework + ': slots/props, raw keys, entity reset, stale query/group guards passed');
  } finally { await browser.close(); }
})().catch(error => {console.error(error);process.exitCode=1;});
"""


@pytest.mark.parametrize("framework", ["react-vite", "nextjs", "vue"])
def test_generated_ui_in_browser(tmp_path, web, ir, framework):
    deps = _node_modules(framework)
    playwright = REPO / "frontend/node_modules/@playwright/test"
    compiler = _node_modules("vue") / "@vue/compiler-sfc"
    esbuild = _node_modules("react-vite") / "esbuild"
    if not (playwright / "package.json").exists() or not (esbuild / "package.json").exists():
        pytest.skip("Optional local browser tooling is not installed")
    project = _runtime_project(tmp_path, web, ir, framework)
    if framework == "vue":
        entry = """import {createApp,h} from 'vue';
import FilterxApp from './src/filterx-custom/FilterxShell.vue';
createApp({render:()=>h(FilterxApp,{}, {
header:ctx=>h('h1',{'data-custom-header':''},ctx.entity.name+':'+ctx.rows.length),
toolbar:ctx=>h('button',{onClick:ctx.refresh},'Refresh custom'),
cell:ctx=>h('span',{'data-custom-cell':''},String(ctx.value).toUpperCase())
})}).mount('#root');"""
    else:
        entry = """import {createRoot} from 'react-dom/client';
import {FilterxShell as FilterxApp} from './src/filterx-custom/FilterxShell';
createRoot(document.getElementById('root')!).render(<FilterxApp
renderHeader={ctx=><h1 data-custom-header>{ctx.entity.name}:{ctx.rows.length}</h1>}
renderToolbar={ctx=><button onClick={ctx.refresh}>Refresh custom</button>}
renderCell={ctx=><span data-custom-cell>{String(ctx.value).toUpperCase()}</span>}/>);"""
    _write(project / "entry.tsx", entry)
    _write(project / "check.cjs", _BROWSER_CHECK)
    chromium = os.environ.get("FILTERX_TEST_CHROMIUM", "")
    if not chromium and os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        cached = sorted((Path(os.environ["LOCALAPPDATA"]) / "ms-playwright").glob("chromium-*/chrome-win*/chrome.exe"))
        chromium = str(cached[-1]) if cached else ""
    result = subprocess.run(["node", str(project / "check.cjs"), str(project), str(deps), str(playwright), str(compiler), framework, chromium, str(esbuild)], capture_output=True, text=True, encoding="utf-8", timeout=120)
    if result.returncode == 77:
        pytest.skip(result.stdout)
    assert result.returncode == 0, result.stdout + result.stderr