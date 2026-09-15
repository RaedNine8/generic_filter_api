from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from filterx.commands import frontend
from filterx.core.config import default_config
from golden_support import command_args
from test_spring_boot_jpa_install import _spring_ir

pytestmark = pytest.mark.skipif(
    os.environ.get("FILTERX_RUN_WEB_E2E") != "1",
    reason="set FILTERX_RUN_WEB_E2E=1 to install npm packages and compile all generated web targets",
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _npm() -> str:
    command = shutil.which("npm")
    if not command:
        pytest.skip("npm is not installed")
    return command


def _base(root: Path, framework: str, package: dict[str, object]) -> tuple[Path, Path]:
    project = root / framework
    project.mkdir()
    config = default_config()
    config["frontend"]["framework"] = framework
    config["backend"]["enabled"] = False
    config["database"]["enabled"] = False
    config["safety"]["dry_run_default"] = False
    config_path = project / "filterx.yaml"
    _write(config_path, json.dumps(config, indent=2) + "\n")
    _write(project / ".filterx/ir.json", json.dumps(_spring_ir().to_dict(), indent=2) + "\n")
    _write(project / "frontend/package.json", json.dumps(package, indent=2) + "\n")
    return project, config_path


def _react(root: Path) -> tuple[Path, Path]:
    project, config = _base(root, "react-vite", {"name": "fx-react", "private": True, "type": "module", "scripts": {"build": "tsc -b && vite build"}})
    _write(project / "frontend/index.html", '<div id="root"></div><script type="module" src="/src/main.tsx"></script>\n')
    _write(project / "frontend/src/main.tsx", "import { StrictMode } from 'react'; import { createRoot } from 'react-dom/client'; import App from './App'; createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>);\n")
    _write(project / "frontend/src/App.tsx", "export default function App(){ return <main>// FILTERX:APP</main>; }\n")
    _write(project / "frontend/tsconfig.json", json.dumps({"compilerOptions": {"target": "ES2022", "useDefineForClassFields": True, "lib": ["ES2022", "DOM", "DOM.Iterable"], "allowJs": False, "skipLibCheck": True, "esModuleInterop": True, "allowSyntheticDefaultImports": True, "strict": True, "forceConsistentCasingInFileNames": True, "module": "ESNext", "moduleResolution": "Bundler", "resolveJsonModule": True, "isolatedModules": True, "noEmit": True, "jsx": "react-jsx"}, "include": ["src"]}, indent=2))
    _write(project / "frontend/vite.config.ts", "import { defineConfig } from 'vite'; import react from '@vitejs/plugin-react'; export default defineConfig({plugins:[react()]});\n")
    return project, config


def _next(root: Path) -> tuple[Path, Path]:
    project, config = _base(root, "nextjs", {"name": "fx-next", "private": True, "scripts": {"build": "next build"}})
    _write(project / "frontend/src/app/layout.tsx", "export default function Layout({children}:{children:React.ReactNode}){return <html><body>{children}</body></html>}\n")
    _write(project / "frontend/src/app/page.tsx", "export default function Home(){return <a href='/filterx'>FilterX</a>}\n")
    _write(project / "frontend/next.config.ts", "import type { NextConfig } from 'next'; const config: NextConfig = {}; export default config;\n")
    _write(project / "frontend/tsconfig.json", json.dumps({"compilerOptions": {"target": "ES2017", "lib": ["dom", "dom.iterable", "esnext"], "allowJs": True, "skipLibCheck": True, "strict": True, "noEmit": True, "esModuleInterop": True, "module": "esnext", "moduleResolution": "bundler", "resolveJsonModule": True, "isolatedModules": True, "jsx": "preserve", "incremental": True}, "include": ["next-env.d.ts", ".next/types/**/*.ts", "**/*.ts", "**/*.tsx"], "exclude": ["node_modules"]}, indent=2))
    _write(project / "frontend/next-env.d.ts", '/// <reference types="next" />\n/// <reference types="next/image-types/global" />\n')
    return project, config


def _vue(root: Path) -> tuple[Path, Path]:
    project, config = _base(root, "vue", {"name": "fx-vue", "private": True, "type": "module", "scripts": {"build": "vue-tsc -b && vite build"}})
    _write(project / "frontend/index.html", '<div id="app"></div><script type="module" src="/src/main.ts"></script>\n')
    _write(project / "frontend/src/main.ts", "import { createApp } from 'vue'; import App from './App.vue'; createApp(App).mount('#app');\n")
    _write(project / "frontend/src/App.vue", '<script setup lang="ts">\nconst host=true;\n</script>\n<template><!-- FILTERX:APP --></template>\n')
    _write(project / "frontend/src/env.d.ts", '/// <reference types="vite/client" />\n')
    _write(project / "frontend/tsconfig.json", json.dumps({"compilerOptions": {"target": "ES2022", "useDefineForClassFields": True, "module": "ESNext", "lib": ["ES2022", "DOM", "DOM.Iterable"], "skipLibCheck": True, "moduleResolution": "Bundler", "allowImportingTsExtensions": True, "resolveJsonModule": True, "isolatedModules": True, "noEmit": True, "strict": True}, "include": ["src/**/*.ts", "src/**/*.vue"]}, indent=2))
    _write(project / "frontend/vite.config.ts", "import { defineConfig } from 'vite'; import vue from '@vitejs/plugin-vue'; export default defineConfig({plugins:[vue()]});\n")
    return project, config


@pytest.mark.parametrize("factory", [_react, _next, _vue])
def test_generated_web_target_compiles(tmp_path: Path, factory) -> None:
    project, config = factory(tmp_path)
    assert frontend.run_install(command_args(project, config)) == 0
    subprocess.run([_npm(), "install", "--no-audit", "--no-fund"], cwd=project / "frontend", check=True, timeout=600)
    subprocess.run([_npm(), "run", "build"], cwd=project / "frontend", check=True, timeout=600)
