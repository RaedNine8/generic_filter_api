from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from filterx.core.config import default_config
from filterx.core.ir import IR_VERSION
from filterx.scanners import ScannerContext, ScannerError, scan_to_ir

PRISMA_SCHEMAS = {
    "simple": """
model Author {
  id    Int    @id @default(autoincrement())
  name  String
  email String? @unique
}
""",
    "one_to_many": """
model Author {
  id    Int    @id @default(autoincrement())
  name  String
  books Book[]
}
model Book {
  id       Int    @id @default(autoincrement())
  title    String
  authorId Int
  author   Author @relation(fields: [authorId], references: [id])
}
""",
    "many_to_many": """
model Author {
  id    Int    @id @default(autoincrement())
  name  String
  books Book[]
}
model Book {
  id      Int      @id @default(autoincrement())
  title   String
  authors Author[]
}
""",
    "relationship_cycle": """
model Author {
  id             Int   @id @default(autoincrement())
  name           String
  favoriteBookId Int?  @unique
  favoriteBook   Book? @relation(fields: [favoriteBookId], references: [id])
}
model Book {
  id            Int     @id @default(autoincrement())
  title         String
  recommendedBy Author?
}
""",
}


def _write_prisma_project(project_root: Path, schema: str) -> dict:
    schema_path = project_root / "prisma/schema.prisma"
    schema_path.parent.mkdir(parents=True)
    schema_path.write_text(schema.strip() + "\n", encoding="utf-8")
    (project_root / "package.json").write_text(
        json.dumps(
            {
                "name": "prisma-scanner-fixture",
                "dependencies": {"@prisma/client": "^6.0.0"},
                "devDependencies": {"prisma": "^6.0.0"},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    marker = project_root / "node_modules/.prisma/client/index.js"
    marker.parent.mkdir(parents=True)
    marker.write_text("// generated fixture marker\n", encoding="utf-8")
    os.utime(marker, (schema_path.stat().st_mtime + 10, schema_path.stat().st_mtime + 10))
    config = default_config()
    config["scan"]["framework"] = "prisma"
    config["backend"]["framework"] = "express-prisma"
    return config


@pytest.mark.parametrize("scenario", tuple(PRISMA_SCHEMAS))
def test_prisma_scanner_translates_schema_to_ir(tmp_path: Path, scenario: str) -> None:
    config = _write_prisma_project(tmp_path, PRISMA_SCHEMAS[scenario])

    ir = scan_to_ir(ScannerContext(project_root=tmp_path, config=config), "prisma")

    assert ir.version == IR_VERSION
    assert ir.source_framework == "prisma"
    assert [entity.name for entity in ir.entities] == sorted(entity.name for entity in ir.entities)
    if scenario == "simple":
        author = ir.entities[0]
        assert author.identity.primary_keys == ("id",)
        assert author.fields[2].nullable is False or any(field.name == "email" and field.nullable for field in author.fields)
    if scenario == "one_to_many":
        relationships = {(entity.name, item.name): item.kind.value for entity in ir.entities for item in entity.relationships}
        assert relationships[("Author", "books")] == "one-to-many"
        assert relationships[("Book", "author")] == "many-to-one"
    if scenario == "many_to_many":
        assert all(item.kind.value == "many-to-many" for entity in ir.entities for item in entity.relationships)
    if scenario == "relationship_cycle":
        assert all(entity.cycle_memberships for entity in ir.entities)


def test_prisma_scanner_rejects_missing_or_stale_client(tmp_path: Path) -> None:
    config = _write_prisma_project(tmp_path, PRISMA_SCHEMAS["simple"])
    marker = tmp_path / "node_modules/.prisma/client/index.js"
    marker.unlink()

    with pytest.raises(ScannerError) as missing:
        scan_to_ir(ScannerContext(project_root=tmp_path, config=config), "prisma")
    assert missing.value.code == "PRISMA_CLIENT_MISSING"

    marker.write_text("// stale\n", encoding="utf-8")
    schema_path = tmp_path / "prisma/schema.prisma"
    os.utime(schema_path, (marker.stat().st_mtime + 10, marker.stat().st_mtime + 10))
    with pytest.raises(ScannerError) as stale:
        scan_to_ir(ScannerContext(project_root=tmp_path, config=config), "prisma")
    assert stale.value.code == "PRISMA_CLIENT_STALE"
