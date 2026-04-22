from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class Conflict:
    code: str
    message: str
    context: Dict[str, Any]


@dataclass
class ConflictReport:
    conflicts: List[Conflict]
    warnings: List[Conflict]

    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)



def check_anchor_exists(file_path: Path, anchor: str) -> ConflictReport:
    report = ConflictReport(conflicts=[], warnings=[])
    if not file_path.exists():
        report.conflicts.append(
            Conflict(
                code="ANCHOR_FILE_NOT_FOUND",
                message="Target file for anchor patch does not exist.",
                context={"path": str(file_path), "anchor": anchor},
            )
        )
        return report

    content = file_path.read_text(encoding="utf-8")
    if anchor not in content:
        report.conflicts.append(
            Conflict(
                code="ANCHOR_NOT_FOUND",
                message="Anchor not found in target file.",
                context={"path": str(file_path), "anchor": anchor},
            )
        )
    return report



def check_anchor_already_contains(file_path: Path, snippet: str) -> bool:
    if not file_path.exists():
        return False
    content = file_path.read_text(encoding="utf-8")
    return snippet in content



def check_route_path_conflicts(existing_routes: List[Dict[str, Any]], candidate_paths: List[str]) -> ConflictReport:
    def normalize(path: str) -> str:
        if not path:
            return path
        if path == "/":
            return path
        return path.rstrip("/")

    report = ConflictReport(conflicts=[], warnings=[])
    existing_path_set = {normalize(str(route.get("path", ""))) for route in existing_routes}
    for path in candidate_paths:
        normalized = normalize(path)
        if normalized in existing_path_set:
            report.conflicts.append(
                Conflict(
                    code="ROUTE_PATH_CONFLICT",
                    message="Candidate generated route path already exists.",
                    context={"path": normalized},
                )
            )
    return report
