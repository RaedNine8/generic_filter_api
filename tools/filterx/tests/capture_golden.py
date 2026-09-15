from __future__ import annotations

import json
import tempfile
from pathlib import Path

from golden_support import SCENARIOS, capture_scenario


def main() -> None:
    golden_root = Path(__file__).parent / "golden"
    golden_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="filterx-golden-") as temp_dir:
        workspace = Path(temp_dir)
        for scenario in SCENARIOS:
            snapshot = capture_scenario(workspace / scenario, scenario)
            target = golden_root / f"{scenario}.json"
            target.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(f"captured {scenario}: {target}")


if __name__ == "__main__":
    main()
