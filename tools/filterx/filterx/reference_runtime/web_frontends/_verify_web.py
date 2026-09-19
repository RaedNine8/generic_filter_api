"""One-shot isolated source verification while the parent lifecycle is unavailable."""
from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import subprocess
import tempfile


REPO = Path(__file__).resolve().parents[5]
RENDERER = REPO / "tools/filterx/filterx/renderers/web_frontends.py"
TEST = REPO / "tools/filterx/tests/test_web_customization.py"


def main():
    # Execute only real pure rendering definitions; do not import or replace the
    # missing lifecycle or PatchOp. The full-install pytest tests remain separate.
    tree = ast.parse(RENDERER.read_text(encoding="utf-8"))
    pure = {"WebTarget", "_target_config", "_slug", "_ts_type", "_render_types", "_render_entities", "_render_api", "_relative_import"}
    selected = [node for node in tree.body if
                isinstance(node, ast.Import) or
                isinstance(node, ast.ImportFrom) and node.module in {"__future__", "dataclasses", "pathlib", "typing", "filterx.core.ir"} or
                isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in pure or
                isinstance(node, ast.Assign)]
    namespace = {"__file__": str(RENDERER)}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(RENDERER), "exec"), namespace)
    tests = ast.parse(TEST.read_text(encoding="utf-8"))
    ir_import = next(node for node in tests.body if isinstance(node, ast.ImportFrom) and node.module == "filterx.core.ir")
    fixture = next(node for node in tests.body if isinstance(node, ast.FunctionDef) and node.name == "ir")
    fixture.decorator_list = []
    exec(compile(ast.Module(body=[ir_import, fixture], type_ignores=[]), str(TEST), "exec"), namespace)
    ir = namespace["ir"]()
    browser_script = next(ast.literal_eval(node.value) for node in tests.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "_BROWSER_CHECK" for target in node.targets))
    browser_test = next(node for node in tests.body if isinstance(node, ast.FunctionDef) and node.name == "test_generated_ui_in_browser")
    entries = [ast.literal_eval(node.value) for node in ast.walk(browser_test) if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "entry" for target in node.targets)]
    operations = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_operations")
    start = next(i for i, node in enumerate(operations.body) if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "shell_path" for target in node.targets))
    shell_nodes = operations.body[start:start + 3]
    cached = sorted((Path(os.environ["LOCALAPPDATA"]) / "ms-playwright").glob("chromium-*/chrome-win*/chrome.exe"))
    with tempfile.TemporaryDirectory(prefix="filterx-web-source-") as directory:
        base = Path(directory)
        print(f"Isolated source check directory: {base}", flush=True)
        for framework, target_name in (("react-vite", "REACT_VITE"), ("nextjs", "NEXTJS"), ("vue", "VUE")):
            project = base / framework
            generated = project / "src/filterx-generated"
            custom = project / "src/filterx-custom"
            generated.mkdir(parents=True)
            custom.mkdir(parents=True)
            deps = REPO / f"filterx-matrix-20260820/projects/express-prisma__{framework}/frontend/node_modules"
            client = "'use client';\n" if framework == "nextjs" else ""
            extension = ".vue" if framework == "vue" else ".tsx"
            for file, constant in (("contracts.ts", "CONTRACTS"), ("display.ts", "DISPLAY"), ("filterx.css", "CSS")):
                (generated / file).write_text(namespace[constant], encoding="utf-8")
            (generated / "api.ts").write_text(namespace["_render_api"]("/api/filterx"), encoding="utf-8")
            (generated / "types.ts").write_text(namespace["_render_types"](ir), encoding="utf-8")
            (generated / "entities.ts").write_text(namespace["_render_entities"](ir), encoding="utf-8")
            (generated / "presentation.ts").write_text("export const FILTERX_PRESENTATION = " + json.dumps({
                "Author": {"label": "People", "columns": ["name", "removed", "secret", "name"], "labels": {"name": "Display name"}},
                "Book": {"label": "Library", "columns": ["title"], "labels": {"title": "Book title"}},
            }) + ";\n", encoding="utf-8")
            (generated / ("FilterxApp" + extension)).write_text(namespace["VUE_COMPONENT"] if framework == "vue" else client + namespace["REACT_COMPONENT"], encoding="utf-8")
            if framework == "vue":
                (generated / "FilterxFilterBuilder.vue").write_text(namespace["VUE_BUILDER"], encoding="utf-8")
            namespace.update(target=namespace[target_name], root=generated.as_posix(), custom=custom.as_posix(), client=client, extension=extension)
            exec(compile(ast.Module(body=shell_nodes, type_ignores=[]), str(RENDERER), "exec"), namespace)
            (custom / ("FilterxShell" + extension)).write_text(namespace["shell"], encoding="utf-8")
            (custom / "theme.css").write_text(".fx-shell { border-top: 7px solid rgb(12, 34, 56); }\n", encoding="utf-8")
            paths = {"vue": [str(deps / "vue/dist/vue.d.ts")]} if framework == "vue" else {
                "react": [str(deps / "@types/react/index.d.ts")],
                "react/jsx-runtime": [str(deps / "@types/react/jsx-runtime.d.ts")],
            }
            (project / "tsconfig.json").write_text(json.dumps({"compilerOptions": {"target": "ES2020", "module": "ESNext", "moduleResolution": "Bundler", "strict": True, "skipLibCheck": True, "noEmit": True, "jsx": "react-jsx", "lib": ["ES2020", "DOM"], "paths": paths}, "include": ["src/**/*.ts", "src/**/*.tsx", "src/**/*.vue"]}), encoding="utf-8")
            compiler = deps / ("vue-tsc/bin/vue-tsc.js" if framework == "vue" else "typescript/lib/tsc.js")
            subprocess.run(["node", str(compiler), "-p", str(project / "tsconfig.json")], check=True, timeout=90)
            print(framework + ": real tsc/vue-tsc passed", flush=True)
            (project / "entry.tsx").write_text(entries[0 if framework == "vue" else 1], encoding="utf-8")
            (project / "check.cjs").write_text(browser_script, encoding="utf-8")
            subprocess.run(["node", str(project / "check.cjs"), str(project), str(deps), str(REPO / "frontend/node_modules/@playwright/test"), str(REPO / "filterx-matrix-20260820/projects/express-prisma__vue/frontend/node_modules/@vue/compiler-sfc"), framework, str(cached[-1]), str(REPO / "filterx-matrix-20260820/projects/express-prisma__react-vite/frontend/node_modules/esbuild")], check=True, timeout=120)
            if framework == "nextjs":
                route = project / "src/app/filterx/page.tsx"
                route.parent.mkdir(parents=True)
                route.write_text("import {FilterxShell} from '../../filterx-custom/FilterxShell';\nexport default function Page(){return <FilterxShell />}\n", encoding="utf-8")
                (project / "package.json").write_text(json.dumps({"private": True, "dependencies": {"next": "^15.0.0", "react": "^19.0.0", "react-dom": "^19.0.0"}, "devDependencies": {"typescript": "^5.7.0", "@types/react": "^19.0.0", "@types/node": "^22.0.0"}}), encoding="utf-8")
                write = next(node for node in tests.body if isinstance(node, ast.FunctionDef) and node.name == "_write")
                build_test = next(node for node in tests.body if isinstance(node, ast.FunctionDef) and node.name == "test_next_client_boundary_production_build")
                namespace.update(project=project, deps=deps, subprocess=subprocess, os=os)
                exec(compile(ast.Module(body=[write] + build_test.body[2:], type_ignores=[]), str(TEST), "exec"), namespace)
                print("nextjs: production build with server-to-client boundary passed", flush=True)


if __name__ == "__main__":
    main()