from __future__ import annotations

"""Generate and exercise the 3 x 4 FilterX manual integration matrix.

This is intentionally a reusable manual runner rather than a pytest E2E test.  Every
combination is an independent project and records enough information to reproduce a
failure without relying on runner state.
"""

import argparse
import csv
import hashlib
import io
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import venv
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

import yaml

from filterx.core.config import default_config, load_effective_config

BACKENDS = ("fastapi-sqlalchemy", "express-prisma", "spring-boot-jpa")
FRONTENDS = ("angular", "react-vite", "nextjs", "vue")
EXPECTED_TITLES = ["Alpha Filtering", "Beta Search"]
CREATE_NEW_PROCESS_GROUP = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)


@dataclass
class CommandResult:
    stage: str
    command: list[str]
    cwd: str
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    log_file: str


@dataclass
class CombinationResult:
    name: str
    backend: str
    frontend: str
    project_root: str
    status: str = "scaffolded"
    failed_stage: str | None = None
    error: str | None = None
    commands: list[CommandResult] = field(default_factory=list)
    checks: list[dict[str, Any]] = field(default_factory=list)
    host_baseline: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Options:
    repo_root: Path
    root: Path
    maven_command: str
    only: tuple[str, ...]
    keep_existing: bool
    skip_runtime: bool
    skip_dependency_install: bool
    scaffold_only: bool


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _write_json(path: Path, value: Any) -> None:
    _write(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def _json_document(name: str, scripts: dict[str, str], dependencies: dict[str, str], dev: dict[str, str]) -> str:
    return json.dumps(
        {
            "name": name,
            "version": "1.0.0",
            "private": True,
            "type": "module",
            "scripts": scripts,
            "dependencies": dependencies,
            "devDependencies": dev,
        },
        indent=2,
    ) + "\n"


def _combination_name(backend: str, frontend: str) -> str:
    return f"{backend}__{frontend}"


def _parse_only(values: Sequence[str]) -> tuple[str, ...]:
    selected: list[str] = []
    valid = {_combination_name(backend, frontend) for backend in BACKENDS for frontend in FRONTENDS}
    for raw in values:
        value = raw.strip().replace("+", "__")
        if value not in valid:
            raise argparse.ArgumentTypeError(
                f"unknown combination {raw!r}; expected BACKEND__FRONTEND"
            )
        if value not in selected:
            selected.append(value)
    return tuple(selected)


def _config(backend: str, frontend: str, name: str, maven_command: str) -> dict[str, Any]:
    """Return the complete, valid config written before any lifecycle command."""
    cfg = default_config()
    cfg["project"].update(
        {"name": name, "root": ".", "backend_root": ".", "frontend_root": "frontend"}
    )
    cfg["backend"].update(
        {
            "enabled": True,
            "framework": backend,
            "api_prefix": "/api",
            "entities": ["Author", "Book"],
        }
    )
    cfg["frontend"].update(
        {
            "enabled": True,
            "framework": frontend,
            "workspace_root": "frontend",
        }
    )
    cfg["database"]["enabled"] = False
    cfg["safety"]["dry_run_default"] = False

    if backend == "fastapi-sqlalchemy":
        cfg["scan"]["framework"] = "sqlalchemy"
        cfg["python"].update(
            {
                "app_import": "app.main:app",
                "base_class_import": "app.database:Base",
                "models_package": "app.models",
                "session_dependency_import": "app.database:get_db",
            }
        )
        cfg["backend"].update(
            {
                "generated_package": "app/filterx_generated",
                "mount_file": "app/main.py",
                "mount_anchor": "# FILTERX:ROUTER_MOUNT",
                "auth_dependency_import": "app.security:get_principal",
                "field_visibility_hook_import": "app.security:field_visible",
                "global_predicate_hooks": ["app.security:row_predicate"],
            }
        )
    elif backend == "express-prisma":
        cfg["scan"]["framework"] = "prisma"
        cfg["scan"]["prisma"].update(
            {
                "schema": "prisma/schema.prisma",
                "package_json": "package.json",
                "client_marker": "node_modules/.prisma/client/index.js",
                "allow_stale_client": False,
            }
        )
        cfg["backend"]["express"].update(
            {
                "generated_root": "src/filterx-generated",
                "app_file": "src/app.ts",
                "app_anchor": "// FILTERX:ROUTER_MOUNT",
                # Generated modules are in src/filterx-generated and compile to the same layout.
                "hooks_module": "../filterx-hooks.js",
                "rate_limit_per_minute": 120,
            }
        )
    else:
        cfg["scan"]["framework"] = "jpa"
        cfg["scan"]["jpa"].update(
            {
                "module_path": ".",
                "build_tool": "maven",
                "maven_command": maven_command,
            }
        )
        cfg["backend"]["spring"].update(
            {
                "module_path": ".",
                "build_tool": "maven",
                "maven_command": maven_command,
                "generated_package": "com.example.filterx.generated",
                "application_class": "com.example.FilterxFixtureApplication",
                "pom_file": "pom.xml",
                "rate_limit_per_minute": 120,
            }
        )

    if frontend == "angular":
        cfg["frontend"].update(
            {
                "generated_root": "frontend/src/app/filterx-generated",
                "routes_file": "frontend/src/app/app.routes.ts",
                "routes_anchor": "// FILTERX:ROUTES",
                "app_config_file": "frontend/src/app/app.config.ts",
                "app_config_anchor": "// FILTERX:PROVIDERS",
            }
        )
    elif frontend == "react-vite":
        cfg["frontend"]["react_vite"].update(
            {
                "workspace_root": "frontend",
                "generated_root": "src/filterx-generated",
                "host_file": "src/App.tsx",
                "host_anchor": "// FILTERX:APP",
                "api_base_url": "/api/filterx",
            }
        )
    elif frontend == "nextjs":
        cfg["frontend"]["nextjs"].update(
            {
                "workspace_root": "frontend",
                "generated_root": "src/filterx-generated",
                "api_base_url": "/api/filterx",
            }
        )
    else:
        cfg["frontend"]["vue"].update(
            {
                "workspace_root": "frontend",
                "generated_root": "src/filterx-generated",
                "host_file": "src/App.vue",
                "host_anchor": "<!-- FILTERX:APP -->",
                "api_base_url": "/api/filterx",
            }
        )
    return cfg


def _scaffold_fastapi(root: Path) -> None:
    for package in ("app", "app/models"):
        _write(root / package / "__init__.py", "")
    _write(
        root / "app/database.py",
        "from sqlalchemy import create_engine\n"
        "from sqlalchemy.orm import declarative_base, sessionmaker\n\n"
        "engine = create_engine('sqlite:///./filterx.db', connect_args={'check_same_thread': False})\n"
        "SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)\n"
        "Base = declarative_base()\n\n"
        "def get_db():\n"
        "    db = SessionLocal()\n"
        "    try:\n"
        "        yield db\n"
        "    finally:\n"
        "        db.close()\n",
    )
    _write(
        root / "app/models/author.py",
        "from sqlalchemy import Column, Integer, String\n"
        "from sqlalchemy.orm import relationship\n"
        "from app.database import Base\n\n"
        "class Author(Base):\n"
        "    __tablename__ = 'authors'\n"
        "    id = Column(Integer, primary_key=True)\n"
        "    name = Column(String, nullable=False)\n"
        "    books = relationship('Book', back_populates='author')\n",
    )
    _write(
        root / "app/models/book.py",
        "from sqlalchemy import Column, Float, ForeignKey, Integer, String\n"
        "from sqlalchemy.orm import relationship\n"
        "from app.database import Base\n\n"
        "class Book(Base):\n"
        "    __tablename__ = 'books'\n"
        "    id = Column(Integer, primary_key=True)\n"
        "    title = Column(String, nullable=False)\n"
        "    genre = Column(String, nullable=False)\n"
        "    price = Column(Float, nullable=False)\n"
        "    note = Column(String, nullable=True)\n"
        "    author_id = Column(Integer, ForeignKey('authors.id'), nullable=False)\n"
        "    author = relationship('Author', back_populates='books')\n",
    )
    _write(
        root / "app/models/__init__.py",
        "from app.models.author import Author\nfrom app.models.book import Book\n\n__all__ = ['Author', 'Book']\n",
    )
    _write(
        root / "app/security.py",
        "from fastapi import Header\n\n"
        "def get_principal(x_genre: str = Header(default='Tech')):\n"
        "    return x_genre\n\n"
        "def row_predicate(*, principal, request, entity, model, action):\n"
        "    return model.genre == principal if entity.get('model') == 'Book' else None\n\n"
        "def field_visible(*, principal, request, entity, field, action):\n"
        "    return field != 'price'\n",
    )
    _write(
        root / "app/main.py",
        "from fastapi import FastAPI\nfrom app import models as _models\n\n"
        "app = FastAPI(title='FilterX matrix fixture')\n\n"
        "@app.get('/health')\n"
        "def health(): return {'ok': True}\n\n"
        "# FILTERX:ROUTER_MOUNT\n",
    )
    _write(
        root / "seed.py",
        "from app.database import Base, SessionLocal, engine\n"
        "from app.models.author import Author\n"
        "from app.models.book import Book\n\n"
        "Base.metadata.drop_all(bind=engine); Base.metadata.create_all(bind=engine)\n"
        "db = SessionLocal()\n"
        "ada, bob = Author(name='Ada'), Author(name='Bob')\n"
        "db.add_all([ada, bob]); db.flush()\n"
        "db.add_all([Book(title='Alpha Filtering', genre='Tech', price=10, note='first', author=ada), "
        "Book(title='Beta Search', genre='Tech', price=30, note=None, author=bob), "
        "Book(title='Gamma Grouping', genre='Business', price=40, note='last', author=bob)])\n"
        "db.commit(); db.close()\n",
    )


def _scaffold_express(root: Path) -> None:
    _write(
        root / "package.json",
        _json_document(
            "filterx-express-matrix",
            {"build": "tsc", "start": "node dist/server.js", "seed": "node seed.mjs"},
            {"@prisma/client": "^6.0.0", "express": "^5.0.0"},
            {"@types/express": "^5.0.0", "@types/node": "^22.0.0", "prisma": "^6.0.0", "typescript": "^5.7.0"},
        ),
    )
    _write_json(
        root / "tsconfig.json",
        {
            "compilerOptions": {
                "target": "ES2022",
                "module": "NodeNext",
                "moduleResolution": "NodeNext",
                "strict": True,
                "esModuleInterop": True,
                "outDir": "dist",
                "skipLibCheck": True,
            },
            "include": ["src/**/*.ts"],
        },
    )
    _write(
        root / "prisma/schema.prisma",
        "generator client {\n  provider = \"prisma-client-js\"\n}\n\n"
        "datasource db {\n  provider = \"sqlite\"\n  url = env(\"DATABASE_URL\")\n}\n\n"
        "model Author {\n  id Int @id @default(autoincrement())\n  name String\n  books Book[]\n}\n\n"
        "model Book {\n  id Int @id @default(autoincrement())\n  title String\n  genre String\n"
        "  price Decimal\n  note String?\n  authorId Int\n  author Author @relation(fields: [authorId], references: [id])\n}\n",
    )
    _write(
        root / "src/app.ts",
        "import express from 'express';\n\n"
        "export const app = express();\napp.use(express.json());\n\n"
        "app.get('/health', (_req, res) => res.json({ok: true}));\n"
        "// FILTERX:ROUTER_MOUNT\n",
    )
    _write(
        root / "src/server.ts",
        "import { app } from './app.js';\n"
        "const port = Number(process.env.PORT ?? 8000);\n"
        "app.listen(port, '127.0.0.1', () => console.log(`LISTENING:${port}`));\n",
    )
    _write(
        root / "src/filterx-hooks.ts",
        "export const hooks = {\n"
        "  extractIdentity: (request: any) => request.header('x-genre') ?? 'Tech',\n"
        "  rowPredicate: ({principal, entity}: any) => entity.name === 'Book' ? {genre: principal} : {},\n"
        "  fieldVisible: ({field}: any) => field !== 'price',\n"
        "};\n",
    )
    _write(
        root / "seed.mjs",
        "import { PrismaClient } from '@prisma/client';\n"
        "const db = new PrismaClient();\nawait db.book.deleteMany(); await db.author.deleteMany();\n"
        "await db.author.create({data:{name:'Ada',books:{create:[{title:'Alpha Filtering',genre:'Tech',price:'10.00',note:'first'}]}}});\n"
        "await db.author.create({data:{name:'Bob',books:{create:[{title:'Beta Search',genre:'Tech',price:'30.00'},"
        "{title:'Gamma Grouping',genre:'Business',price:'40.00',note:'last'}]}}});\nawait db.$disconnect();\n",
    )
    _write(root / ".env", "DATABASE_URL=file:./filterx.db\n")


def _scaffold_spring(root: Path) -> None:
    _write(
        root / "pom.xml",
        """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <parent><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-parent</artifactId><version>3.4.7</version></parent>
  <groupId>com.example</groupId><artifactId>filterx-matrix</artifactId><version>1.0.0</version>
  <properties><java.version>21</java.version></properties>
  <dependencies>
    <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-web</artifactId></dependency>
    <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-data-jpa</artifactId></dependency>
    <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-security</artifactId></dependency>
    <dependency><groupId>com.h2database</groupId><artifactId>h2</artifactId><scope>runtime</scope></dependency>
  </dependencies>
  <build><plugins><plugin><groupId>org.springframework.boot</groupId><artifactId>spring-boot-maven-plugin</artifactId></plugin></plugins></build>
</project>
""",
    )
    _write(
        root / "src/main/java/com/example/FilterxFixtureApplication.java",
        "package com.example;\n\nimport org.springframework.boot.SpringApplication;\n"
        "import org.springframework.boot.autoconfigure.SpringBootApplication;\n\n"
        "@SpringBootApplication\npublic class FilterxFixtureApplication {\n"
        "  public static void main(String[] args) { SpringApplication.run(FilterxFixtureApplication.class, args); }\n}\n",
    )
    _write(
        root / "src/main/java/com/example/HealthController.java",
        "package com.example;\n\nimport java.util.Map;\n"
        "import org.springframework.web.bind.annotation.GetMapping;\n"
        "import org.springframework.web.bind.annotation.RestController;\n\n"
        "@RestController public class HealthController {\n"
        "  @GetMapping(\"/health\") public Map<String, Boolean> health() { return Map.of(\"ok\", true); }\n}\n",
    )
    _write(
        root / "src/main/java/com/example/HostSecurityConfiguration.java",
        "package com.example;\n\n"
        "import org.springframework.context.annotation.Bean;\nimport org.springframework.context.annotation.Configuration;\n"
        "import org.springframework.security.config.annotation.web.builders.HttpSecurity;\n"
        "import org.springframework.security.web.SecurityFilterChain;\n\n"
        "@Configuration public class HostSecurityConfiguration {\n"
        "  @Bean SecurityFilterChain permitAll(HttpSecurity http) throws Exception {\n"
        "    return http.securityMatcher(\"/health\").csrf(c -> c.disable()).authorizeHttpRequests(a -> a.anyRequest().permitAll()).build();\n"
        "  }\n}\n",
    )
    _write(
        root / "src/main/java/com/example/model/Author.java",
        "package com.example.model;\nimport jakarta.persistence.*;\nimport java.util.*;\n"
        "@Entity @Table(name=\"authors\") public class Author {\n"
        " @Id @GeneratedValue(strategy=GenerationType.IDENTITY) private Long id;\n"
        " @Column(nullable=false) private String name;\n"
        " @OneToMany(mappedBy=\"author\") private List<Book> books=new ArrayList<>();\n"
        " public Long getId(){return id;} public String getName(){return name;} public List<Book> getBooks(){return books;}\n}\n",
    )
    _write(
        root / "src/main/java/com/example/model/Book.java",
        "package com.example.model;\nimport jakarta.persistence.*;\nimport java.math.BigDecimal;\n"
        "@Entity @Table(name=\"books\") public class Book {\n"
        " @Id @GeneratedValue(strategy=GenerationType.IDENTITY) private Long id;\n"
        " @Column(nullable=false) private String title; @Column(nullable=false) private String genre;\n"
        " @Column(nullable=false) private BigDecimal price; private String note;\n"
        " @Column(name=\"author_id\",nullable=false) private Long authorId;\n"
        " @ManyToOne(fetch=FetchType.LAZY) @JoinColumn(name=\"author_id\",insertable=false,updatable=false) private Author author;\n"
        " public Long getId(){return id;} public String getTitle(){return title;} public String getGenre(){return genre;}\n"
        " public BigDecimal getPrice(){return price;} public String getNote(){return note;} public Long getAuthorId(){return authorId;} public Author getAuthor(){return author;}\n}\n",
    )
    _write(
        root / "src/main/resources/application.properties",
        "server.address=127.0.0.1\nspring.datasource.url=jdbc:h2:file:./filterx;AUTO_SERVER=TRUE\n"
        "spring.jpa.hibernate.ddl-auto=create-drop\nspring.jpa.defer-datasource-initialization=true\n"
        "spring.sql.init.mode=always\nspring.jpa.open-in-view=false\n",
    )
    _write(
        root / "src/main/resources/data.sql",
        "insert into authors(id,name) values (1,'Ada'),(2,'Bob');\n"
        "insert into books(id,title,genre,price,note,author_id) values "
        "(1,'Alpha Filtering','Tech',10.00,'first',1),(2,'Beta Search','Tech',30.00,null,2),"
        "(3,'Gamma Grouping','Business',40.00,'last',2);\n",
    )
    # Kept outside Java sources until scan succeeds: it references generated interfaces.
    _write(
        root / ".filterx/templates/FixtureSecurityConfiguration.java",
        "package com.example;\n\nimport com.example.filterx.generated.FilterxSecurity;\n"
        "import org.springframework.context.annotation.Bean;\nimport org.springframework.context.annotation.Configuration;\n\n"
        "@Configuration\npublic class FixtureSecurityConfiguration {\n"
        " @Bean FilterxSecurity.IdentityExtractor identity(){ return request -> request.getHeader(\"x-genre\") == null ? \"Tech\" : request.getHeader(\"x-genre\"); }\n"
        " @Bean FilterxSecurity.RowLevelSecurity rows(){ return (principal,entity,action,request) -> \"Book\".equals(entity.path(\"name\").asText()) ? (root,query,cb) -> cb.equal(root.get(\"genre\"),principal) : null; }\n"
        " @Bean FilterxSecurity.FieldVisibility fields(){ return (principal,entity,field,action,request) -> !\"price\".equals(field); }\n}\n",
    )


def _scaffold_angular(root: Path) -> None:
    front = root / "frontend"
    _write(
        front / "package.json",
        _json_document(
            "filterx-angular-matrix",
            {"start": "ng serve --host 127.0.0.1 --port 4200", "build": "ng build"},
            {"@angular/animations": "^18.2.0", "@angular/common": "^18.2.0", "@angular/compiler": "^18.2.0", "@angular/core": "^18.2.0", "@angular/forms": "^18.2.0", "@angular/platform-browser": "^18.2.0", "@angular/platform-browser-dynamic": "^18.2.0", "@angular/router": "^18.2.0", "rxjs": "^7.8.0", "tslib": "^2.6.0", "zone.js": "^0.14.10"},
            {"@angular-devkit/build-angular": "^18.2.0", "@angular/cli": "^18.2.0", "@angular/compiler-cli": "^18.2.0", "typescript": "~5.5.0"},
        ),
    )
    _write_json(front / "tsconfig.json", {"compileOnSave": False, "compilerOptions": {"baseUrl": "./", "outDir": "./dist/out-tsc", "strict": True, "noImplicitOverride": True, "noPropertyAccessFromIndexSignature": True, "noImplicitReturns": True, "noFallthroughCasesInSwitch": True, "sourceMap": True, "declaration": False, "downlevelIteration": True, "experimentalDecorators": True, "moduleResolution": "node", "importHelpers": True, "target": "ES2022", "module": "ES2022", "useDefineForClassFields": False, "lib": ["ES2022", "dom"]}, "angularCompilerOptions": {"enableI18nLegacyMessageIdFormat": False, "strictInjectionParameters": True, "strictInputAccessModifiers": True, "strictTemplates": True}})
    _write_json(front / "tsconfig.app.json", {"extends": "./tsconfig.json", "compilerOptions": {"outDir": "./out-tsc/app", "types": []}, "files": ["src/main.ts"], "include": ["src/**/*.d.ts"]})
    _write_json(front / "angular.json", {"$schema": "./node_modules/@angular/cli/lib/config/schema.json", "version": 1, "newProjectRoot": "projects", "projects": {"filterx-host": {"projectType": "application", "root": "", "sourceRoot": "src", "prefix": "app", "architect": {"build": {"builder": "@angular-devkit/build-angular:application", "options": {"outputPath": "dist/filterx-host", "index": "src/index.html", "browser": "src/main.ts", "tsConfig": "tsconfig.app.json", "assets": [], "styles": ["src/styles.scss"]}}, "serve": {"builder": "@angular-devkit/build-angular:dev-server", "options": {"buildTarget": "filterx-host:build", "proxyConfig": "proxy.conf.cjs"}}}}}})
    _write(front / "src/index.html", "<!doctype html><html><head><meta charset=\"utf-8\"><title>FilterX Matrix</title><base href=\"/\"></head><body><app-root></app-root></body></html>\n")
    _write(front / "src/styles.scss", "body { font-family: system-ui; margin: 2rem; }\n")
    _write(front / "src/main.ts", "import { bootstrapApplication } from '@angular/platform-browser';\nimport { AppComponent } from './app/app.component';\nimport { appConfig } from './app/app.config';\nbootstrapApplication(AppComponent, appConfig).catch(console.error);\n")
    _write(front / "src/app/app.component.ts", "import { Component } from '@angular/core';\nimport { RouterOutlet } from '@angular/router';\n@Component({selector:'app-root',standalone:true,imports:[RouterOutlet],template:'<h1>FilterX Matrix</h1><router-outlet />'}) export class AppComponent {}\n")
    _write(front / "src/app/app.routes.ts", "import { Routes } from '@angular/router';\nexport const routes: Routes = [\n  // FILTERX:ROUTES\n];\n")
    _write(front / "src/app/app.config.ts", "import { ApplicationConfig } from '@angular/core';\nimport { provideRouter } from '@angular/router';\nimport { routes } from './app.routes';\nexport const appConfig: ApplicationConfig = { providers: [provideRouter(routes),\n  // FILTERX:PROVIDERS\n] };\n")
    _write(front / "proxy.conf.cjs", "module.exports = {'/api': {target: 'http://127.0.0.1:8000', secure: false, changeOrigin: true}};\n")


def _scaffold_react(root: Path) -> None:
    front = root / "frontend"
    _write(front / "package.json", _json_document("filterx-react-matrix", {"dev": "vite --host 127.0.0.1 --port 5173", "build": "tsc -b && vite build"}, {"react": "^18.3.1", "react-dom": "^18.3.1"}, {"@types/react": "^18.3.0", "@types/react-dom": "^18.3.0", "@vitejs/plugin-react": "^4.3.0", "typescript": "^5.5.0", "vite": "^5.4.0"}))
    _write(front / "index.html", '<div id="root"></div><script type="module" src="/src/main.tsx"></script>\n')
    _write(front / "src/main.tsx", "import { StrictMode } from 'react'; import { createRoot } from 'react-dom/client'; import App from './App'; createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>);\n")
    _write(front / "src/App.tsx", "export default function App(){ return <main><h1>FilterX Matrix</h1>{/* // FILTERX:APP */}</main>; }\n")
    _write_json(front / "tsconfig.json", {"compilerOptions": {"target": "ES2022", "useDefineForClassFields": True, "lib": ["ES2022", "DOM", "DOM.Iterable"], "skipLibCheck": True, "esModuleInterop": True, "allowSyntheticDefaultImports": True, "strict": True, "module": "ESNext", "moduleResolution": "Bundler", "resolveJsonModule": True, "isolatedModules": True, "noEmit": True, "jsx": "react-jsx"}, "include": ["src"]})
    _write(front / "vite.config.ts", "import { defineConfig } from 'vite'; import react from '@vitejs/plugin-react'; export default defineConfig({plugins:[react()],server:{proxy:{'/api':'http://127.0.0.1:8000'}}});\n")


def _scaffold_next(root: Path) -> None:
    front = root / "frontend"
    _write(front / "package.json", _json_document("filterx-next-matrix", {"dev": "next dev -H 127.0.0.1 -p 3000", "build": "next build", "start": "next start -H 127.0.0.1 -p 3000"}, {"next": "^15.0.0", "react": "^19.0.0", "react-dom": "^19.0.0"}, {"@types/node": "^22.0.0", "@types/react": "^19.0.0", "@types/react-dom": "^19.0.0", "typescript": "^5.7.0"}))
    _write(front / "src/app/layout.tsx", "export default function Layout({children}:{children:React.ReactNode}){return <html><body>{children}</body></html>}\n")
    _write(front / "src/app/page.tsx", "export default function Home(){return <main><h1>FilterX Matrix</h1><a href='/filterx'>Open FilterX</a></main>}\n")
    _write(front / "next.config.ts", "import type { NextConfig } from 'next'; const config: NextConfig={async rewrites(){return [{source:'/api/:path*',destination:'http://127.0.0.1:8000/api/:path*'}]}}; export default config;\n")
    _write(front / "next-env.d.ts", '/// <reference types="next" />\n/// <reference types="next/image-types/global" />\n')
    _write_json(front / "tsconfig.json", {"compilerOptions": {"target": "ES2017", "lib": ["dom", "dom.iterable", "esnext"], "allowJs": True, "skipLibCheck": True, "strict": True, "noEmit": True, "esModuleInterop": True, "module": "esnext", "moduleResolution": "bundler", "resolveJsonModule": True, "isolatedModules": True, "jsx": "preserve", "incremental": True, "plugins": [{"name": "next"}]}, "include": ["next-env.d.ts", ".next/types/**/*.ts", "**/*.ts", "**/*.tsx"], "exclude": ["node_modules"]})


def _scaffold_vue(root: Path) -> None:
    front = root / "frontend"
    _write(front / "package.json", _json_document("filterx-vue-matrix", {"dev": "vite --host 127.0.0.1 --port 5173", "build": "vue-tsc -b && vite build"}, {"vue": "^3.5.0"}, {"@vitejs/plugin-vue": "^5.1.0", "typescript": "^5.5.0", "vite": "^5.4.0", "vue-tsc": "^2.1.0"}))
    _write(front / "index.html", '<div id="app"></div><script type="module" src="/src/main.ts"></script>\n')
    _write(front / "src/main.ts", "import { createApp } from 'vue'; import App from './App.vue'; createApp(App).mount('#app');\n")
    _write(front / "src/App.vue", '<script setup lang="ts">const title="FilterX Matrix";</script>\n<template><main><h1>{{ title }}</h1><!-- FILTERX:APP --></main></template>\n')
    _write(front / "src/env.d.ts", '/// <reference types="vite/client" />\n')
    _write_json(front / "tsconfig.json", {"compilerOptions": {"target": "ES2022", "useDefineForClassFields": True, "module": "ESNext", "lib": ["ES2022", "DOM", "DOM.Iterable"], "skipLibCheck": True, "moduleResolution": "Bundler", "allowImportingTsExtensions": True, "resolveJsonModule": True, "isolatedModules": True, "noEmit": True, "strict": True}, "include": ["src/**/*.ts", "src/**/*.vue"]})
    _write(front / "vite.config.ts", "import { defineConfig } from 'vite'; import vue from '@vitejs/plugin-vue'; export default defineConfig({plugins:[vue()],server:{proxy:{'/api':'http://127.0.0.1:8000'}}});\n")


def _commands_markdown(backend: str, frontend: str, maven_command: str) -> str:
    ps_bootstrap: list[str]
    sh_bootstrap: list[str]
    ps_cli = "filterx"
    sh_cli = "filterx"
    if backend == "fastapi-sqlalchemy":
        ps_bootstrap = ["py -m venv .venv", r".\.venv\Scripts\python.exe -m pip install -e <REPO_ROOT>\tools\filterx fastapi sqlalchemy uvicorn httpx", r".\.venv\Scripts\python.exe seed.py"]
        sh_bootstrap = ["python3 -m venv .venv", "./.venv/bin/python -m pip install -e <REPO_ROOT>/tools/filterx fastapi sqlalchemy uvicorn httpx", "./.venv/bin/python seed.py"]
        ps_cli = r".\.venv\Scripts\filterx.exe"
        sh_cli = "./.venv/bin/filterx"
        ps_runtime = r".\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
        sh_runtime = "./.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
        post_backend_ps: list[str] = []
        post_backend_sh: list[str] = []
    elif backend == "express-prisma":
        ps_bootstrap = sh_bootstrap = ["npm install --no-audit --no-fund", "npm exec prisma generate", "npm exec prisma db push -- --skip-generate", "npm run seed", "npm run build"]
        ps_runtime = sh_runtime = "npm start"
        post_backend_ps = post_backend_sh = ["npm install --no-audit --no-fund", "npm exec prisma db push -- --skip-generate", "npm run seed", "npm run build"]
    else:
        ps_bootstrap = [f'& "{maven_command}" -q -DskipTests compile', f'& "{maven_command}" -q -DskipTests package']
        sh_bootstrap = [f'"{maven_command}" -q -DskipTests compile', f'"{maven_command}" -q -DskipTests package']
        ps_runtime = sh_runtime = "java -jar target/filterx-matrix-1.0.0.jar --server.port=8000"
        post_backend_ps = [f'& "{maven_command}" -q -DskipTests package']
        post_backend_sh = [f'"{maven_command}" -q -DskipTests package']
    front_start = {"angular": "npm start", "react-vite": "npm run dev", "nextjs": "npm run dev", "vue": "npm run dev"}[frontend]
    def lifecycle(cli: str) -> list[str]:
        suffix = "--project-root . --config filterx.yaml --yes --json"
        return [f"{cli} scan {suffix}", f"{cli} backend install {suffix}", f"{cli} frontend install {suffix}", f"{cli} validate {suffix}", f"{cli} backend install {suffix}", f"{cli} frontend install {suffix}"]
    ps_lines = ["Set-Location <PROJECT_ROOT>", "# Verify the untouched host first", *ps_bootstrap, "Push-Location frontend", "npm install --no-audit --no-fund", "npm run build", "Pop-Location", "# Integrate FilterX and repeat installs to prove idempotency", *lifecycle(ps_cli), "# Reconcile generated dependencies and rebuild", *post_backend_ps, "Push-Location frontend", "npm install --no-audit --no-fund", "npm run build", "Pop-Location", "# Backend terminal", ps_runtime, "# Frontend terminal (from <PROJECT_ROOT>/frontend)", front_start, "# Roll back frontend then backend in reverse patch order", f"{ps_cli} rollback --project-root . --config filterx.yaml --yes --json", f"{ps_cli} rollback --project-root . --config filterx.yaml --yes --json"]
    sh_lines = ["cd <PROJECT_ROOT>", "# Verify the untouched host first", *sh_bootstrap, "(cd frontend && npm install --no-audit --no-fund && npm run build)", "# Integrate FilterX and repeat installs to prove idempotency", *lifecycle(sh_cli), "# Reconcile generated dependencies and rebuild", *post_backend_sh, "(cd frontend && npm install --no-audit --no-fund && npm run build)", "# Backend terminal", sh_runtime, "# Frontend terminal (from <PROJECT_ROOT>/frontend)", front_start, "# Roll back frontend then backend in reverse patch order", f"{sh_cli} rollback --project-root . --config filterx.yaml --yes --json", f"{sh_cli} rollback --project-root . --config filterx.yaml --yes --json"]
    ps_text = "\n".join(ps_lines)
    sh_text = "\n".join(sh_lines)
    return f"# Reproducible commands: {backend} + {frontend}\n\nReplace `<PROJECT_ROOT>` and `<REPO_ROOT>`. Commands are ordered exactly as qualification ran them; runtime commands marked as separate terminals must run concurrently.\n\n## PowerShell\n\n```powershell\n{ps_text}\n```\n\n## POSIX shell\n\n```sh\n{sh_text}\n```\n"


def scaffold_combination(root: Path, backend: str, frontend: str, maven_command: str) -> CombinationResult:
    name = _combination_name(backend, frontend)
    root.mkdir(parents=True, exist_ok=True)
    (root / ".filterx/cli-logs").mkdir(parents=True, exist_ok=True)
    cfg = _config(backend, frontend, name, maven_command)
    _write(root / "filterx.yaml", yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True))
    {"fastapi-sqlalchemy": _scaffold_fastapi, "express-prisma": _scaffold_express, "spring-boot-jpa": _scaffold_spring}[backend](root)
    {"angular": _scaffold_angular, "react-vite": _scaffold_react, "nextjs": _scaffold_next, "vue": _scaffold_vue}[frontend](root)
    _write(root / "COMMANDS.md", _commands_markdown(backend, frontend, maven_command))
    # Prove the first and only config is valid before any subprocess can run.
    load_effective_config(root, root / "filterx.yaml")
    result = CombinationResult(name=name, backend=backend, frontend=frontend, project_root=str(root))
    _write_json(root / "result.json", _result_document(result))
    return result


def _result_document(result: CombinationResult) -> dict[str, Any]:
    document = asdict(result)
    document["commands"] = [asdict(command) for command in result.commands]
    return document


def _display_command(command: Sequence[str]) -> str:
    return subprocess.list2cmdline(list(command)) if os.name == "nt" else " ".join(_shell_quote(item) for item in command)


def _shell_quote(value: str) -> str:
    if value and all(character.isalnum() or character in "-._/:=+" for character in value):
        return value
    return "'" + value.replace("'", "'\"'\"'") + "'"


def _run_logged(result: CombinationResult, stage: str, command: Sequence[str], cwd: Path, *, env: dict[str, str] | None = None, timeout: float = 900) -> bool:
    started = time.monotonic()
    stdout = ""
    stderr = ""
    try:
        completed = subprocess.run(list(command), cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False)
        code, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
    except subprocess.TimeoutExpired as error:
        code = 124
        stdout = _subprocess_text(error.stdout)
        timeout_stderr = _subprocess_text(error.stderr)
        stderr = timeout_stderr + f"\nTimed out after {timeout} seconds."
    except OSError as error:
        code, stderr = 127, str(error)
    duration = time.monotonic() - started
    index = len(result.commands) + 1
    relative_log = f".filterx/cli-logs/{index:02d}-{stage}.json"
    entry = CommandResult(stage, list(command), str(cwd), code, stdout, stderr, round(duration, 6), relative_log)
    result.commands.append(entry)
    _write_json(Path(result.project_root) / relative_log, asdict(entry))
    _write_json(Path(result.project_root) / "result.json", _result_document(result))
    return code == 0


def _subprocess_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _venv_paths(project: Path) -> tuple[Path, Path]:
    scripts = project / ".venv" / ("Scripts" if os.name == "nt" else "bin")
    return scripts / ("python.exe" if os.name == "nt" else "python"), scripts / ("filterx.exe" if os.name == "nt" else "filterx")


def _base_env(repo_root: Path) -> dict[str, str]:
    env = dict(os.environ)
    package_root = str(repo_root / "tools/filterx")
    env["PYTHONPATH"] = package_root + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env["DATABASE_URL"] = "file:./filterx.db"
    return env


def _executable(name: str) -> str:
    """Resolve platform-specific command shims before shell-free execution."""
    return shutil.which(name) or name


def _prepare_dependencies(options: Options, result: CombinationResult) -> tuple[str, dict[str, str]] | None:
    project = Path(result.project_root)
    env = _base_env(options.repo_root)
    if options.skip_dependency_install:
        executable = str(_venv_paths(project)[1]) if result.backend == "fastapi-sqlalchemy" else sys.executable
        return executable, env
    if result.backend == "fastapi-sqlalchemy":
        if not _run_logged(result, "python-venv", [sys.executable, "-m", "venv", ".venv"], project, env=env):
            return None
        python, executable = _venv_paths(project)
        if not _run_logged(result, "python-dependencies", [str(python), "-m", "pip", "install", "-e", str(options.repo_root / "tools/filterx"), "fastapi", "sqlalchemy", "uvicorn", "httpx"], project, env=env):
            return None
        cli_executable = str(executable)
    elif result.backend == "express-prisma":
        if not _run_logged(result, "backend-npm-install", [_executable("npm"), "install", "--no-audit", "--no-fund"], project, env=env):
            return None
        if not _run_logged(result, "prisma-generate", [_executable("npm"), "exec", "prisma", "generate"], project, env=env):
            return None
        cli_executable = sys.executable
    else:
        if not _run_logged(result, "spring-host-compile", [options.maven_command, "-q", "-DskipTests", "compile"], project, env=env):
            return None
        cli_executable = sys.executable
    if not options.skip_dependency_install and not _run_logged(
        result,
        "frontend-host-npm-install",
        [_executable("npm"), "install", "--no-audit", "--no-fund"],
        project / "frontend",
        env=env,
    ):
        return None
    return cli_executable, env


def _host_backend_build(options: Options, result: CombinationResult, env: dict[str, str], prefix: str) -> bool:
    project = Path(result.project_root)
    if result.backend == "fastapi-sqlalchemy":
        python, _ = _venv_paths(project)
        return _run_logged(result, f"{prefix}-seed", [str(python), "seed.py"], project, env=env)
    if result.backend == "express-prisma":
        commands = [
            (f"{prefix}-db-push", [_executable("npm"), "exec", "prisma", "db", "push", "--", "--skip-generate"]),
            (f"{prefix}-seed", [_executable("npm"), "run", "seed"]),
            (f"{prefix}-build", [_executable("npm"), "run", "build"]),
        ]
    else:
        commands = [(f"{prefix}-package", [options.maven_command, "-q", "-DskipTests", "package"])]
    return all(_run_logged(result, stage, command, project, env=env) for stage, command in commands)


def _host_frontend_build(result: CombinationResult, env: dict[str, str], prefix: str) -> bool:
    return _run_logged(
        result,
        f"{prefix}-frontend-build",
        [_executable("npm"), "run", "build"],
        Path(result.project_root) / "frontend",
        env=env,
    )


def _host_snapshot(project: Path) -> dict[str, str]:
    ignored_parts = {
        ".angular", ".filterx", ".venv", ".next", "__pycache__", "dist", "node_modules", "out-tsc", "target"
    }
    ignored_names = {
        "filterx.db", "filterx.lock.db", "filterx.mv.db", "filterx.trace.db", "host-baseline.json",
        "COMMANDS.md", "package-lock.json", "result.json"
    }
    snapshot: dict[str, str] = {}
    for path in sorted(project.rglob("*")):
        relative = path.relative_to(project)
        if not path.is_file() or any(part in ignored_parts for part in relative.parts) or path.name in ignored_names:
            continue
        snapshot[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return snapshot


def _cli_command(executable: str, backend: str, words: Sequence[str], project: Path) -> list[str]:
    prefix = [executable] if backend == "fastapi-sqlalchemy" else [executable, "-m", "filterx.cli"]
    return prefix + list(words) + ["--project-root", str(project), "--config", str(project / "filterx.yaml"), "--yes", "--json"]


def _lifecycle(options: Options, result: CombinationResult, executable: str, env: dict[str, str]) -> bool:
    project = Path(result.project_root)
    stages = [
        ("scan", ["scan"]),
        ("backend-install", ["backend", "install"]),
        ("frontend-install", ["frontend", "install"]),
        ("validate", ["validate"]),
        ("backend-reinstall", ["backend", "install"]),
        ("frontend-reinstall", ["frontend", "install"]),
    ]
    for stage, words in stages:
        command = _cli_command(executable, result.backend, words, project)
        if not _run_logged(result, stage, command, project, env=env):
            result.failed_stage = stage
            return False
        if stage == "scan" and result.backend == "spring-boot-jpa":
            source = project / ".filterx/templates/FixtureSecurityConfiguration.java"
            target = project / "src/main/java/com/example/FixtureSecurityConfiguration.java"
            shutil.copyfile(source, target)
        if stage in {"backend-reinstall", "frontend-reinstall"}:
            try:
                payload = json.loads(result.commands[-1].stdout)
                assert payload.get("applied_ops") == 0, payload
            except (AssertionError, json.JSONDecodeError) as error:
                result.error = f"idempotency assertion failed for {stage}: {error}"
                result.failed_stage = stage
                return False
    result.checks.append({"check": "filterx-idempotent-reinstall", "status": "passed"})
    return True


def _build_hosts(options: Options, result: CombinationResult, env: dict[str, str]) -> bool:
    project = Path(result.project_root)
    if result.backend == "express-prisma" and not options.skip_dependency_install and not _run_logged(
        result,
        "backend-npm-install-after-filterx",
        [_executable("npm"), "install", "--no-audit", "--no-fund"],
        project,
        env=env,
    ):
        return False
    if not _host_backend_build(options, result, env, "host-after-filterx"):
        return False
    if not options.skip_dependency_install and not _run_logged(result, "frontend-npm-install", [_executable("npm"), "install", "--no-audit", "--no-fund"], project / "frontend", env=env):
        return False
    return _host_frontend_build(result, env, "host-after-filterx")


def _port_free(port: int) -> bool:
    with socket.socket() as sock:
        try:
            sock.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def _request(url: str, *, method: str = "GET", body: Any = None, headers: dict[str, str] | None = None, timeout: float = 15) -> tuple[int, bytes, dict[str, str]]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, method=method, data=data, headers={"content-type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read(), dict(response.headers.items())
    except urllib.error.HTTPError as error:
        return error.code, error.read(), dict(error.headers.items())


def _wait_ready(url: str, process: subprocess.Popen[str], timeout: float = 90) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"process exited with {process.returncode} before {url} became ready")
        try:
            status, _, _ = _request(url, timeout=2)
            if status < 500:
                return
        except (OSError, urllib.error.URLError):
            pass
        time.sleep(0.2)
    raise TimeoutError(f"timed out waiting for {url}")


def _start(command: Sequence[str], cwd: Path, env: dict[str, str], log_path: Path) -> tuple[subprocess.Popen[str], Any]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    stream = log_path.open("w", encoding="utf-8")
    process = subprocess.Popen(list(command), cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT, text=True, creationflags=CREATE_NEW_PROCESS_GROUP)
    return process, stream


def _stop(process: subprocess.Popen[str], stream: Any) -> None:
    try:
        if process.poll() is None:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, check=False)
            else:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
    finally:
        stream.close()


def _backend_launch(options: Options, result: CombinationResult) -> list[str]:
    project = Path(result.project_root)
    if result.backend == "fastapi-sqlalchemy":
        python, _ = _venv_paths(project)
        return [str(python), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"]
    if result.backend == "express-prisma":
        return [_executable("node"), "dist/server.js"]
    jars = [path for path in (project / "target").glob("*.jar") if not path.name.endswith(".original")]
    if len(jars) != 1:
        raise RuntimeError(f"expected one Spring boot JAR, found {len(jars)}")
    return ["java", "-jar", str(jars[0]), "--server.port=8000"]


def _verify_host_before_integration(
    options: Options,
    result: CombinationResult,
    env: dict[str, str],
    check_name: str = "host-before-filterx-runtime",
) -> bool:
    project = Path(result.project_root)
    if not _host_backend_build(options, result, env, "host-before-filterx"):
        return False
    if not _host_frontend_build(result, env, "host-before-filterx"):
        return False
    if options.skip_runtime:
        result.checks.append({"check": "host-before-filterx-builds", "status": "passed"})
        return True
    if not _port_free(8000):
        result.error = "backend port 8000 is already in use before FilterX integration"
        return False
    backend_process = frontend_process = None
    backend_stream = frontend_stream = None
    try:
        backend_process, backend_stream = _start(
            _backend_launch(options, result),
            project,
            env,
            project / ".filterx/cli-logs/host-before-filterx-backend.log",
        )
        _wait_ready("http://127.0.0.1:8000/health", backend_process, timeout=120)
        status, body, _ = _request("http://127.0.0.1:8000/health")
        assert status == 200 and _json(body).get("ok") is True
        front_command, front_port = _frontend_runtime(result)
        if not _port_free(front_port):
            raise RuntimeError(f"frontend port {front_port} is already in use")
        frontend_process, frontend_stream = _start(
            front_command,
            project / "frontend",
            env,
            project / ".filterx/cli-logs/host-before-filterx-frontend.log",
        )
        _wait_ready(f"http://127.0.0.1:{front_port}/", frontend_process, timeout=120)
        status, page, _ = _request(f"http://127.0.0.1:{front_port}/")
        assert status == 200 and page
        result.checks.append({"check": check_name, "status": "passed"})
        return True
    except Exception as error:
        result.error = f"{type(error).__name__}: {error}"
        return False
    finally:
        if frontend_process is not None:
            _stop(frontend_process, frontend_stream)
        if backend_process is not None:
            _stop(backend_process, backend_stream)


def _json(data: bytes) -> Any:
    return json.loads(data.decode("utf-8"))


def _titles(payload: Any) -> list[str]:
    rows = payload if isinstance(payload, list) else payload.get("data", [])
    return [str(row["title"]) for row in rows]


def _assert_contract(result: CombinationResult) -> None:
    base = "http://127.0.0.1:8000/api/filterx"
    headers = {"x-genre": "Tech"}
    status, metadata_raw, _ = _request(f"{base}/metadata", headers=headers)
    assert status == 200 and _json(metadata_raw)
    result.checks.append({"check": "metadata", "status": "passed"})

    status, query_raw, _ = _request(f"{base}/books?size=20&sort_by=title&order=asc", headers=headers)
    query = _json(query_raw)
    assert status == 200 and _titles(query) == EXPECTED_TITLES
    assert all(row.get("genre") == "Tech" and "price" not in row for row in query["data"])
    result.checks.append({"check": "row-and-field-security", "status": "passed"})

    status, business_raw, _ = _request(
        f"{base}/books?size=20&sort_by=title&order=asc", headers={"x-genre": "Business"}
    )
    assert status == 200 and _titles(_json(business_raw)) == ["Gamma Grouping"]
    assert "price" not in _json(business_raw)["data"][0]
    result.checks.append({"check": "alternate-principal-row-security", "status": "passed"})

    cases = [
        ("url-equality", "title_eq=Alpha%20Filtering", ["Alpha Filtering"]),
        ("url-in", "genre_in=Tech%2CBusiness", EXPECTED_TITLES),
        ("url-null", "note_is_null=true", ["Beta Search"]),
        ("search", "search=beta", ["Beta Search"]),
        ("sort-descending", "sort_by=title&order=desc", list(reversed(EXPECTED_TITLES))),
    ]
    for check, query_string, expected in cases:
        status, raw, _ = _request(f"{base}/books?size=20&{query_string}", headers=headers)
        assert status == 200 and _titles(_json(raw)) == expected
        result.checks.append({"check": check, "status": "passed"})

    for page, expected in ((1, ["Alpha Filtering"]), (2, ["Beta Search"]), (3, [])):
        status, raw, _ = _request(
            f"{base}/books?page={page}&size=1&sort_by=title&order=asc", headers=headers
        )
        assert status == 200 and _titles(_json(raw)) == expected
    result.checks.append({"check": "pagination-boundaries", "status": "passed"})

    body = {"filter_tree": {"node_type": "condition", "field": "author.name", "operation": "eq", "value": "Bob"}}
    status, nested_raw, _ = _request(f"{base}/books/filter?sort_by=title", method="POST", body=body, headers=headers)
    assert status == 200 and _titles(_json(nested_raw)) == ["Beta Search"]
    result.checks.append({"check": "nested-filter", "status": "passed"})

    complex_body = {
        "filter_tree": {
            "node_type": "operator",
            "operator": "AND",
            "children": [
                {"node_type": "condition", "field": "genre", "operation": "in", "value": ["Tech", "Business"]},
                {
                    "node_type": "operator",
                    "operator": "OR",
                    "children": [
                        {"node_type": "condition", "field": "title", "operation": "starts_with", "value": "Alpha"},
                        {"node_type": "condition", "field": "note", "operation": "is_null", "value": None},
                    ],
                },
            ],
        }
    }
    status, complex_raw, _ = _request(
        f"{base}/books/filter?sort_by=title", method="POST", body=complex_body, headers=headers
    )
    assert status == 200 and _titles(_json(complex_raw)) == EXPECTED_TITLES
    result.checks.append({"check": "nested-and-or-in-null-filter", "status": "passed"})

    status, grouped_raw, _ = _request(f"{base}/books/group-by/genre", headers=headers)
    assert status == 200 and _json(grouped_raw) == [{"key": "Tech", "count": 2}]
    result.checks.append({"check": "grouping", "status": "passed"})

    filtered_group_body = {
        "filter_tree": {
            "node_type": "condition",
            "field": "title",
            "operation": "starts_with",
            "value": "Beta",
        }
    }
    status, filtered_group_raw, _ = _request(
        f"{base}/books/group-by/genre/filter",
        method="POST",
        body=filtered_group_body,
        headers=headers,
    )
    assert status == 200 and _json(filtered_group_raw) == [{"key": "Tech", "count": 1}]
    result.checks.append({"check": "filtered-grouping", "status": "passed"})

    status, _, _ = _request(f"{base}/books/group-by/price", headers=headers)
    assert status in {400, 403}
    result.checks.append({"check": "hidden-field-grouping-rejected", "status": "passed"})

    export_body = {"filter_tree": {"node_type": "condition", "field": "genre", "operation": "eq", "value": "Tech"}}
    for fmt in ("json", "csv", "xlsx"):
        status, exported, _ = _request(f"{base}/books/export?format={fmt}&sort_by=title&order=asc", method="POST", body=export_body, headers=headers, timeout=30)
        assert status == 200
        if fmt == "json":
            rows = _json(exported)
            assert _titles(rows) == EXPECTED_TITLES and all("price" not in row for row in rows)
        elif fmt == "csv":
            rows = list(csv.DictReader(io.StringIO(exported.decode("utf-8-sig"))))
            assert _titles(rows) == EXPECTED_TITLES and "price" not in rows[0]
        else:
            with zipfile.ZipFile(io.BytesIO(exported)) as workbook:
                xml = "".join(workbook.read(name).decode("utf-8", errors="replace") for name in workbook.namelist() if name.endswith(".xml"))
            assert all(title in xml for title in EXPECTED_TITLES) and ">price<" not in xml
        result.checks.append({"check": f"{fmt}-export", "status": "passed"})


def _frontend_runtime(result: CombinationResult) -> tuple[list[str], int]:
    if result.frontend == "angular":
        return [_executable("npm"), "start", "--", "--host", "127.0.0.1", "--port", "4200"], 4200
    return [_executable("npm"), "run", "dev"], 3000 if result.frontend == "nextjs" else 5173


def _runtime(options: Options, result: CombinationResult, env: dict[str, str]) -> bool:
    if not _port_free(8000):
        result.error = "backend port 8000 is already in use"
        return False
    project = Path(result.project_root)
    backend_process = frontend_process = None
    backend_stream = frontend_stream = None
    try:
        backend_process, backend_stream = _start(_backend_launch(options, result), project, env, project / ".filterx/cli-logs/backend-runtime.log")
        _wait_ready("http://127.0.0.1:8000/health", backend_process, timeout=120)
        _assert_contract(result)
        front_command, front_port = _frontend_runtime(result)
        if not _port_free(front_port):
            raise RuntimeError(f"frontend port {front_port} is already in use")
        frontend_process, frontend_stream = _start(front_command, project / "frontend", env, project / ".filterx/cli-logs/frontend-runtime.log")
        _wait_ready(f"http://127.0.0.1:{front_port}/", frontend_process, timeout=120)
        status, _, _ = _request(f"http://127.0.0.1:{front_port}/")
        assert status == 200
        status, metadata, _ = _request(f"http://127.0.0.1:{front_port}/api/filterx/metadata")
        assert status == 200 and _json(metadata)
        generated_page = "/filterx" if result.frontend == "nextjs" else "/books"
        status, page, _ = _request(f"http://127.0.0.1:{front_port}{generated_page}")
        assert status == 200 and page
        result.checks.append({"check": "frontend-page-and-proxy", "status": "passed"})
        return True
    except Exception as error:  # manual runner records assertion detail and proceeds with the matrix
        result.error = f"{type(error).__name__}: {error}"
        return False
    finally:
        if frontend_process is not None:
            _stop(frontend_process, frontend_stream)
        if backend_process is not None:
            _stop(backend_process, backend_stream)


def _rollback_and_verify(
    options: Options,
    result: CombinationResult,
    executable: str,
    env: dict[str, str],
) -> bool:
    project = Path(result.project_root)
    list_command = _cli_command(executable, result.backend, ["rollback", "--list"], project)
    if not _run_logged(result, "rollback-list", list_command, project, env=env):
        return False
    try:
        patches = json.loads(result.commands[-1].stdout).get("patches", [])
    except json.JSONDecodeError as error:
        result.error = f"could not parse rollback list: {error}"
        return False
    if not patches:
        result.error = "FilterX produced no patch bundles to roll back"
        return False
    for index, patch_id in enumerate(reversed(patches), start=1):
        command = _cli_command(
            executable,
            result.backend,
            ["rollback", "--patch-id", str(patch_id)],
            project,
        )
        if not _run_logged(result, f"rollback-{index:02d}", command, project, env=env):
            return False

    spring_fixture = project / "src/main/java/com/example/FixtureSecurityConfiguration.java"
    if spring_fixture.exists():
        spring_fixture.unlink()
    if not options.skip_dependency_install and not _run_logged(
        result,
        "post-rollback-frontend-npm-install",
        [_executable("npm"), "install", "--no-audit", "--no-fund"],
        project / "frontend",
        env=env,
    ):
        return False
    if not _verify_host_before_integration(options, result, env, "post-rollback-host-runtime"):
        return False
    restored = _host_snapshot(project)
    if restored != result.host_baseline:
        missing = sorted(set(result.host_baseline) - set(restored))
        extra = sorted(set(restored) - set(result.host_baseline))
        changed = sorted(
            path for path in set(restored) & set(result.host_baseline)
            if restored[path] != result.host_baseline[path]
        )
        result.error = f"rollback did not restore host snapshot; missing={missing}, extra={extra}, changed={changed}"
        return False
    result.checks.append({"check": "rollback-exact-host-restore", "status": "passed"})
    return True


def run_combination(options: Options, backend: str, frontend: str) -> CombinationResult:
    project = options.root / _combination_name(backend, frontend)
    if project.exists() and not options.keep_existing:
        shutil.rmtree(project)
    if project.exists():
        cfg = load_effective_config(project, project / "filterx.yaml").raw
        if cfg["backend"]["framework"] != backend or cfg["frontend"]["framework"] != frontend:
            raise ValueError(f"existing project {project} does not match requested combination")
        result = CombinationResult(_combination_name(backend, frontend), backend, frontend, str(project), status="reused")
        (project / ".filterx/cli-logs").mkdir(parents=True, exist_ok=True)
    else:
        result = scaffold_combination(project, backend, frontend, options.maven_command)
    if options.scaffold_only:
        return result
    prepared = _prepare_dependencies(options, result)
    if prepared is None:
        result.status, result.failed_stage = "failed", result.commands[-1].stage
        return result
    executable, env = prepared
    if not _verify_host_before_integration(options, result, env):
        result.status, result.failed_stage = "failed", "host-before-filterx"
        return result
    result.host_baseline = _host_snapshot(project)
    _write_json(project / "host-baseline.json", result.host_baseline)
    if not _lifecycle(options, result, executable, env):
        result.status = "failed"
        return result
    if not _build_hosts(options, result, env):
        result.status, result.failed_stage = "failed", result.commands[-1].stage
        return result
    if not options.skip_runtime and not _runtime(options, result, env):
        result.status, result.failed_stage = "failed", "runtime"
        return result
    if not _rollback_and_verify(options, result, executable, env):
        result.status, result.failed_stage = "failed", "rollback"
        return result
    result.status = "passed"
    return result


def _summary(options: Options, results: Iterable[CombinationResult]) -> dict[str, Any]:
    values = list(results)
    return {
        "repo_root": str(options.repo_root),
        "root": str(options.root),
        "python_executable": sys.executable,
        "options": {"maven_command": options.maven_command, "keep_existing": options.keep_existing, "skip_runtime": options.skip_runtime, "skip_dependency_install": options.skip_dependency_install, "scaffold_only": options.scaffold_only},
        "counts": {status: sum(result.status == status for result in values) for status in ("scaffolded", "reused", "passed", "failed")},
        "combinations": [_result_document(result) for result in values],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3], help="FilterX repository root")
    parser.add_argument("--root", type=Path, required=True, help="Generated matrix workspace")
    parser.add_argument("--maven-command", default=os.environ.get("FILTERX_MAVEN_COMMAND", "mvn"))
    parser.add_argument("--only", action="append", default=[], metavar="BACKEND__FRONTEND", help="Run only this combination; repeatable")
    parser.add_argument("--keep-existing", action="store_true")
    parser.add_argument("--skip-runtime", action="store_true")
    parser.add_argument("--skip-dependency-install", action="store_true")
    parser.add_argument("--scaffold-only", action="store_true", help="Create projects/config/docs/results without invoking subprocesses")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        only = _parse_only(args.only)
    except argparse.ArgumentTypeError as error:
        build_parser().error(str(error))
    options = Options(args.repo_root.resolve(), args.root.resolve(), args.maven_command, only, args.keep_existing, args.skip_runtime, args.skip_dependency_install, args.scaffold_only)
    options.root.mkdir(parents=True, exist_ok=True)
    selected = only or tuple(_combination_name(backend, frontend) for backend in BACKENDS for frontend in FRONTENDS)
    results: list[CombinationResult] = []
    for name in selected:
        backend, frontend = name.split("__", 1)
        try:
            result = run_combination(options, backend, frontend)
        except Exception as error:
            result = CombinationResult(name, backend, frontend, str(options.root / name), status="failed", failed_stage="scaffold", error=f"{type(error).__name__}: {error}")
        results.append(result)
        project = Path(result.project_root)
        if project.exists():
            _write_json(project / "result.json", _result_document(result))
        _write_json(options.root / "matrix-summary.json", _summary(options, results))
    return 1 if any(result.status == "failed" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
