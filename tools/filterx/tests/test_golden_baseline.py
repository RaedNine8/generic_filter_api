from __future__ import annotations

import json
from pathlib import Path

import pytest

from golden_support import SCENARIOS, capture_scenario

GOLDEN_ROOT = Path(__file__).parent / "golden"


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_legacy_generation_matches_golden_outputs(tmp_path: Path, scenario: str) -> None:
    expected = json.loads((GOLDEN_ROOT / f"{scenario}.json").read_text(encoding="utf-8"))

    actual = capture_scenario(tmp_path / scenario, scenario)

    assert actual == expected


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_golden_baseline_covers_required_contracts(scenario: str) -> None:
    snapshot = json.loads((GOLDEN_ROOT / f"{scenario}.json").read_text(encoding="utf-8"))

    assert set(snapshot["stages"]) == {
        "scan",
        "backend_install",
        "frontend_install",
        "db_install",
        "reinstall",
        "rollback",
    }
    assert all(command["exit_code"] == 0 for name, command in snapshot["commands"].items() if name != "rollback")
    assert all(command["exit_code"] == 0 for command in snapshot["commands"]["rollback"])
    assert snapshot["commands"]["backend_reinstall"]["stdout"].count('"applied_ops": 0') == 1
    assert snapshot["commands"]["frontend_reinstall"]["stdout"].count('"applied_ops": 0') == 1
    assert snapshot["commands"]["db_reinstall"]["stdout"].count('"applied_ops": 0') == 1
