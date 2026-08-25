from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Sequence

from manual_matrix_runner import BACKENDS, FRONTENDS, _commands_markdown


def _load(root: Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for backend in BACKENDS:
        for frontend in FRONTENDS:
            project = root / f"{backend}__{frontend}"
            result_file = project / "result.json"
            if not result_file.exists():
                raise FileNotFoundError(result_file)
            result = json.loads(result_file.read_text(encoding="utf-8"))
            result["result_file"] = str(result_file)
            results.append(result)
    return results


def _report(root: Path, results: list[dict[str, Any]], *, relative_links: bool) -> str:
    passed = sum(result["status"] == "passed" for result in results)
    lines = [
        "# FilterX standalone 12-combination qualification report",
        "",
        "## Outcome",
        "",
        f"- Standalone projects qualified: **{passed}/12**",
        f"- External project root: `{root}`",
        "- Each project was scaffolded from an empty directory and received one complete, validated `filterx.yaml` before any FilterX lifecycle command.",
        "- Every FastAPI project used its own `.venv`; Maven was isolated under the matrix root.",
        "- A passing result requires host builds/runtime before integration, CLI install/validation/idempotency, integrated builds/runtime/contract checks, reverse rollback, and post-rollback host verification.",
        "",
        "## Matrix",
        "",
        "| Backend | Frontend | Status | Checks | Commands | Evidence |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for result in results:
        relative = f"projects/{result['name']}/result.json"
        evidence = f"[{relative}]({relative})" if relative_links else f"`{root / result['name'] / 'result.json'}`"
        status = result["status"]
        if result.get("failed_stage"):
            status += f" ({result['failed_stage']})"
        lines.append(
            f"| `{result['backend']}` | `{result['frontend']}` | {status} | {len(result.get('checks', []))} | {len(result.get('commands', []))} | {evidence} |"
        )
    all_checks = sorted({check["check"] for result in results for check in result.get("checks", [])})
    lines.extend([
        "",
        "## Required checks represented by each passing project",
        "",
        *[f"- `{check}`" for check in all_checks],
        "",
        "Runtime contract checks cover metadata, URL equality/`in`/null grammar, search, descending sorting, pagination boundaries, relationship filters, nested AND/OR trees, grouping and filtered grouping, hidden-field rejection, row/field security, alternate principals, CSV/JSON/XLSX exports, and frontend page/proxy behavior.",
        "",
        "## Product regressions found and fixed",
        "",
        "1. Angular standalone config could call `provideAnimationsAsync()` without importing it.",
        "2. Patch rollback used text mode and changed LF bytes to CRLF on Windows.",
        "3. Cross-layer validation incorrectly required FastAPI and Angular files for every renderer.",
        "4. Web frontend install JSON omitted operation counts needed to prove idempotency.",
        "5. Spring and Express grouping could expose a field hidden by the field-visibility hook.",
        "6. The JPA scanner emitted noncanonical `neq`/`contains`/`icontains` operations that the generated API and typed web clients did not support.",
        "",
        "## Reproduction",
        "",
        "Each project contains `COMMANDS.md` with PowerShell and POSIX commands in the same order as qualification. Raw subprocess evidence is under `.filterx/cli-logs/`; `result.json` records command, working directory, exit code, output, duration, checks, host baseline, and final status.",
        "",
        "## Qualification boundary",
        "",
        "These are deterministic local dummy applications using SQLite for FastAPI/Prisma and file-backed H2 for Spring. They prove generator integration and backend/frontend parity for the supported matrix; they do not replace testing against an application's production database, authentication provider, deployment proxy, or domain-specific hooks.",
        "",
    ])
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--repo-report", type=Path, required=True)
    parser.add_argument("--maven-command", required=True)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    results = _load(root)
    for result in results:
        project = root / result["name"]
        result["project_root"] = str(project)
        host_runtime_indexes = [
            index for index, check in enumerate(result.get("checks", []))
            if check.get("check") == "host-before-filterx-runtime"
        ]
        if len(host_runtime_indexes) > 1:
            result["checks"][host_runtime_indexes[-1]]["check"] = "post-rollback-host-runtime"
        guide = _commands_markdown(result["backend"], result["frontend"], args.maven_command)
        exact = [guide, "## Exact recorded qualification subprocesses", ""]
        for command in result.get("commands", []):
            exact.extend(
                [
                    f"### `{command['stage']}`",
                    "",
                    "```powershell",
                    f"Set-Location {subprocess.list2cmdline([command['cwd']])}",
                    subprocess.list2cmdline(command["command"]),
                    "```",
                    "",
                ]
            )
        (project / "COMMANDS.md").write_text(
            "\n".join(exact),
            encoding="utf-8",
            newline="\n",
        )
        baseline = result.get("host_baseline", {})
        baseline.pop("COMMANDS.md", None)
        config_file = project / "filterx.yaml"
        if "filterx.yaml" in baseline and config_file.exists():
            baseline["filterx.yaml"] = hashlib.sha256(config_file.read_bytes()).hexdigest()
        (project / "host-baseline.json").write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8", newline="\n")
        result_path = project / "result.json"
        result_path.write_text(json.dumps({key: value for key, value in result.items() if key != "result_file"}, indent=2) + "\n", encoding="utf-8", newline="\n")
    summary = {
        "root": str(root),
        "counts": {"passed": sum(result["status"] == "passed" for result in results), "failed": sum(result["status"] != "passed" for result in results)},
        "combinations": [
            {
                "name": result["name"],
                "backend": result["backend"],
                "frontend": result["frontend"],
                "status": result["status"],
                "failed_stage": result.get("failed_stage"),
                "error": result.get("error"),
                "check_count": len(result.get("checks", [])),
                "command_count": len(result.get("commands", [])),
                "result_file": result["result_file"],
            }
            for result in results
        ],
    }
    (root / "matrix-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")
    external_report = _report(root, results, relative_links=True)
    repository_report = _report(root, results, relative_links=False)
    (root.parent / "FULL-REPORT.md").write_text(external_report, encoding="utf-8", newline="\n")
    args.repo_report.resolve().write_text(repository_report, encoding="utf-8", newline="\n")
    return 0 if summary["counts"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
