from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping

import pytest

from filterx.commands import scan as scan_command
from filterx.core.config import load_effective_config
from filterx.core.ir import IR_VERSION, FilterxIR, validate_ir
from filterx.core.scanner import run_scan
from filterx.renderers import RendererTarget, renderer_registry
from filterx.scanners import ScannerContext, scan_to_ir, scanner_registry
from filterx.scanners.base import ScannerError, ScannerExecutionMode
from filterx.scanners.subprocess import SubprocessScannerPlugin
from golden_support import SCENARIOS, build_golden_project, command_args

SCHEMA_PATH = Path(__file__).parents[1] / "filterx" / "schemas" / "filterx-ir-v1.schema.json"


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_sqlalchemy_scan_produces_valid_deterministic_ir(tmp_path: Path, scenario: str) -> None:
    project_root = tmp_path / scenario
    config_path = build_golden_project(project_root, scenario)
    config = load_effective_config(project_root, config_path).raw

    first = run_scan(config, project_root).ir
    second = run_scan(config, project_root).ir

    assert isinstance(first, FilterxIR)
    assert first == second
    validate_ir(first)
    payload = first.to_dict()
    assert payload["version"] == IR_VERSION
    assert [entity["name"] for entity in payload["entities"]] == sorted(
        entity["name"] for entity in payload["entities"]
    )

    if scenario == "relationship_cycle":
        assert all(entity["cycle_memberships"] for entity in payload["entities"])
        assert all(
            relationship["cycle"]
            for entity in payload["entities"]
            for relationship in entity["relationships"]
        )
    if scenario == "soft_delete":
        assert payload["entities"][0]["soft_delete"] == {"respected": True, "field": "deleted_at"}
    if scenario == "custom_predicate":
        assert payload["security"]["row_predicates"] == ["app.security:active_rows"]


def test_published_json_schema_matches_ir_contract(tmp_path: Path) -> None:
    project_root = tmp_path / "simple_entity"
    config_path = build_golden_project(project_root, "simple_entity")
    config = load_effective_config(project_root, config_path).raw
    payload = run_scan(config, project_root).ir
    assert payload is not None
    document = payload.to_dict()
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["properties"]["version"]["const"] == IR_VERSION
    assert set(schema["required"]) == set(document)
    assert set(schema["$defs"]["entity"]["required"]) == set(document["entities"][0])
    assert set(schema["$defs"]["field"]["required"]) == set(document["entities"][0]["fields"][0])


def test_ir_artifact_emission_is_explicitly_opt_in(tmp_path: Path) -> None:
    project_root = tmp_path / "simple_entity"
    config_path = build_golden_project(project_root, "simple_entity")
    config_document = json.loads(config_path.read_text(encoding="utf-8"))
    config_document["scan"]["emit_ir"] = True
    config_path.write_text(json.dumps(config_document, indent=2) + "\n", encoding="utf-8")

    assert scan_command.run(command_args(project_root, config_path)) == 0

    ir_path = project_root / ".filterx/ir.json"
    assert ir_path.exists()
    assert json.loads(ir_path.read_text(encoding="utf-8"))["version"] == IR_VERSION


def test_scanner_and_renderer_registries_resolve_builtins_and_fail_actionably(tmp_path: Path) -> None:
    project_root = tmp_path / "simple_entity"
    config_path = build_golden_project(project_root, "simple_entity")
    config = load_effective_config(project_root, config_path).raw

    ir = scan_to_ir(ScannerContext(project_root=project_root, config=config), "sqlalchemy")

    assert ir.version == IR_VERSION
    assert scanner_registry.names() == ("jpa", "prisma", "sqlalchemy")
    assert renderer_registry.resolve(RendererTarget.BACKEND, "fastapi-sqlalchemy").version == "1.0.0"
    assert renderer_registry.resolve(RendererTarget.FRONTEND, "angular").version == "1.0.0"

    with pytest.raises(ValueError, match="Registered scanners: jpa, prisma, sqlalchemy"):
        scanner_registry.resolve("missing-scanner")
    with pytest.raises(ValueError, match="Registered backend renderers: express-prisma, fastapi-sqlalchemy"):
        renderer_registry.resolve(RendererTarget.BACKEND, "missing-backend")


class _CommandScanner(SubprocessScannerPlugin):
    name = "contract-subprocess"
    version = "1.0.0"

    def __init__(self, command: tuple[str, ...], mode: ScannerExecutionMode) -> None:
        self._command = command
        self.execution_mode = mode

    def command(self, context: ScannerContext) -> tuple[str, ...]:
        return self._command

    def decode_ir(self, payload: Mapping[str, Any]) -> FilterxIR:
        raise AssertionError("decode_ir is not reached in scanner failure tests")


def test_out_of_process_scanner_reports_missing_runtime_actionably(tmp_path: Path) -> None:
    scanner = _CommandScanner(
        ("definitely-missing-filterx-runtime", "scan"),
        ScannerExecutionMode.NEW_TOOLCHAIN,
    )

    with pytest.raises(ScannerError) as error:
        scanner.scan(ScannerContext(project_root=tmp_path, config={}))

    assert error.value.code == "SCANNER_RUNTIME_MISSING"
    assert error.value.context["execution_mode"] == "new-toolchain"
    assert "Install the required new-toolchain runtime" in str(error.value)


def test_out_of_process_scanner_reports_timeout_actionably(tmp_path: Path) -> None:
    scanner = _CommandScanner(
        (sys.executable, "-c", "import time; time.sleep(1)"),
        ScannerExecutionMode.EXISTING_TOOLCHAIN,
    )

    with pytest.raises(ScannerError) as error:
        scanner.scan(ScannerContext(project_root=tmp_path, config={}, timeout_seconds=0.01))

    assert error.value.code == "SCANNER_TIMEOUT"
    assert error.value.context["timeout_seconds"] == 0.01
