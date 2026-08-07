from __future__ import annotations

import json
import os
from pathlib import Path

from filterx.commands import backend, rollback, scan
from filterx.core.config import default_config
from golden_support import command_args


def _write_express_project(project_root: Path) -> tuple[Path, str]:
    project_root.mkdir()
    package_document = {
        "name": "express-filterx-fixture",
        "version": "1.0.0",
        "private": True,
        "type": "module",
        "scripts": {"host:test": "echo host"},
        "dependencies": {"@prisma/client": "^6.0.0", "express": "^5.0.0"},
        "devDependencies": {"prisma": "^6.0.0", "typescript": "^5.7.0"},
    }
    original_package = json.dumps(package_document, indent=4) + "\n"
    (project_root / "package.json").write_text(original_package, encoding="utf-8")
    (project_root / "tsconfig.json").write_text(
        json.dumps(
            {
                "compilerOptions": {
                    "target": "ES2022",
                    "module": "NodeNext",
                    "moduleResolution": "NodeNext",
                    "strict": True,
                    "esModuleInterop": True,
                    "outDir": "dist",
                },
                "include": ["src/**/*.ts"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (project_root / "src").mkdir()
    (project_root / "src/app.ts").write_text(
        "import express from 'express';\n\n"
        "export const app = express();\n"
        "app.use(express.json());\n\n"
        "// FILTERX:ROUTER_MOUNT\n",
        encoding="utf-8",
    )
    schema = project_root / "prisma/schema.prisma"
    schema.parent.mkdir()
    schema.write_text(
        "generator client {\n"
        "  provider = \"prisma-client-js\"\n"
        "}\n\n"
        "datasource db {\n"
        "  provider = \"sqlite\"\n"
        "  url = env(\"DATABASE_URL\")\n"
        "}\n\n"
        "model Author {\n"
        "  id Int @id @default(autoincrement())\n"
        "  name String\n"
        "  books Book[]\n"
        "}\n\n"
        "model Book {\n"
        "  id Int @id @default(autoincrement())\n"
        "  title String\n"
        "  genre String\n"
        "  price Decimal\n"
        "  note String?\n"
        "  authorId Int\n"
        "  author Author @relation(fields: [authorId], references: [id])\n"
        "}\n",
        encoding="utf-8",
    )
    marker = project_root / "node_modules/.prisma/client/index.js"
    marker.parent.mkdir(parents=True)
    marker.write_text("// generated marker\n", encoding="utf-8")
    os.utime(marker, (schema.stat().st_mtime + 10, schema.stat().st_mtime + 10))

    config = default_config()
    config["project"]["name"] = "express_filterx_fixture"
    config["scan"]["framework"] = "prisma"
    config["backend"]["framework"] = "express-prisma"
    config["frontend"]["enabled"] = False
    config["database"]["enabled"] = False
    config["safety"]["dry_run_default"] = False
    config_path = project_root / "filterx.yaml"
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return config_path, original_package


def test_express_prisma_generation_dependency_merge_and_rollback(tmp_path: Path) -> None:
    project_root = tmp_path / "express_project"
    config_path, original_package = _write_express_project(project_root)
    args = command_args(project_root, config_path)

    assert scan.run(args) == 0
    assert (project_root / ".filterx/ir.json").exists()

    preview_args = command_args(project_root, config_path, dry_run=True)
    assert backend.run_install(preview_args) == 0
    assert not (project_root / "src/filterx-generated/router.ts").exists()

    assert backend.run_install(args) == 0
    assert backend.run_validate(args) == 0

    generated = project_root / "src/filterx-generated"
    assert {path.name for path in generated.iterdir()} == {
        "index.ts",
        "metadata.ts",
        "query.ts",
        "router.ts",
        "security.ts",
        "types.ts",
        "validation.ts",
    }
    app_source = (project_root / "src/app.ts").read_text(encoding="utf-8")
    assert "./filterx-generated/index.js" in app_source
    assert "app.use('/api/filterx', filterxRouter);" in app_source

    package = json.loads((project_root / "package.json").read_text(encoding="utf-8"))
    assert package["scripts"] == {"host:test": "echo host"}
    assert package["dependencies"]["helmet"] == "^8.0.0"
    assert package["dependencies"]["zod"] == "^3.24.0"
    assert package["devDependencies"]["prisma"] == "^6.0.0"

    patch_ids = sorted(path.name for path in (project_root / ".filterx/patches").iterdir() if path.is_dir())
    assert len(patch_ids) == 1
    assert rollback.run(command_args(project_root, config_path, patch_id=patch_ids[0])) == 0
    assert not generated.exists() or not any(generated.iterdir())
    assert (project_root / "package.json").read_text(encoding="utf-8") == original_package
    assert "filterxRouter" not in (project_root / "src/app.ts").read_text(encoding="utf-8")
