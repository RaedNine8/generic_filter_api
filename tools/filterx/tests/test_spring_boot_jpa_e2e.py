from __future__ import annotations

import csv
import io
import json
import os
import shutil
import socket
import subprocess
import threading
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import pytest

from filterx.commands import backend
from golden_support import command_args
from test_spring_boot_jpa_install import _write_spring_project

pytestmark = pytest.mark.skipif(
    os.environ.get("FILTERX_RUN_JAVA_E2E") != "1",
    reason="set FILTERX_RUN_JAVA_E2E=1 and optionally FILTERX_MAVEN_COMMAND to run the real Spring suite",
)


def _maven() -> str:
    configured = os.environ.get("FILTERX_MAVEN_COMMAND")
    command = configured or shutil.which("mvn")
    if not command:
        pytest.skip("Maven is unavailable; set FILTERX_MAVEN_COMMAND or install Maven")
    return command


def _run(command: list[str], cwd: Path) -> None:
    subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )


def _port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _request(
    port: int,
    path: str,
    *,
    method: str = "GET",
    body: object | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, object]:
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/filterx{path}",
        method=method,
        data=payload,
        headers={"content-type": "application/json", **(headers or {})},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))


def _titles(payload: object) -> list[str]:
    assert isinstance(payload, dict)
    return [str(row["title"]) for row in payload["data"]]


def _raw_request(port: int, path: str, body: object, headers: dict[str, str] | None = None) -> tuple[int, bytes]:
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/filterx{path}",
        method="POST",
        data=json.dumps(body).encode("utf-8"),
        headers={"content-type": "application/json", **(headers or {})},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.status, response.read()


def _xlsx_xml(payload: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(payload)) as workbook:
        return "".join(workbook.read(name).decode("utf-8", errors="replace") for name in workbook.namelist() if name.endswith(".xml"))


def test_generated_spring_project_compiles_and_serves_full_filter_contract(tmp_path: Path) -> None:
    project_root = tmp_path / "spring_e2e"
    config_path, _ = _write_spring_project(project_root)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["backend"]["spring"].update(
        {
            "maven_command": _maven(),
            "rate_limit_per_minute": 32,
            "max_query_cost": 20,
        }
    )
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    args = command_args(project_root, config_path)

    assert backend.run_install(args) == 0
    assert backend.run_validate(args) == 0
    _run([_maven(), "-q", "-DskipTests", "package"], project_root)
    jars = [path for path in (project_root / "target").glob("*.jar") if not path.name.endswith(".original")]
    assert len(jars) == 1

    port = _port()
    process = subprocess.Popen(
        ["java", "-jar", str(jars[0]), f"--server.port={port}"],
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        assert process.stdout is not None
        for _ in range(250):
            line = process.stdout.readline()
            if "Started FilterxFixtureApplication" in line:
                break
            assert process.poll() is None, line
        else:
            raise AssertionError("Spring fixture did not report successful startup")
        threading.Thread(target=lambda: list(process.stdout), daemon=True).start()

        status, unrestricted = _request(port, "/books?size=10&sort_by=id")
        assert status == 200
        assert _titles(unrestricted) == ["Alpha Filtering", "Beta Search", "Gamma Grouping"]
        assert all("price" not in row for row in unrestricted["data"])

        status, secured = _request(port, "/books?size=10&sort_by=id", headers={"x-genre": "Tech"})
        assert status == 200
        assert _titles(secured) == ["Alpha Filtering", "Beta Search"]

        status, metadata = _request(port, "/books/metadata", headers={"x-genre": "Tech"})
        assert status == 200
        assert "price" not in {field["name"] for field in metadata["fields"]}

        status, secured_filter = _request(
            port,
            "/books/filter?size=10&sort_by=id",
            method="POST",
            headers={"x-genre": "Tech"},
            body={"filter_tree": {"node_type": "condition", "field": "price", "operation": "gt", "value": 15}},
        )
        assert status == 200
        assert _titles(secured_filter) == ["Beta Search"]

        status, secured_group = _request(port, "/books/group-by/genre", headers={"x-genre": "Tech"})
        assert status == 200
        assert secured_group == [{"key": "Tech", "count": 2}]

        # These are the same abstract cases asserted against FastAPI and Express in the Step 2 parity suite.
        operator_cases = [
            ({"field": "title", "operation": "eq", "value": "Alpha Filtering"}, ["Alpha Filtering"]),
            ({"field": "title", "operation": "ne", "value": "Alpha Filtering"}, ["Beta Search", "Gamma Grouping"]),
            ({"field": "price", "operation": "gt", "value": 20}, ["Beta Search", "Gamma Grouping"]),
            ({"field": "price", "operation": "gte", "value": 30}, ["Beta Search", "Gamma Grouping"]),
            ({"field": "price", "operation": "lt", "value": 30}, ["Alpha Filtering"]),
            ({"field": "price", "operation": "lte", "value": 30}, ["Alpha Filtering"]),
            ({"field": "title", "operation": "like", "value": "Search"}, ["Beta Search"]),
            ({"field": "title", "operation": "ilike", "value": "alpha"}, ["Alpha Filtering"]),
            ({"field": "title", "operation": "starts_with", "value": "Gamma"}, ["Gamma Grouping"]),
            ({"field": "title", "operation": "ends_with", "value": "Filtering"}, ["Alpha Filtering"]),
            ({"field": "title", "operation": "in", "value": ["Alpha Filtering", "Gamma Grouping"]}, ["Alpha Filtering", "Gamma Grouping"]),
            ({"field": "title", "operation": "not_in", "value": ["Alpha Filtering", "Gamma Grouping"]}, ["Beta Search"]),
            ({"field": "price", "operation": "between", "value": [20, 35]}, ["Beta Search"]),
            ({"field": "note", "operation": "is_null"}, ["Beta Search"]),
            ({"field": "note", "operation": "is_not_null"}, ["Alpha Filtering", "Gamma Grouping"]),
            ({"field": "author.name", "operation": "eq", "value": "Bob"}, ["Beta Search", "Gamma Grouping"]),
            ({"field": "price", "operation": "eq", "value": "30.10"}, ["Beta Search"]),
            ({"field": "status", "operation": "eq", "value": "PUBLISHED"}, ["Beta Search", "Gamma Grouping"]),
            ({"field": "publishedAt", "operation": "gte", "value": "2024-01-02T01:00:00+01:00"}, ["Beta Search", "Gamma Grouping"]),
        ]
        for condition, expected in operator_cases:
            status, payload = _request(
                port,
                "/books/filter?size=100&sort_by=id&order=asc",
                method="POST",
                body={"filter_tree": {"node_type": "condition", **condition}},
            )
            assert status == 200, (condition, payload)
            assert _titles(payload) == expected

        for query, expected in (
            ("size=100&sort_by=price&order=desc", ["Gamma Grouping", "Beta Search", "Alpha Filtering"]),
            ("page=2&size=1&sort_by=price&order=asc", ["Beta Search"]),
            ("size=100&search=Search&sort_by=id&order=asc", ["Beta Search"]),
        ):
            status, payload = _request(port, f"/books?{query}")
            assert status == 200
            assert _titles(payload) == expected

        status, groups = _request(port, "/books/group-by/genre")
        assert status == 200
        assert {row["key"]: row["count"] for row in groups} == {"Tech": 2, "Business": 1}

        export_body = {"filter_tree": {"node_type": "condition", "field": "price", "operation": "gte", "value": "10.00"}}
        for export_format in ("json", "csv", "xlsx"):
            status, exported = _raw_request(
                port,
                f"/books/export?format={export_format}&sort_by=title&order=asc",
                export_body,
                {"x-genre": "Tech"},
            )
            assert status == 200
            if export_format == "json":
                rows = json.loads(exported.decode("utf-8"))
                assert [row["title"] for row in rows] == ["Alpha Filtering", "Beta Search"]
                assert all("price" not in row for row in rows)
            elif export_format == "csv":
                rows = list(csv.DictReader(io.StringIO(exported.decode("utf-8-sig"))))
                assert [row["title"] for row in rows] == ["Alpha Filtering", "Beta Search"]
                assert "price" not in rows[0]
            else:
                xml = _xlsx_xml(exported)
                assert "Alpha Filtering" in xml and "Beta Search" in xml
                assert ">price<" not in xml

        status = 200
        limited: object = {}
        for _ in range(5):
            status, limited = _request(port, "/metadata")
            if status == 429:
                break
        assert status == 429
        assert limited["error"]["code"] == "RATE_LIMITED"
    finally:
        process.terminate()
        process.wait(timeout=20)
