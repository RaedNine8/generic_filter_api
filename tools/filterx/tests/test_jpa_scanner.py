from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from filterx.core.config import default_config
from filterx.core.ir import IR_VERSION
from filterx.scanners import ScannerContext, ScannerError
from filterx.scanners.jpa import JPABuildTool, JPAScannerPlugin


def _context(project_root: Path) -> ScannerContext:
    config = default_config()
    config["scan"]["framework"] = "jpa"
    return ScannerContext(project_root=project_root, config=config)


def _completed(command: object, returncode: int = 0, stdout: str = "", stderr: str = ""):
    return subprocess.CompletedProcess(command, returncode, stdout=stdout, stderr=stderr)


def _minimal_ir() -> dict:
    return {
        "version": IR_VERSION,
        "source_framework": "jpa",
        "entities": [
            {
                "name": "Author",
                "identity": {"module": "example", "table": "authors", "primary_keys": ["id"]},
                "fields": [
                    {
                        "name": "id",
                        "type": "integer",
                        "source_type": "java.lang.Long",
                        "nullable": False,
                        "primary_key": True,
                        "unique": False,
                        "has_default": True,
                        "foreign_keys": [],
                        "operations": ["eq", "neq"],
                        "enum_values": [],
                        "visibility": "public",
                        "permission": None,
                    }
                ],
                "relationships": [],
                "cycle_memberships": [],
                "soft_delete": {"respected": False, "field": None},
            }
        ],
        "routes": [],
        "security": {
            "identity": None,
            "row_predicates": [],
            "entity_row_predicates": [],
            "field_visibility": None,
        },
        "max_relationship_depth": 0,
    }


def test_jpa_defaults_are_additive_and_legacy_frameworks_remain_selected() -> None:
    config = default_config()

    assert config["scan"]["framework"] == "sqlalchemy"
    assert config["backend"]["framework"] == "fastapi-sqlalchemy"
    assert config["scan"]["jpa"] == {
        "module_path": ".",
        "build_tool": None,
        "java_command": "java",
        "maven_command": None,
        "gradle_command": None,
        "helper_source": None,
        "classes_dir": None,
        "classpath": None,
        "compile_timeout_seconds": 120,
        "helper_timeout_seconds": 60,
        "maven_args": [],
        "gradle_args": [],
    }
    assert config["backend"]["spring"]["module_path"] == "."
    assert config["backend"]["spring"]["use_records"] is True


def test_jpa_build_tool_prefers_wrappers_and_supports_module_path(tmp_path: Path) -> None:
    module = tmp_path / "services/catalog"
    module.mkdir(parents=True)
    (module / "pom.xml").write_text("<project />\n", encoding="utf-8")
    wrapper = tmp_path / "mvnw.cmd"
    wrapper.write_text("@echo off\n", encoding="utf-8")
    context = _context(tmp_path)
    context.config["scan"]["jpa"]["module_path"] = "services/catalog"
    scanner = JPAScannerPlugin()

    tool = scanner.resolve_build_tool(context)
    compile_command, classpath_command = scanner.build_commands(
        context, tool, module / ".filterx/classpath.txt"
    )

    assert tool == JPABuildTool("maven", str(wrapper), True)
    assert compile_command[-2:] == ("-DskipTests", "compile")
    assert "dependency:build-classpath" in classpath_command
    assert any(item.startswith("-Dmdep.outputFile=") for item in classpath_command)


def test_jpa_gradle_kotlin_wrapper_command_does_not_require_installed_gradle(tmp_path: Path) -> None:
    (tmp_path / "build.gradle.kts").write_text("plugins { java }\n", encoding="utf-8")
    wrapper = tmp_path / "gradlew.bat"
    wrapper.write_text("@echo off\n", encoding="utf-8")
    context = _context(tmp_path)
    scanner = JPAScannerPlugin()

    tool = scanner.resolve_build_tool(context)
    compile_command, classpath_command = scanner.build_commands(
        context, tool, tmp_path / ".filterx/classpath.txt"
    )

    assert tool == JPABuildTool("gradle", str(wrapper), True)
    assert compile_command[-2:] == ("classes", "--no-daemon")
    assert classpath_command == ()


def test_jpa_scanner_reports_missing_java_actionably(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    context = _context(tmp_path)
    context.config["scan"]["jpa"]["classes_dir"] = "classes"
    (tmp_path / "classes").mkdir()

    def missing(*args, **kwargs):
        raise FileNotFoundError("missing")

    monkeypatch.setattr(subprocess, "run", missing)
    with pytest.raises(ScannerError) as error:
        JPAScannerPlugin().scan(context)

    assert error.value.code == "JPA_JAVA_MISSING"
    assert "Install JDK 17+" in str(error.value)


def test_jpa_scanner_rejects_helper_package_version_mismatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    context = _context(tmp_path)
    context.config["scan"]["jpa"]["classes_dir"] = "classes"
    (tmp_path / "classes").mkdir()
    calls = 0

    def run(command, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return _completed(command, stderr='openjdk version "17.0.12"')
        return _completed(
            command,
            stdout=json.dumps({"helper_version": "99.0.0", "protocol_version": IR_VERSION}),
        )

    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(ScannerError) as error:
        JPAScannerPlugin().scan(context)

    assert error.value.code == "JPA_HELPER_VERSION_MISMATCH"
    assert error.value.context["helper_version"] == "99.0.0"
    assert "Reinstall FilterX" in str(error.value)


def test_jpa_scanner_classifies_preexisting_compile_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "pom.xml").write_text("<project />\n", encoding="utf-8")
    context = _context(tmp_path)
    calls = 0

    def run(command, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return _completed(command, stderr='openjdk version "21.0.4"')
        if calls == 2:
            return _completed(
                command,
                stdout=json.dumps({"helper_version": "0.1.0", "protocol_version": IR_VERSION}),
            )
        return _completed(command, returncode=1, stderr="Compilation failure: existing host error")

    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(ScannerError) as error:
        JPAScannerPlugin().scan(context)

    assert error.value.code == "JPA_COMPILATION_FAILED"
    assert "pre-existing compile errors" in str(error.value)
    assert "existing host error" in error.value.context["stderr"]


def test_jpa_scanner_classifies_compile_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "pom.xml").write_text("<project />\n", encoding="utf-8")
    context = _context(tmp_path)
    calls = 0

    def run(command, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return _completed(command, stderr='openjdk version "21.0.4"')
        if calls == 2:
            return _completed(
                command,
                stdout=json.dumps({"helper_version": "0.1.0", "protocol_version": IR_VERSION}),
            )
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(ScannerError) as error:
        JPAScannerPlugin().scan(context)

    assert error.value.code == "JPA_COMPILE_TIMEOUT"
    assert "Maven compilation" in str(error.value)
    assert error.value.context["timeout_seconds"] == 120


def test_jpa_scanner_decodes_ir_and_applies_security_contract(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    classes = tmp_path / "classes"
    classes.mkdir()
    context = _context(tmp_path)
    context.config["scan"]["jpa"]["classes_dir"] = "classes"
    context.config["scan"]["jpa"]["classpath"] = str(classes)
    context.config["backend"]["global_predicate_hooks"] = ["security.rules:active_rows"]
    calls = 0

    def run(command, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return _completed(command, stderr='openjdk version "17.0.12"')
        if calls == 2:
            return _completed(
                command,
                stdout=json.dumps({"helper_version": "0.1.0", "protocol_version": IR_VERSION}),
            )
        return _completed(command, stdout=json.dumps(_minimal_ir()))

    monkeypatch.setattr(subprocess, "run", run)
    ir = JPAScannerPlugin().scan(context)

    assert ir.version == IR_VERSION
    assert ir.source_framework == "jpa"
    assert ir.entities[0].identity.primary_keys == ("id",)
    assert ir.security.row_predicates == ("security.rules:active_rows",)


def test_jpa_decode_rejects_wrong_helper_ir_version() -> None:
    payload = _minimal_ir()
    payload["version"] = "filterx-ir/v999"

    with pytest.raises(ValueError, match="unsupported version"):
        JPAScannerPlugin().decode_ir(payload)


@pytest.mark.skipif(
    shutil.which("java") is None or shutil.which("javac") is None,
    reason="JDK is not installed",
)
def test_jpa_helper_reflects_relationships_cycles_and_field_metadata_without_maven_or_gradle(
    tmp_path: Path,
) -> None:
    sources = tmp_path / "src"
    classes = tmp_path / "classes"
    annotations = {
        "Entity": "@Retention(RetentionPolicy.RUNTIME) @Target(ElementType.TYPE) public @interface Entity { String name() default \"\"; }",
        "Table": "@Retention(RetentionPolicy.RUNTIME) @Target(ElementType.TYPE) public @interface Table { String name() default \"\"; }",
        "Id": "@Retention(RetentionPolicy.RUNTIME) @Target({ElementType.FIELD, ElementType.METHOD}) public @interface Id {}",
        "GeneratedValue": "@Retention(RetentionPolicy.RUNTIME) @Target({ElementType.FIELD, ElementType.METHOD}) public @interface GeneratedValue {}",
        "Column": "@Retention(RetentionPolicy.RUNTIME) @Target({ElementType.FIELD, ElementType.METHOD}) public @interface Column { boolean nullable() default true; boolean unique() default false; String columnDefinition() default \"\"; }",
        "OneToMany": "@Retention(RetentionPolicy.RUNTIME) @Target({ElementType.FIELD, ElementType.METHOD}) public @interface OneToMany { String mappedBy() default \"\"; }",
        "ManyToOne": "@Retention(RetentionPolicy.RUNTIME) @Target({ElementType.FIELD, ElementType.METHOD}) public @interface ManyToOne { String mappedBy() default \"\"; }",
    }
    java_files: list[str] = []
    for name, declaration in annotations.items():
        path = sources / "jakarta/persistence" / f"{name}.java"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "package jakarta.persistence; import java.lang.annotation.*; " + declaration + "\n",
            encoding="utf-8",
        )
        java_files.append(str(path))
    author = sources / "example/Author.java"
    author.parent.mkdir(parents=True, exist_ok=True)
    author.write_text(
        "package example; import jakarta.persistence.*; import java.util.*; "
        "@Entity @Table(name=\"authors\") public class Author { "
        "@Id @GeneratedValue public Long id; @Column(nullable=false, unique=true) public String name; "
        "@OneToMany(mappedBy=\"author\") public List<Book> books; }\n",
        encoding="utf-8",
    )
    book = sources / "example/Book.java"
    book.write_text(
        "package example; import jakarta.persistence.*; "
        "@Entity @Table(name=\"books\") public class Book { "
        "@Id public Long id; @Column(nullable=false) public String title; "
        "@ManyToOne public Author author; }\n",
        encoding="utf-8",
    )
    java_files.extend((str(author), str(book)))
    classes.mkdir()
    subprocess.run(["javac", "-d", str(classes), *java_files], check=True, capture_output=True, text=True)

    context = _context(tmp_path)
    context.config["scan"]["jpa"]["classes_dir"] = "classes"
    context.config["scan"]["jpa"]["classpath"] = str(classes)
    ir = JPAScannerPlugin().scan(context)

    assert [entity.name for entity in ir.entities] == ["Author", "Book"]
    author_ir = ir.entities[0]
    assert author_ir.identity.table == "authors"
    assert author_ir.identity.primary_keys == ("id",)
    assert next(field for field in author_ir.fields if field.name == "id").has_default is True
    name = next(field for field in author_ir.fields if field.name == "name")
    assert name.nullable is False and name.unique is True
    assert author_ir.relationships[0].kind.value == "one-to-many"
    assert ir.entities[1].relationships[0].kind.value == "many-to-one"
    assert all(entity.cycle_memberships for entity in ir.entities)
    assert all(relationship.cycle for entity in ir.entities for relationship in entity.relationships)
