from __future__ import annotations

from pathlib import Path

from filterx.core.manifest import load_manifest
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
