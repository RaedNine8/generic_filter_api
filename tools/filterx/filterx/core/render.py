from __future__ import annotations

import json
from typing import Any, Dict, List



def print_result(title: str, lines: List[str]) -> None:
    print(title)
    for line in lines:
        print(f"- {line}")



def print_json(data: Dict[str, Any]) -> None:
    print(json.dumps(data, indent=2))
