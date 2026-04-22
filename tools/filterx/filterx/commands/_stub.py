from __future__ import annotations

from typing import Any


def run_stub(args: Any, command_name: str) -> int:
    dry_run = args.dry_run
    print(f"FilterX command '{command_name}' is scaffolded but not implemented yet.")
    print(f"- Dry run: {bool(dry_run) if dry_run is not None else 'config-default'}")
    return 0
