from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from filterx.core.config import load_effective_config
from filterx.core.io import write_json
from filterx.core.scanner import run_scan


def run(args: Any) -> int:
    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config).resolve() if args.config else None

    effective = load_effective_config(project_root, config_path)
    cfg = effective.raw

    if args.entities:
        cfg["backend"]["entities"] = [e.strip() for e in args.entities.split(",") if e.strip()]
    if args.exclude_entities:
        cfg["backend"]["exclude_entities"] = [
            e.strip() for e in args.exclude_entities.split(",") if e.strip()
        ]
    if args.max_depth is not None:
        cfg["scan"]["max_relationship_depth"] = int(args.max_depth)

    dry_run = args.dry_run
    if dry_run is None:
        dry_run = bool(cfg["safety"].get("dry_run_default", True))

    result = run_scan(cfg, project_root)

    scan_path = project_root / cfg["output"]["scan_file"]
    diagnostics_path = project_root / cfg["output"]["diagnostics_file"]
    plan_path = project_root / cfg["output"]["plan_file"]

    if not dry_run and not args.check:
        write_json(scan_path, result.scan)
        write_json(diagnostics_path, result.diagnostics)
        write_json(plan_path, result.plan)

    payload = {
        "dry_run": dry_run or bool(args.check),
        "wrote_files": not (dry_run or args.check),
        "scan_file": str(scan_path),
        "diagnostics_file": str(diagnostics_path),
        "plan_file": str(plan_path),
        "diagnostics": result.diagnostics,
        "entity_count": result.scan["graph_stats"]["entity_count"],
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("FilterX scan completed.")
        print(f"- Entity count: {payload['entity_count']}")
        print(f"- Dry run: {payload['dry_run']}")
        print(f"- Wrote files: {payload['wrote_files']}")
        print(f"- Scan file: {payload['scan_file']}")
        print(f"- Diagnostics file: {payload['diagnostics_file']}")
        print(f"- Plan file: {payload['plan_file']}")

    errors = result.diagnostics.get("errors", [])
    warnings = result.diagnostics.get("warnings", [])

    if errors:
        return 2
    if args.fail_on_warning and warnings:
        return 3
    return 0
