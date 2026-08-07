from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from filterx.core.manifest import load_manifest, validate_manifest
from filterx.core.patcher import PatchOp, apply_patch_operations, rollback_patch_bundle


def test_apply_and_rollback_patch_bundle(tmp_path: Path):
    project_root = tmp_path
    mount_file = project_root / "app_main.py"
    mount_file.write_text("line1\n# FILTERX:ROUTER_MOUNT\nline3\n", encoding="utf-8")

    manifest_path = project_root / ".filterx" / "manifest.json"
    patch_dir = project_root / ".filterx" / "patches"

    ops = [
        PatchOp(
            kind="generated_file",
            path="generated/hello.txt",
            content="hello from filterx\n",
            owner="filterx-generated",
            description="generate file",
        ),
        PatchOp(
            kind="anchor_insert",
            path="app_main.py",
            anchor="# FILTERX:ROUTER_MOUNT",
            snippet="app.include_router(filterx_router)",
            insert_mode="after",
            description="mount router",
        ),
    ]

    result = apply_patch_operations(
        project_root=project_root,
        operations=ops,
        manifest_path=manifest_path,
        patch_dir=patch_dir,
        dry_run=False,
        check_mode=False,
        strict_conflict_mode=True,
        description="test patch",
    )

    assert result.applied_ops == 2
    assert (project_root / "generated/hello.txt").exists()
    patched_text = mount_file.read_text(encoding="utf-8")
    assert "app.include_router(filterx_router)" in patched_text

    manifest = load_manifest(manifest_path)
    assert "generated/hello.txt" in manifest.data["entries"]
    assert "app_main.py" in manifest.data["entries"]

    rollback = rollback_patch_bundle(project_root, patch_dir, result.patch_id)
    assert rollback["count"] == 2
    assert not (project_root / "generated/hello.txt").exists()
    restored_text = mount_file.read_text(encoding="utf-8")
    assert "app.include_router(filterx_router)" not in restored_text


def test_anchor_conflict_blocks_patch_when_strict(tmp_path: Path):
    project_root = tmp_path
    target = project_root / "main.py"
    target.write_text("no anchor here\n", encoding="utf-8")

    result = apply_patch_operations(
        project_root=project_root,
        operations=[
            PatchOp(
                kind="anchor_insert",
                path="main.py",
                anchor="# FILTERX:ROUTER_MOUNT",
                snippet="x = 1",
            )
        ],
        manifest_path=project_root / ".filterx" / "manifest.json",
        patch_dir=project_root / ".filterx" / "patches",
        dry_run=False,
        check_mode=False,
        strict_conflict_mode=True,
        description="strict conflict check",
    )

    assert result.has_conflicts
    assert result.applied_ops == 0
    assert "x = 1" not in target.read_text(encoding="utf-8")


def test_patch_ids_are_unique_across_consecutive_applies(tmp_path: Path):
    project_root = tmp_path
    manifest_path = project_root / ".filterx" / "manifest.json"
    patch_dir = project_root / ".filterx" / "patches"

    first = apply_patch_operations(
        project_root=project_root,
        operations=[PatchOp(kind="generated_file", path="a.txt", content="a\n")],
        manifest_path=manifest_path,
        patch_dir=patch_dir,
        dry_run=False,
        check_mode=False,
        strict_conflict_mode=True,
        description="first",
    )

    second = apply_patch_operations(
        project_root=project_root,
        operations=[PatchOp(kind="generated_file", path="b.txt", content="b\n")],
        manifest_path=manifest_path,
        patch_dir=patch_dir,
        dry_run=False,
        check_mode=False,
        strict_conflict_mode=True,
        description="second",
    )

    assert first.patch_id != second.patch_id


def test_apply_and_rollback_supports_paths_outside_project_root(tmp_path: Path):
    project_root = tmp_path / "backend"
    frontend_root = tmp_path / "frontend"
    project_root.mkdir(parents=True, exist_ok=True)
    frontend_root.mkdir(parents=True, exist_ok=True)

    manifest_path = project_root / ".filterx" / "manifest.json"
    patch_dir = project_root / ".filterx" / "patches"

    result = apply_patch_operations(
        project_root=project_root,
        operations=[
            PatchOp(
                kind="generated_file",
                path="../frontend/generated.txt",
                content="generated from backend patcher\n",
            )
        ],
        manifest_path=manifest_path,
        patch_dir=patch_dir,
        dry_run=False,
        check_mode=False,
        strict_conflict_mode=True,
        description="outside root",
    )

    assert result.applied_ops == 1
    assert (frontend_root / "generated.txt").exists()

    rollback = rollback_patch_bundle(project_root, patch_dir, result.patch_id)
    assert rollback["count"] == 1
    assert not (frontend_root / "generated.txt").exists()


def test_structured_json_merge_is_idempotent_and_rolls_back_exactly(tmp_path: Path):
    package_file = tmp_path / "package.json"
    original = '{\n    "name": "host-app",\n    "scripts": {"test": "host-test"},\n    "dependencies": {"express": "^5.0.0"}\n}\n'
    package_file.write_text(original, encoding="utf-8")
    manifest_path = tmp_path / ".filterx/manifest.json"
    patch_dir = tmp_path / ".filterx/patches"
    operation = PatchOp(
        kind="structured_merge",
        path="package.json",
        owner="host",
        structured_format="json",
        merge={
            "scripts": {"filterx:generate": "filterx generate"},
            "dependencies": {"@prisma/client": "^6.0.0"},
        },
    )

    preview = apply_patch_operations(
        project_root=tmp_path,
        operations=[operation],
        manifest_path=manifest_path,
        patch_dir=patch_dir,
        dry_run=True,
        check_mode=False,
        strict_conflict_mode=True,
        description="structured preview",
    )
    assert preview.applied_ops == 1
    assert package_file.read_text(encoding="utf-8") == original

    applied = apply_patch_operations(
        project_root=tmp_path,
        operations=[operation],
        manifest_path=manifest_path,
        patch_dir=patch_dir,
        dry_run=False,
        check_mode=False,
        strict_conflict_mode=True,
        description="structured apply",
    )
    document = json.loads(package_file.read_text(encoding="utf-8"))
    assert document["name"] == "host-app"
    assert document["scripts"] == {"test": "host-test", "filterx:generate": "filterx generate"}
    assert document["dependencies"] == {"express": "^5.0.0", "@prisma/client": "^6.0.0"}
    assert load_manifest(manifest_path).data["entries"]["package.json"]["kind"] == "structured_merge"

    repeated = apply_patch_operations(
        project_root=tmp_path,
        operations=[operation],
        manifest_path=manifest_path,
        patch_dir=patch_dir,
        dry_run=False,
        check_mode=False,
        strict_conflict_mode=True,
        description="structured repeat",
    )
    assert repeated.applied_ops == 0
    assert repeated.skipped_ops == 1

    rollback_patch_bundle(tmp_path, patch_dir, applied.patch_id)
    assert package_file.read_text(encoding="utf-8") == original


def test_maven_structured_merge_is_idempotent_and_rolls_back_exactly(tmp_path: Path):
    pom = tmp_path / "pom.xml"
    original = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>host</groupId>
  <artifactId>app</artifactId>
  <version>1.0.0</version>
  <properties><java.version>21</java.version></properties>
  <dependencies>
    <dependency><groupId>host</groupId><artifactId>unrelated</artifactId><version>9</version></dependency>
  </dependencies>
</project>
"""
    pom.write_text(original, encoding="utf-8")
    operation = PatchOp(
        kind="structured_merge",
        path="pom.xml",
        owner="host",
        structured_format="xml",
        merge={
            "properties": {"filterx.version": "1.0.0"},
            "dependencies": [
                {
                    "group_id": "org.springframework.boot",
                    "artifact_id": "spring-boot-starter-data-jpa",
                }
            ],
        },
    )

    preview = apply_patch_operations(
        project_root=tmp_path,
        operations=[operation],
        manifest_path=tmp_path / ".filterx/manifest.json",
        patch_dir=tmp_path / ".filterx/patches",
        dry_run=True,
        check_mode=False,
        strict_conflict_mode=True,
        description="maven preview",
    )
    assert preview.applied_ops == 1
    assert pom.read_text(encoding="utf-8") == original

    applied = apply_patch_operations(
        project_root=tmp_path,
        operations=[operation],
        manifest_path=tmp_path / ".filterx/manifest.json",
        patch_dir=tmp_path / ".filterx/patches",
        dry_run=False,
        check_mode=False,
        strict_conflict_mode=True,
        description="maven apply",
    )
    root = ET.fromstring(pom.read_text(encoding="utf-8"))
    namespace = {"m": "http://maven.apache.org/POM/4.0.0"}
    artifacts = [item.text for item in root.findall("m:dependencies/m:dependency/m:artifactId", namespace)]
    assert artifacts == ["unrelated", "spring-boot-starter-data-jpa"]
    assert root.findtext("m:properties/m:java.version", namespaces=namespace) == "21"
    assert root.findtext("m:properties/m:filterx.version", namespaces=namespace) == "1.0.0"
    assert load_manifest(tmp_path / ".filterx/manifest.json").data["entries"]["pom.xml"]["metadata"]["format"] == "xml"

    repeated = apply_patch_operations(
        project_root=tmp_path,
        operations=[operation],
        manifest_path=tmp_path / ".filterx/manifest.json",
        patch_dir=tmp_path / ".filterx/patches",
        dry_run=False,
        check_mode=False,
        strict_conflict_mode=True,
        description="maven repeat",
    )
    assert repeated.applied_ops == 0
    rollback_patch_bundle(tmp_path, tmp_path / ".filterx/patches", applied.patch_id)
    assert pom.read_text(encoding="utf-8") == original


def test_gradle_groovy_structured_merge_preserves_unrelated_content_and_rolls_back(tmp_path: Path):
    build = tmp_path / "build.gradle"
    original = "plugins { id 'java' }\n\nrepositories { mavenCentral() }\n\ndependencies {\n    implementation 'host:unrelated:9'\n}\n"
    build.write_text(original, encoding="utf-8")
    operation = PatchOp(
        kind="structured_merge",
        path="build.gradle",
        owner="host",
        structured_format="gradle",
        merge={"dependencies": [{"configuration": "implementation", "group": "org.example", "name": "filterx", "version": "1.0.0"}]},
    )

    applied = apply_patch_operations(
        project_root=tmp_path,
        operations=[operation],
        manifest_path=tmp_path / ".filterx/manifest.json",
        patch_dir=tmp_path / ".filterx/patches",
        dry_run=False,
        check_mode=False,
        strict_conflict_mode=True,
        description="gradle groovy",
    )
    patched = build.read_text(encoding="utf-8")
    assert "repositories { mavenCentral() }" in patched
    assert "implementation 'host:unrelated:9'" in patched
    assert 'implementation "org.example:filterx:1.0.0"' in patched
    repeated = apply_patch_operations(
        project_root=tmp_path,
        operations=[operation],
        manifest_path=tmp_path / ".filterx/manifest.json",
        patch_dir=tmp_path / ".filterx/patches",
        dry_run=False,
        check_mode=False,
        strict_conflict_mode=True,
        description="gradle groovy repeat",
    )
    assert repeated.applied_ops == 0
    rollback_patch_bundle(tmp_path, tmp_path / ".filterx/patches", applied.patch_id)
    assert build.read_text(encoding="utf-8") == original


def test_gradle_kotlin_structured_merge_creates_dependency_block_idempotently(tmp_path: Path):
    build = tmp_path / "build.gradle.kts"
    original = 'plugins { java }\n\nrepositories { mavenCentral() }\n'
    build.write_text(original, encoding="utf-8")
    operation = PatchOp(
        kind="structured_merge",
        path="build.gradle.kts",
        owner="host",
        structured_format="gradle",
        merge={"dependencies": [{"configuration": "runtimeOnly", "notation": "com.h2database:h2:2.3.232"}]},
    )
    applied = apply_patch_operations(
        project_root=tmp_path,
        operations=[operation],
        manifest_path=tmp_path / ".filterx/manifest.json",
        patch_dir=tmp_path / ".filterx/patches",
        dry_run=False,
        check_mode=False,
        strict_conflict_mode=True,
        description="gradle kotlin",
    )
    assert 'runtimeOnly("com.h2database:h2:2.3.232")' in build.read_text(encoding="utf-8")
    repeated = apply_patch_operations(
        project_root=tmp_path,
        operations=[operation],
        manifest_path=tmp_path / ".filterx/manifest.json",
        patch_dir=tmp_path / ".filterx/patches",
        dry_run=False,
        check_mode=False,
        strict_conflict_mode=True,
        description="gradle kotlin repeat",
    )
    assert repeated.applied_ops == 0
    rollback_patch_bundle(tmp_path, tmp_path / ".filterx/patches", applied.patch_id)
    assert build.read_text(encoding="utf-8") == original


def test_invalid_gradle_manifest_is_rejected_without_text_fallback(tmp_path: Path):
    build = tmp_path / "build.gradle"
    original = "dependencies { implementation 'broken:coordinate:1'\n"
    build.write_text(original, encoding="utf-8")

    result = apply_patch_operations(
        project_root=tmp_path,
        operations=[
            PatchOp(
                kind="structured_merge",
                path="build.gradle",
                structured_format="gradle",
                merge={"dependencies": [{"configuration": "implementation", "notation": "safe:addition:1"}]},
            )
        ],
        manifest_path=tmp_path / ".filterx/manifest.json",
        patch_dir=tmp_path / ".filterx/patches",
        dry_run=False,
        check_mode=False,
        strict_conflict_mode=True,
        description="invalid Gradle",
    )

    assert result.has_conflicts
    assert result.issues[0].code == "CONFLICT_STRUCTURED_DOCUMENT_INVALID"
    assert build.read_text(encoding="utf-8") == original


def test_pre_versioned_manifest_and_legacy_bundle_remain_operable(tmp_path: Path):
    manifest_path = tmp_path / ".filterx/manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps(
            {
                "created_at": "2025-01-01T00:00:00+00:00",
                "updated_at": "2025-01-01T00:00:00+00:00",
                "entries": {"generated.txt": {"kind": "generated_file", "sha256": "legacy"}},
                "patch_history": [],
            }
        ),
        encoding="utf-8",
    )
    generated = tmp_path / "generated.txt"
    generated.write_text("post-patch\n", encoding="utf-8")
    bundle = tmp_path / ".filterx/patches/legacy-patch"
    (bundle / "backup").mkdir(parents=True)
    (bundle / "backup/generated.txt").write_text("pre-patch\n", encoding="utf-8")
    (bundle / "meta.json").write_text(
        json.dumps(
            {
                "patch_id": "legacy-patch",
                "backups": [
                    {
                        "relative_path": "generated.txt",
                        "existed": True,
                        "backup_path": "backup/generated.txt",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    loaded = load_manifest(manifest_path)
    assert loaded.data["version"] == 1
    assert "generated.txt" in loaded.data["entries"]
    assert validate_manifest(loaded) == []

    result = rollback_patch_bundle(tmp_path, tmp_path / ".filterx/patches", "legacy-patch")
    assert result["restored"] == ["generated.txt"]
    assert generated.read_text(encoding="utf-8") == "pre-patch\n"
