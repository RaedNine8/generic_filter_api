from __future__ import annotations

import json
from pathlib import Path

import yaml

import manual_matrix_runner as runner
from filterx.core.config import load_effective_config


def test_scaffold_only_creates_complete_independent_matrix(
    tmp_path: Path,
    monkeypatch,
) -> None:
    matrix_root = tmp_path / "matrix"
    repo_root = Path(__file__).resolve().parents[3]

    def unexpected_subprocess(*args, **kwargs):  # pragma: no cover - failure guard
        raise AssertionError("scaffold-only mode must not invoke external commands")

    monkeypatch.setattr(runner.subprocess, "run", unexpected_subprocess)
    monkeypatch.setattr(runner.subprocess, "Popen", unexpected_subprocess)

    exit_code = runner.main(
        [
            "--repo-root",
            str(repo_root),
            "--root",
            str(matrix_root),
            "--scaffold-only",
            "--skip-dependency-install",
            "--skip-runtime",
            "--maven-command",
            "mvn-test",
        ]
    )
    assert exit_code == 0

    expected = {
        f"{backend}__{frontend}"
        for backend in runner.BACKENDS
        for frontend in runner.FRONTENDS
    }
    projects = {path.name for path in matrix_root.iterdir() if path.is_dir()}
    assert projects == expected
    assert len(projects) == 12

    command_docs: dict[str, str] = {}
    log_roots: set[Path] = set()
    for name in sorted(expected):
        backend, frontend = name.split("__", 1)
        project = matrix_root / name
        config_path = project / "filterx.yaml"
        config_text = config_path.read_text(encoding="utf-8")
        config = yaml.safe_load(config_text)

        assert config_text.lstrip().startswith("version: 1")
        assert not config_text.lstrip().startswith("{")
        assert config["project"]["name"] == name
        assert config["backend"]["framework"] == backend
        assert config["frontend"]["framework"] == frontend
        assert config["safety"]["dry_run_default"] is False
        assert load_effective_config(project, config_path).raw["scan"]["framework"] == {
            "fastapi-sqlalchemy": "sqlalchemy",
            "express-prisma": "prisma",
            "spring-boot-jpa": "jpa",
        }[backend]

        if backend == "fastapi-sqlalchemy":
            assert config["backend"]["global_predicate_hooks"] == ["app.security:row_predicate"]
            assert (project / "app/main.py").exists()
            assert (project / "seed.py").exists()
        elif backend == "express-prisma":
            assert config["backend"]["express"]["hooks_module"] == "../filterx-hooks.js"
            assert (project / "prisma/schema.prisma").exists()
            assert (project / "src/server.ts").exists()
        else:
            assert config["scan"]["jpa"]["maven_command"] == "mvn-test"
            assert config["backend"]["spring"]["maven_command"] == "mvn-test"
            assert not (project / "src/main/java/com/example/FixtureSecurityConfiguration.java").exists()
            assert (project / ".filterx/templates/FixtureSecurityConfiguration.java").exists()

        host_files = {
            "angular": ["frontend/angular.json", "frontend/src/app/app.routes.ts"],
            "react-vite": ["frontend/vite.config.ts", "frontend/src/App.tsx"],
            "nextjs": ["frontend/next.config.ts", "frontend/src/app/page.tsx"],
            "vue": ["frontend/vite.config.ts", "frontend/src/App.vue"],
        }[frontend]
        assert all((project / relative).exists() for relative in host_files)

        log_root = (project / ".filterx/cli-logs").resolve()
        assert log_root.is_dir()
        assert not any(log_root.iterdir())
        log_roots.add(log_root)

        result = json.loads((project / "result.json").read_text(encoding="utf-8"))
        assert result["name"] == name
        assert result["status"] == "scaffolded"
        assert result["commands"] == []

        commands = (project / "COMMANDS.md").read_text(encoding="utf-8")
        assert f"{backend} + {frontend}" in commands
        assert "filterx scan" in commands
        assert "filterx backend install" in commands
        assert "filterx frontend install" in commands
        command_docs[name] = commands

    assert len(log_roots) == 12
    assert len(command_docs) == 12

    summary = json.loads((matrix_root / "matrix-summary.json").read_text(encoding="utf-8"))
    assert len(summary["combinations"]) == 12
    assert summary["counts"]["scaffolded"] == 12
    assert summary["python_executable"] == runner.sys.executable
