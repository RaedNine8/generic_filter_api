from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from filterx.commands import validate
from filterx.core.config import default_config


@pytest.mark.parametrize(
    ("backend", "frontend", "backend_file", "frontend_files"),
    [
        (
            "express-prisma",
            "nextjs",
            "src/filterx-generated/router.ts",
            ["src/filterx-generated/FilterxApp.tsx", "src/app/filterx/page.tsx"],
        ),
        (
            "spring-boot-jpa",
            "vue",
            "src/main/java/com/example/filterx/generated/FilterxController.java",
            ["src/filterx-generated/FilterxApp.vue", "src/App.vue"],
        ),
    ],
)
def test_cross_layer_validate_uses_selected_framework_artifacts(
    tmp_path: Path,
    backend: str,
    frontend: str,
    backend_file: str,
    frontend_files: list[str],
) -> None:
    cfg = default_config()
    cfg["backend"].update({"framework": backend, "enabled": True})
    cfg["frontend"].update({"framework": frontend, "enabled": True, "workspace_root": "frontend"})
    cfg["database"]["enabled"] = False
    if backend == "express-prisma":
        cfg["backend"]["express"].update(
            {"generated_root": "src/filterx-generated", "app_file": "src/app.ts"}
        )
        (tmp_path / "src/app.ts").parent.mkdir(parents=True)
        (tmp_path / "src/app.ts").write_text("export {};\n", encoding="utf-8")
    else:
        cfg["backend"]["spring"].update(
            {
                "module_path": ".",
                "source_root": "src/main/java",
                "generated_package": "com.example.filterx.generated",
            }
        )
    target = cfg["frontend"][frontend.replace("-", "_")]
    target.update({"workspace_root": "frontend", "generated_root": "src/filterx-generated"})
    if frontend == "vue":
        target.update({"host_file": "src/App.vue"})

    for relative in (".filterx/scan.json", ".filterx/diagnostics.json", ".filterx/plan.json", backend_file):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
    for relative in frontend_files:
        path = tmp_path / "frontend" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("generated\n", encoding="utf-8")

    config_path = tmp_path / "filterx.yaml"
    config_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    args = SimpleNamespace(
        project_root=str(tmp_path),
        config=str(config_path),
        json=True,
        fail_on_warning=False,
    )

    assert validate.run(args) == 0
