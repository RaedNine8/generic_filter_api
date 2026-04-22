from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from filterx.core.config import load_effective_config
from filterx.core.patcher import list_patch_bundles, rollback_patch_bundle


def run(args: Any) -> int:
    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config).resolve() if args.config else None
    effective = load_effective_config(project_root, config_path)
    cfg = effective.raw

    patch_dir = project_root / cfg["output"]["patch_dir"]
    bundles = list_patch_bundles(patch_dir)

    if args.list:
        payload = {"patch_dir": str(patch_dir), "patches": bundles}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print("Available patch bundles:")
            if not bundles:
                print("- (none)")
            for patch in bundles:
                print(f"- {patch}")
        return 0

    if not bundles:
        print("No patch bundles available for rollback.")
        return 2

    patch_id = args.patch_id or bundles[-1]
    if patch_id not in bundles:
        print(f"Patch id '{patch_id}' not found.")
        return 2

    result = rollback_patch_bundle(project_root, patch_dir, patch_id)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Rollback completed for: {patch_id}")
        print(f"- Restored files: {len(result['restored'])}")
        print(f"- Removed files: {len(result['removed'])}")
    return 0
