from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from filterx.core.config import load_effective_config

from . import backend, db, frontend, scan, validate


def _as_payload(steps: list[dict[str, Any]], final_code: int) -> dict[str, Any]:
    return {
        "steps": steps,
        "exit_code": final_code,
        "ok": final_code == 0,
    }


def _ensure_scan_option_defaults(args: Any) -> None:
    if not hasattr(args, "entities"):
        args.entities = None
    if not hasattr(args, "exclude_entities"):
        args.exclude_entities = None
    if not hasattr(args, "max_depth"):
        args.max_depth = None


def _print_payload(args: Any, payload: dict[str, Any]) -> None:
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2))
        return
    print("FilterX orchestrated install completed.")
    print(f"- Exit code: {payload['exit_code']}")
    for step in payload["steps"]:
        print(f"- {step['name']}: {step['status']} (code={step['code']})")


def run(args: Any) -> int:
    _ensure_scan_option_defaults(args)

    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config).resolve() if args.config else None
    effective = load_effective_config(project_root, config_path)
    cfg = effective.raw

    steps: list[dict[str, Any]] = []

    scan_code = int(scan.run(args) or 0)
    steps.append(
        {
            "name": "scan",
            "status": "ok" if scan_code == 0 else "failed",
            "code": scan_code,
        }
    )
    if scan_code != 0:
        payload = _as_payload(steps, scan_code)
        _print_payload(args, payload)
        return scan_code

    if cfg["backend"].get("enabled", True):
        backend_code = int(backend.run_install(args) or 0)
        steps.append(
            {
                "name": "backend.install",
                "status": "ok" if backend_code == 0 else "failed",
                "code": backend_code,
            }
        )
        if backend_code != 0:
            payload = _as_payload(steps, backend_code)
            _print_payload(args, payload)
            return backend_code
    else:
        steps.append({"name": "backend.install", "status": "skipped", "code": 0})

    if cfg["frontend"].get("enabled", True):
        frontend_code = int(frontend.run_install(args) or 0)
        steps.append(
            {
                "name": "frontend.install",
                "status": "ok" if frontend_code == 0 else "failed",
                "code": frontend_code,
            }
        )
        if frontend_code != 0:
            payload = _as_payload(steps, frontend_code)
            _print_payload(args, payload)
            return frontend_code
    else:
        steps.append({"name": "frontend.install", "status": "skipped", "code": 0})

    if cfg["database"].get("enabled", False):
        db_code = int(db.run_install(args) or 0)
        steps.append(
            {
                "name": "db.install",
                "status": "ok" if db_code == 0 else "failed",
                "code": db_code,
            }
        )
        if db_code != 0:
            payload = _as_payload(steps, db_code)
            _print_payload(args, payload)
            return db_code
    else:
        steps.append({"name": "db.install", "status": "skipped", "code": 0})

    validate_code = int(validate.run(args) or 0)
    steps.append(
        {
            "name": "validate",
            "status": "ok" if validate_code == 0 else "failed",
            "code": validate_code,
        }
    )

    payload = _as_payload(steps, validate_code)
    _print_payload(args, payload)
    return validate_code
