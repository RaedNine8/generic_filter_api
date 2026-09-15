from __future__ import annotations

import importlib
import csv
import io
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from filterx.commands import backend, scan
from golden_support import command_args
from test_express_prisma_install import _write_express_project
from test_backend_install import _args as fastapi_args
from test_backend_install import _purge_app_modules, _write_file, _write_runtime_project

pytestmark = pytest.mark.skipif(
    os.environ.get("FILTERX_RUN_NODE_E2E") != "1",
    reason="set FILTERX_RUN_NODE_E2E=1 to run the real Node/Prisma HTTP suite",
)


def _npm() -> str:
    command = shutil.which("npm")
    if not command:
        pytest.skip("npm is not installed")
    return command


def _run(command: list[str], cwd: Path, env: dict[str, str]) -> None:
    subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )


def _request(port: int, path: str, *, method: str = "GET", body: object | None = None) -> tuple[int, object]:
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        method=method,
        data=payload,
        headers={"content-type": "application/json", "x-genre": "Tech"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))


def _raw_request(port: int, path: str, body: object) -> tuple[int, bytes]:
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        method="POST",
        data=json.dumps(body).encode("utf-8"),
        headers={"content-type": "application/json", "x-genre": "Tech"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.status, response.read()


def _xlsx_xml(payload: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(payload)) as workbook:
        return "".join(
            workbook.read(name).decode("utf-8", errors="replace")
            for name in workbook.namelist()
            if name.endswith(".xml")
        )


def test_generated_express_prisma_project_serves_queries_and_enforces_security(tmp_path: Path) -> None:
    project_root = tmp_path / "express_e2e"
    config_path, _ = _write_express_project(project_root)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["backend"]["express"].update(
        {
            "hooks_module": "../filterx-hooks.js",
            "rate_limit_per_minute": 26,
            "max_query_cost": 20,
        }
    )
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    (project_root / "src/filterx-hooks.ts").write_text(
        "export const hooks = {\n"
        "  extractIdentity: (request: any) => request.header('x-genre') ?? null,\n"
        "  rowPredicate: ({ principal, entity }: any) => entity.name === 'Book' && principal ? { genre: principal } : {},\n"
        "  fieldVisible: ({ field }: any) => field !== 'price',\n"
        "};\n",
        encoding="utf-8",
    )
    (project_root / "src/server.ts").write_text(
        "import { app } from './app.js';\n"
        "const server = app.listen(0, '127.0.0.1', () => {\n"
        "  const address = server.address();\n"
        "  if (address && typeof address === 'object') console.log(`LISTENING:${address.port}`);\n"
        "});\n",
        encoding="utf-8",
    )

    fastapi_root = tmp_path / "fastapi_e2e"
    fastapi_root.mkdir()
    fastapi_config_path = _write_runtime_project(fastapi_root)
    fastapi_config = json.loads(fastapi_config_path.read_text(encoding="utf-8"))
    fastapi_config["backend"].update(
        {
            "auth_dependency_import": "app.security:get_principal",
            "field_visibility_hook_import": "app.security:field_visible",
            "global_predicate_hooks": ["app.security:row_predicate"],
        }
    )
    fastapi_config_path.write_text(json.dumps(fastapi_config, indent=2), encoding="utf-8")
    _write_file(
        fastapi_root / "app/security.py",
        "from fastapi import Header\n\n"
        "def get_principal(x_genre: str = Header(...)):\n"
        "    return x_genre\n\n"
        "def row_predicate(*, principal, request, entity, model, action):\n"
        "    return model.genre == principal if entity.get('model') == 'Book' else None\n\n"
        "def field_visible(*, principal, request, entity, field, action):\n"
        "    return field != 'price'\n",
    )
    assert backend.run_install(fastapi_args(fastapi_root, fastapi_config_path)) == 0

    sys.path.insert(0, str(fastapi_root))
    _purge_app_modules()
    fastapi_client: TestClient | None = None
    try:
        fastapi_database = importlib.import_module("app.database")
        importlib.import_module("app.models.author")
        importlib.import_module("app.models.book")
        fastapi_database.Base.metadata.create_all(bind=fastapi_database.engine)
        FastAuthor = importlib.import_module("app.models.author").Author
        FastBook = importlib.import_module("app.models.book").Book
        fastapi_session = fastapi_database.SessionLocal()
        fastapi_author = FastAuthor(name="Ada")
        fastapi_session.add_all(
            [
                fastapi_author,
                FastBook(title="Alpha Filtering", genre="Tech", price=10.0, note=None, author=fastapi_author),
                FastBook(title="Beta Search", genre="Tech", price=30.0, note="featured", author=fastapi_author),
                FastBook(title="Gamma Grouping", genre="Business", price=40.0, note="archived", author=fastapi_author),
            ]
        )
        fastapi_session.commit()
        fastapi_session.close()
        fastapi_client = TestClient(importlib.import_module("app.main").app)
        fastapi_client.__enter__()

        args = command_args(project_root, config_path)
        assert scan.run(args) == 0
        assert backend.run_install(args) == 0

        env = dict(os.environ)
        env["DATABASE_URL"] = "file:./filterx.db"
        npm = _npm()
        _run([npm, "install", "--ignore-scripts", "--no-audit", "--no-fund"], project_root, env)
        _run([npm, "exec", "prisma", "generate"], project_root, env)
        _run([npm, "exec", "prisma", "db", "push", "--skip-generate"], project_root, env)
        _run([npm, "exec", "tsc"], project_root, env)

        seed = project_root / "seed.mjs"
        seed.write_text(
        "import { PrismaClient } from '@prisma/client';\n"
        "const prisma = new PrismaClient();\n"
        "await prisma.book.deleteMany(); await prisma.author.deleteMany();\n"
        "await prisma.author.create({ data: { name: 'Ada', books: { create: [\n"
        "  { title: 'Alpha Filtering', genre: 'Tech', price: '10.00', note: null },\n"
        "  { title: 'Beta Search', genre: 'Tech', price: '30.00', note: 'featured' },\n"
        "  { title: 'Gamma Grouping', genre: 'Business', price: '40.00', note: 'archived' }\n"
        "] } } });\n"
        "await prisma.$disconnect();\n",
            encoding="utf-8",
        )
        _run(["node", str(seed)], project_root, env)

        process = subprocess.Popen(
        ["node", "dist/server.js"],
        cwd=project_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
        try:
            assert process.stdout is not None
            port = None
            for _ in range(30):
                line = process.stdout.readline()
                if line.startswith("LISTENING:"):
                    port = int(line.split(":", 1)[1])
                    break
            assert port is not None

            status, query = _request(port, "/api/filterx/books?size=10")
            assert status == 200
            assert query["meta"]["total_items"] == 2
            assert all("price" not in row and row["genre"] == "Tech" for row in query["data"])

            status, filtered = _request(
            port,
            "/api/filterx/books/filter?size=10",
            method="POST",
            body={"filter_tree": {"field": "price", "operation": "gt", "value": 15}},
        )
            assert status == 200
            assert [row["title"] for row in filtered["data"]] == ["Beta Search"]

            status, url_filtered = _request(port, "/api/filterx/books?price_gte=30&sort_by=title")
            assert status == 200
            assert [row["title"] for row in url_filtered["data"]] == ["Beta Search"]

            status, grouped = _request(port, "/api/filterx/books/group-by/genre")
            assert status == 200
            fast_grouped = fastapi_client.get(
                "/api/filterx/books/group-by/genre", headers={"x-genre": "Tech"}
            )
            assert fast_grouped.status_code == 200
            assert grouped == fast_grouped.json() == [{"key": "Tech", "count": 2}]

            status, filtered_group = _request(
            port,
            "/api/filterx/books/group-by/genre/filter",
            method="POST",
            body={"filters": [{"field": "price", "operation": "gt", "value": 15}]},
        )
            assert status == 200
            fast_filtered_group = fastapi_client.post(
                "/api/filterx/books/group-by/genre/filter",
                headers={"x-genre": "Tech"},
                json={"filters": [{"field": "price", "operation": "gt", "value": 15}]},
            )
            assert fast_filtered_group.status_code == 200
            assert filtered_group == fast_filtered_group.json() == [{"key": "Tech", "count": 1}]

            operator_cases = [
                ("title", "eq", "Alpha Filtering"),
                ("title", "ne", "Alpha Filtering"),
                ("price", "gt", 15),
                ("price", "gte", 30),
                ("price", "lt", 30),
                ("price", "lte", 10),
                ("title", "like", "Filtering"),
                ("title", "ilike", "alpha"),
                ("title", "starts_with", "Alpha"),
                ("title", "ends_with", "Search"),
                ("title", "in", ["Alpha Filtering", "Beta Search"]),
                ("title", "not_in", ["Alpha Filtering"]),
                ("price", "between", [10, 30]),
                ("note", "is_null", None),
                ("note", "is_not_null", None),
                ("author.name", "eq", "Ada"),
            ]
            for field, operation, value in operator_cases:
                tree = {"node_type": "condition", "field": field, "operation": operation, "value": value}
                body = {"filter_tree": tree}
                express_status, express_payload = _request(
                    port, "/api/filterx/books/filter?sort_by=title", method="POST", body=body
                )
                fastapi_response = fastapi_client.post(
                    "/api/filterx/books/filter?sort_by=title",
                    headers={"x-genre": "Tech"},
                    json=body,
                )
                assert express_status == fastapi_response.status_code == 200, (field, operation, express_payload)
                assert [row["title"] for row in express_payload["data"]] == [
                    row["title"] for row in fastapi_response.json()["data"]
                ], (field, operation)

            status, sorted_page = _request(
                port, "/api/filterx/books?sort_by=title&order=desc&page=2&size=1"
            )
            fast_sorted_page = fastapi_client.get(
                "/api/filterx/books?sort_by=title&order=desc&page=2&size=1",
                headers={"x-genre": "Tech"},
            )
            assert status == fast_sorted_page.status_code == 200
            assert [row["title"] for row in sorted_page["data"]] == [
                row["title"] for row in fast_sorted_page.json()["data"]
            ]

            status, searched = _request(port, "/api/filterx/books?search=beta")
            fast_searched = fastapi_client.get(
                "/api/filterx/books?search=beta", headers={"x-genre": "Tech"}
            )
            assert status == fast_searched.status_code == 200
            assert [row["title"] for row in searched["data"]] == [
                row["title"] for row in fast_searched.json()["data"]
            ]

            export_body = {
                "filter_tree": {
                    "node_type": "condition",
                    "field": "price",
                    "operation": "gte",
                    "value": 10,
                }
            }
            expected_titles = ["Alpha Filtering", "Beta Search"]
            for export_format in ("json", "csv", "xlsx"):
                path = f"/api/filterx/books/export?format={export_format}&sort_by=title&order=asc"
                status, exported = _raw_request(port, path, export_body)
                fast_exported = fastapi_client.post(path, headers={"x-genre": "Tech"}, json=export_body)
                assert status == fast_exported.status_code == 200
                if export_format == "json":
                    express_rows = json.loads(exported.decode("utf-8"))
                    fast_rows = fast_exported.json()
                    assert [row["title"] for row in express_rows] == [row["title"] for row in fast_rows] == expected_titles
                    assert all("price" not in row for row in express_rows + fast_rows)
                elif export_format == "csv":
                    express_rows = list(csv.DictReader(io.StringIO(exported.decode("utf-8-sig"))))
                    fast_rows = list(csv.DictReader(io.StringIO(fast_exported.content.decode("utf-8-sig"))))
                    assert [row["title"] for row in express_rows] == [row["title"] for row in fast_rows] == expected_titles
                    assert "price" not in express_rows[0] and "price" not in fast_rows[0]
                else:
                    express_xml = _xlsx_xml(exported)
                    fast_xml = _xlsx_xml(fast_exported.content)
                    assert all(title in express_xml and title in fast_xml for title in expected_titles)
                    assert ">price<" not in express_xml and ">price<" not in fast_xml

            status, limited = _request(port, "/api/filterx/metadata")
            assert status == 429
            assert limited["error"]["code"] == "RATE_LIMITED"
        finally:
            process.terminate()
            process.wait(timeout=10)
    finally:
        if fastapi_client is not None:
            fastapi_client.__exit__(None, None, None)
        _purge_app_modules()
        if str(fastapi_root) in sys.path:
            sys.path.remove(str(fastapi_root))
