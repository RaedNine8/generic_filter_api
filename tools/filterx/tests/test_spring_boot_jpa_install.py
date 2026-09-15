from __future__ import annotations

import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from filterx.commands import backend, rollback
from filterx.core.config import default_config
from filterx.core.ir import (
    IR_VERSION,
    EntityIR,
    EntityIdentityIR,
    FieldIR,
    FieldType,
    FilterxIR,
    RelationshipIR,
    RelationshipKind,
)
from golden_support import command_args


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _field(
    name: str,
    kind: FieldType,
    source_type: str,
    operations: tuple[str, ...],
    *,
    nullable: bool = False,
    primary_key: bool = False,
) -> FieldIR:
    return FieldIR(
        name=name,
        type=kind,
        source_type=source_type,
        nullable=nullable,
        primary_key=primary_key,
        unique=False,
        has_default=primary_key,
        operations=operations,
    )


def _spring_ir() -> FilterxIR:
    numeric = ("eq", "ne", "gt", "gte", "lt", "lte", "in", "not_in", "between", "is_null", "is_not_null")
    text = ("eq", "ne", "like", "ilike", "starts_with", "ends_with", "in", "not_in", "is_null", "is_not_null")
    author = EntityIR(
        name="Author",
        identity=EntityIdentityIR(module="com.example.model", table="authors", primary_keys=("id",)),
        fields=(
            _field("id", FieldType.INTEGER, "java.lang.Long", numeric, primary_key=True),
            _field("name", FieldType.STRING, "java.lang.String", text),
        ),
        relationships=(
            RelationshipIR(
                name="books",
                kind=RelationshipKind.ONE_TO_MANY,
                target_entity="Book",
                target_table="books",
                join_path=("books",),
                depth=1,
                collection=True,
                back_populates="author",
                cycle=True,
            ),
        ),
        cycle_memberships=(("Author", "Book", "Author"),),
    )
    book = EntityIR(
        name="Book",
        identity=EntityIdentityIR(module="com.example.model", table="books", primary_keys=("id",)),
        fields=(
            _field("id", FieldType.INTEGER, "java.lang.Long", numeric, primary_key=True),
            _field("title", FieldType.STRING, "java.lang.String", text),
            _field("genre", FieldType.STRING, "java.lang.String", text),
            _field("price", FieldType.DECIMAL, "java.math.BigDecimal", numeric),
            _field("status", FieldType.ENUM, "com.example.model.BookStatus", text),
            _field("publishedAt", FieldType.DATETIME, "java.time.OffsetDateTime", numeric),
            _field("note", FieldType.STRING, "java.lang.String", text, nullable=True),
            _field("authorId", FieldType.INTEGER, "java.lang.Long", numeric),
        ),
        relationships=(
            RelationshipIR(
                name="author",
                kind=RelationshipKind.MANY_TO_ONE,
                target_entity="Author",
                target_table="authors",
                join_path=("author",),
                depth=1,
                collection=False,
                back_populates="books",
                cycle=True,
            ),
        ),
        cycle_memberships=(("Author", "Book", "Author"),),
    )
    return FilterxIR(
        version=IR_VERSION,
        source_framework="jpa",
        entities=(author, book),
        max_relationship_depth=1,
    )


def _write_spring_project(project_root: Path) -> tuple[Path, str]:
    project_root.mkdir()
    original_pom = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.4.7</version>
  </parent>
  <groupId>com.example</groupId>
  <artifactId>filterx-spring-fixture</artifactId>
  <version>1.0.0</version>
  <properties><java.version>21</java.version></properties>
  <dependencies>
    <dependency>
      <groupId>com.h2database</groupId>
      <artifactId>h2</artifactId>
      <scope>runtime</scope>
    </dependency>
  </dependencies>
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
"""
    _write(project_root / "pom.xml", original_pom)
    _write(
        project_root / "src/main/java/com/example/FilterxFixtureApplication.java",
        "package com.example;\n\n"
        "import org.springframework.boot.SpringApplication;\n"
        "import org.springframework.boot.autoconfigure.SpringBootApplication;\n\n"
        "@SpringBootApplication\n"
        "public class FilterxFixtureApplication {\n"
        "  public static void main(String[] args) { SpringApplication.run(FilterxFixtureApplication.class, args); }\n"
        "}\n",
    )
    _write(
        project_root / "src/main/java/com/example/model/Author.java",
        "package com.example.model;\n\n"
        "import jakarta.persistence.*;\n"
        "import java.util.ArrayList;\n"
        "import java.util.List;\n\n"
        "@Entity @Table(name = \"authors\")\n"
        "public class Author {\n"
        "  @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;\n"
        "  @Column(nullable = false) private String name;\n"
        "  @OneToMany(mappedBy = \"author\") private List<Book> books = new ArrayList<>();\n"
        "  public Long getId() { return id; }\n"
        "  public String getName() { return name; }\n"
        "  public void setName(String name) { this.name = name; }\n"
        "  public List<Book> getBooks() { return books; }\n"
        "}\n",
    )
    _write(
        project_root / "src/main/java/com/example/model/BookStatus.java",
        "package com.example.model;\n\n"
        "public enum BookStatus { DRAFT, PUBLISHED }\n",
    )
    _write(
        project_root / "src/main/java/com/example/model/Book.java",
        "package com.example.model;\n\n"
        "import jakarta.persistence.*;\n"
        "import java.math.BigDecimal;\n"
        "import java.time.OffsetDateTime;\n\n"
        "@Entity @Table(name = \"books\")\n"
        "public class Book {\n"
        "  @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;\n"
        "  @Column(nullable = false) private String title;\n"
        "  @Column(nullable = false) private String genre;\n"
        "  @Column(nullable = false, precision = 18, scale = 2) private BigDecimal price;\n"
        "  @Enumerated(EnumType.STRING) @Column(nullable = false) private BookStatus status;\n"
        "  @Column(name = \"published_at\", nullable = false) private OffsetDateTime publishedAt;\n"
        "  private String note;\n"
        "  @Column(name = \"author_id\", nullable = false) private Long authorId;\n"
        "  @ManyToOne(fetch = FetchType.LAZY) @JoinColumn(name = \"author_id\", insertable = false, updatable = false) private Author author;\n"
        "  public Long getId() { return id; }\n"
        "  public String getTitle() { return title; }\n"
        "  public String getGenre() { return genre; }\n"
        "  public BigDecimal getPrice() { return price; }\n"
        "  public BookStatus getStatus() { return status; }\n"
        "  public OffsetDateTime getPublishedAt() { return publishedAt; }\n"
        "  public String getNote() { return note; }\n"
        "  public Long getAuthorId() { return authorId; }\n"
        "  public Author getAuthor() { return author; }\n"
        "}\n",
    )
    _write(
        project_root / "src/main/java/com/example/FixtureSecurityConfiguration.java",
        "package com.example;\n\n"
        "import com.example.filterx.generated.FilterxSecurity;\n"
        "import org.springframework.context.annotation.Bean;\n"
        "import org.springframework.context.annotation.Configuration;\n\n"
        "@Configuration\n"
        "public class FixtureSecurityConfiguration {\n"
        "  @Bean FilterxSecurity.IdentityExtractor fixtureIdentity() {\n"
        "    return request -> request.getHeader(\"x-genre\");\n"
        "  }\n"
        "  @Bean FilterxSecurity.RowLevelSecurity fixtureRows() {\n"
        "    return (principal, entity, action, request) -> {\n"
        "      if (principal == null || !\"Book\".equals(entity.path(\"name\").asText())) return null;\n"
        "      return (root, query, cb) -> cb.equal(root.get(\"genre\"), principal);\n"
        "    };\n"
        "  }\n"
        "  @Bean FilterxSecurity.FieldVisibility fixtureFields() {\n"
        "    return (principal, entity, field, action, request) -> !\"price\".equals(field);\n"
        "  }\n"
        "}\n",
    )
    _write(
        project_root / "src/main/resources/application.properties",
        "spring.datasource.url=jdbc:h2:mem:filterx;DB_CLOSE_DELAY=-1\n"
        "spring.jpa.hibernate.ddl-auto=create-drop\n"
        "spring.jpa.defer-datasource-initialization=true\n"
        "spring.sql.init.mode=always\n"
        "spring.jpa.open-in-view=false\n",
    )
    _write(
        project_root / "src/main/resources/data.sql",
        "insert into authors(id, name) values (1, 'Ada'), (2, 'Bob');\n"
        "insert into books(id, title, genre, price, status, published_at, note, author_id) values\n"
        "  (1, 'Alpha Filtering', 'Tech', 10.01, 'DRAFT', TIMESTAMP WITH TIME ZONE '2024-01-01 00:00:00+00', 'first', 1),\n"
        "  (2, 'Beta Search', 'Tech', 30.10, 'PUBLISHED', TIMESTAMP WITH TIME ZONE '2024-01-02 00:00:00+00', null, 2),\n"
        "  (3, 'Gamma Grouping', 'Business', 40.99, 'PUBLISHED', TIMESTAMP WITH TIME ZONE '2024-01-03 00:00:00+00', 'last', 2);\n",
    )
    _write(project_root / ".filterx/ir.json", json.dumps(_spring_ir().to_dict(), indent=2) + "\n")

    config = default_config()
    config["project"]["name"] = "spring_fixture"
    config["backend"]["framework"] = "spring-boot-jpa"
    config["backend"]["spring"].update(
        {
            "build_tool": "maven",
            "generated_package": "com.example.filterx.generated",
            "application_class": "com.example.FilterxFixtureApplication",
        }
    )
    config["frontend"]["enabled"] = False
    config["safety"]["dry_run_default"] = False
    config_path = project_root / "filterx.yaml"
    _write(config_path, json.dumps(config, indent=2) + "\n")
    return config_path, original_pom


def _dependency_coordinates(pom: Path) -> set[tuple[str, str]]:
    root = ET.parse(pom).getroot()
    local = lambda tag: tag.rsplit("}", 1)[-1]
    coordinates: set[tuple[str, str]] = set()
    for dependency in root.iter():
        if local(dependency.tag) != "dependency":
            continue
        values = {local(child.tag): (child.text or "").strip() for child in dependency}
        coordinates.add((values.get("groupId", ""), values.get("artifactId", "")))
    return coordinates


def test_spring_renderer_generates_sources_merges_maven_and_rolls_back(tmp_path: Path) -> None:
    project_root = tmp_path / "spring_project"
    config_path, original_pom = _write_spring_project(project_root)
    args = command_args(project_root, config_path)

    preview = command_args(project_root, config_path, dry_run=True)
    assert backend.run_install(preview) == 0
    assert not (project_root / "src/main/java/com/example/filterx/generated").exists()

    assert backend.run_install(args) == 0
    generated = project_root / "src/main/java/com/example/filterx/generated"
    assert {path.name for path in generated.glob("*.java")} == {
        "FilterxConfiguration.java",
        "FilterxController.java",
        "FilterxDtos.java",
        "FilterxErrorHandler.java",
        "FilterxMetadata.java",
        "FilterxQueryService.java",
        "FilterxExportService.java",
        "FilterxRequests.java",
        "FilterxSecurity.java",
        "FilterxSpecifications.java",
    }
    coordinates = _dependency_coordinates(project_root / "pom.xml")
    assert ("com.h2database", "h2") in coordinates
    assert ("org.springframework.boot", "spring-boot-starter-data-jpa") in coordinates
    assert ("org.springdoc", "springdoc-openapi-starter-webmvc-ui") in coordinates
    assert ("io.github.resilience4j", "resilience4j-spring-boot3") in coordinates
    assert ("org.apache.poi", "poi-ooxml") in coordinates

    patches = [path.name for path in (project_root / ".filterx/patches").iterdir() if path.is_dir()]
    assert len(patches) == 1
    assert rollback.run(command_args(project_root, config_path, patch_id=patches[0])) == 0
    assert not generated.exists() or not any(generated.iterdir())
    assert (project_root / "pom.xml").read_text(encoding="utf-8") == original_pom


def test_spring_validate_runs_host_compile_and_reports_failures(tmp_path: Path, monkeypatch, capsys) -> None:
    project_root = tmp_path / "spring_validate"
    config_path, _ = _write_spring_project(project_root)
    args = command_args(project_root, config_path)
    assert backend.run_install(args) == 0
    capsys.readouterr()

    commands: list[tuple[str, ...]] = []

    def successful_run(command, **kwargs):
        commands.append(tuple(command))
        return subprocess.CompletedProcess(command, 0, stdout="BUILD SUCCESS", stderr="")

    monkeypatch.setattr("filterx.renderers.spring_boot_jpa.subprocess.run", successful_run)
    assert backend.run_validate(args) == 0
    assert commands == [("mvn", "-DskipTests", "compile")]
    capsys.readouterr()

    def failed_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="Example.java:12: cannot find symbol")

    monkeypatch.setattr("filterx.renderers.spring_boot_jpa.subprocess.run", failed_run)
    assert backend.run_validate(args) == 4
    payload = json.loads(capsys.readouterr().out)
    assert payload["errors"][0]["code"] == "SPRING_COMPILE_FAILED"
    assert "cannot find symbol" in payload["errors"][0]["stderr"]
