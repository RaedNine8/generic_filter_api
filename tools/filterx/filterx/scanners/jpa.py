from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, replace
from importlib import metadata
from pathlib import Path
from typing import Any, Mapping, Sequence

from filterx.core.ir import IR_VERSION, FilterxIR, SecurityHooksIR, ir_from_dict, validate_ir

from .base import ScannerContext, ScannerError, ScannerExecutionMode


_MINIMUM_JAVA_VERSION = 17
_FALLBACK_PACKAGE_VERSION = "0.1.0"


@dataclass(frozen=True)
class JPABuildTool:
    kind: str
    command: str
    wrapper: bool


class JPAScannerPlugin:
    name = "jpa"
    version = "1.0.0"
    execution_mode = ScannerExecutionMode.NEW_TOOLCHAIN

    def _settings(self, context: ScannerContext) -> Mapping[str, Any]:
        return context.config.get("scan", {}).get("jpa", {})

    def _module_root(self, context: ScannerContext) -> Path:
        configured = str(self._settings(context).get("module_path", "."))
        root = (context.project_root / configured).resolve()
        try:
            root.relative_to(context.project_root.resolve())
        except ValueError as exc:
            raise ScannerError(
                "JPA_MODULE_INVALID",
                "scan.jpa.module_path must resolve inside the FilterX project root.",
                context={"module_path": configured, "resolved_path": str(root)},
            ) from exc
        if not root.is_dir():
            raise ScannerError(
                "JPA_MODULE_MISSING",
                f"The configured JPA module directory does not exist: '{root}'.",
                context={"module_path": configured},
            )
        return root

    def _helper_source(self, context: ScannerContext) -> Path:
        configured = self._settings(context).get("helper_source")
        helper = (
            (context.project_root / str(configured)).resolve()
            if configured
            else Path(__file__).parents[1] / "reference_runtime/scanners/FilterxJpaScanner.java"
        )
        if not helper.is_file():
            raise ScannerError(
                "JPA_HELPER_MISSING",
                f"The versioned JPA scanner helper source was not found at '{helper}'. Reinstall FilterX or correct scan.jpa.helper_source.",
                context={"helper_source": str(helper)},
            )
        return helper

    def resolve_build_tool(self, context: ScannerContext) -> JPABuildTool:
        settings = self._settings(context)
        module_root = self._module_root(context)
        configured = settings.get("build_tool")
        if configured not in {None, "maven", "gradle"}:
            raise ScannerError("JPA_BUILD_TOOL_INVALID", "scan.jpa.build_tool must be 'maven' or 'gradle'.")

        kinds = [str(configured)] if configured else []
        if not kinds:
            if (module_root / "pom.xml").exists():
                kinds.append("maven")
            if (module_root / "build.gradle").exists() or (module_root / "build.gradle.kts").exists():
                kinds.append("gradle")
        if len(kinds) != 1:
            reason = "both Maven and Gradle manifests were found" if len(kinds) > 1 else "no pom.xml or Gradle build file was found"
            raise ScannerError(
                "JPA_BUILD_TOOL_AMBIGUOUS" if len(kinds) > 1 else "JPA_BUILD_TOOL_MISSING",
                f"JPA build tool detection failed because {reason}. Set scan.jpa.build_tool and scan.jpa.module_path explicitly.",
                context={"module_path": str(module_root)},
            )

        kind = kinds[0]
        override_key = "maven_command" if kind == "maven" else "gradle_command"
        override = settings.get(override_key)
        if override:
            return JPABuildTool(kind, str(override), False)

        wrapper_names = ("mvnw.cmd", "mvnw") if kind == "maven" else ("gradlew.bat", "gradlew")
        search_roots = tuple(dict.fromkeys((module_root, context.project_root.resolve())))
        for root in search_roots:
            for name in wrapper_names:
                candidate = root / name
                if candidate.is_file():
                    return JPABuildTool(kind, str(candidate), True)
        return JPABuildTool(kind, "mvn" if kind == "maven" else "gradle", False)

    def build_commands(self, context: ScannerContext, tool: JPABuildTool, classpath_file: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
        settings = self._settings(context)
        if tool.kind == "maven":
            extra = tuple(str(item) for item in settings.get("maven_args", []))
            compile_command = (tool.command, *extra, "-DskipTests", "compile")
            classpath_command = (
                tool.command,
                *extra,
                "-DskipTests",
                "dependency:build-classpath",
                f"-Dmdep.outputFile={classpath_file}",
                "-Dmdep.includeScope=runtime",
            )
            return compile_command, classpath_command

        extra = tuple(str(item) for item in settings.get("gradle_args", []))
        compile_command = (tool.command, *extra, "classes", "--no-daemon")
        return compile_command, ()

    def decode_ir(self, payload: Mapping[str, Any]) -> FilterxIR:
        return ir_from_dict(payload)

    def scan(self, context: ScannerContext) -> FilterxIR:
        settings = self._settings(context)
        module_root = self._module_root(context)
        helper = self._helper_source(context)
        java = str(settings.get("java_command", "java"))
        helper_timeout = float(settings.get("helper_timeout_seconds", context.timeout_seconds))
        compile_timeout = float(settings.get("compile_timeout_seconds", 120))

        self._check_java(java, module_root, helper_timeout)
        package_version = _package_version()
        self._check_helper_version(java, helper, package_version, module_root, helper_timeout)

        configured_classes = settings.get("classes_dir")
        configured_classpath = settings.get("classpath")
        if configured_classes:
            classes_dir = (module_root / str(configured_classes)).resolve()
            classpath = str(configured_classpath or classes_dir)
        else:
            tool = self.resolve_build_tool(context)
            classes_dir, classpath = self._compile_and_classpath(
                context, tool, module_root, compile_timeout
            )

        if not classes_dir.is_dir():
            raise ScannerError(
                "JPA_CLASSES_MISSING",
                f"JPA compilation completed but compiled classes were not found at '{classes_dir}'. Set scan.jpa.classes_dir for a nonstandard layout.",
                context={"classes_dir": str(classes_dir)},
            )

        max_depth = int(context.config.get("scan", {}).get("max_relationship_depth", 3))
        command = (
            java,
            "--class-path",
            classpath,
            str(helper),
            "--helper-version",
            package_version,
            "--classes-dir",
            str(classes_dir),
            "--max-depth",
            str(max_depth),
        )
        result = self._run(
            command,
            cwd=module_root,
            timeout=helper_timeout,
            timeout_code="JPA_HELPER_TIMEOUT",
            timeout_message="JPA reflection helper timed out while loading compiled entities.",
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if "FILTERX_HELPER_VERSION_MISMATCH" in stderr:
                raise ScannerError(
                    "JPA_HELPER_VERSION_MISMATCH",
                    "The JPA helper artifact version does not match the installed FilterX package. Reinstall FilterX so both artifacts come from the same release.",
                    context={"package_version": package_version, "stderr": stderr},
                )
            raise ScannerError(
                "JPA_REFLECTION_FAILED",
                "The JPA helper could not reflect the compiled entity metadata. Ensure the module runtime classpath contains JPA and all entity dependencies.",
                context={"exit_code": result.returncode, "stderr": stderr},
            )
        try:
            payload = json.loads(result.stdout)
            if not isinstance(payload, Mapping):
                raise TypeError("IR document root is not an object")
            ir = self.decode_ir(payload)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise ScannerError(
                "JPA_OUTPUT_INVALID",
                "The JPA helper returned invalid filterx-ir/v1 JSON.",
                context={"error": str(exc), "stdout": result.stdout[-2000:]},
            ) from exc

        backend = context.config.get("backend", {})
        security = SecurityHooksIR(
            identity=backend.get("identity_middleware_import") or backend.get("auth_dependency_import"),
            row_predicates=tuple(str(item) for item in backend.get("global_predicate_hooks") or []),
            entity_row_predicates=tuple(
                (str(name), tuple(str(item) for item in hooks))
                for name, hooks in sorted((backend.get("entity_predicate_hooks") or {}).items())
            ),
            field_visibility=backend.get("field_visibility_hook_import"),
        )
        respect_soft_delete = bool(context.config.get("scan", {}).get("respect_soft_delete", False))
        entities = tuple(
            replace(
                entity,
                soft_delete=replace(
                    entity.soft_delete,
                    respected=respect_soft_delete and entity.soft_delete.field is not None,
                ),
            )
            for entity in ir.entities
        )
        resolved = replace(ir, entities=entities, security=security)
        validate_ir(resolved)
        return resolved

    def _check_java(self, java: str, cwd: Path, timeout: float) -> None:
        result = self._run(
            (java, "-version"),
            cwd=cwd,
            timeout=timeout,
            timeout_code="JPA_JAVA_TIMEOUT",
            timeout_message="Java version detection timed out.",
        )
        output = (result.stderr + "\n" + result.stdout).strip()
        if result.returncode != 0:
            raise ScannerError(
                "JPA_JAVA_INVALID",
                f"'{java} -version' failed. Install JDK {_MINIMUM_JAVA_VERSION}+ or set scan.jpa.java_command.",
                context={"exit_code": result.returncode, "output": output},
            )
        match = re.search(r'version\s+"(?P<version>\d+)(?:\.(?P<minor>\d+))?', output)
        if not match:
            match = re.search(r"(?:openjdk|java)\s+(?P<version>\d+)", output, re.IGNORECASE)
        if not match:
            raise ScannerError(
                "JPA_JAVA_VERSION_UNKNOWN",
                "FilterX could not determine the Java version. Set scan.jpa.java_command to a JDK executable that supports source-file launch mode.",
                context={"output": output},
            )
        major = int(match.group("version"))
        if major == 1 and match.groupdict().get("minor"):
            major = int(match.group("minor"))
        if major < _MINIMUM_JAVA_VERSION:
            raise ScannerError(
                "JPA_JAVA_VERSION_UNSUPPORTED",
                f"The FilterX JPA helper requires JDK {_MINIMUM_JAVA_VERSION}+; detected Java {major}.",
                context={"detected_major": major, "required_major": _MINIMUM_JAVA_VERSION},
            )

    def _check_helper_version(self, java: str, helper: Path, expected: str, cwd: Path, timeout: float) -> None:
        result = self._run(
            (java, str(helper), "--filterx-helper-version"),
            cwd=cwd,
            timeout=timeout,
            timeout_code="JPA_HELPER_TIMEOUT",
            timeout_message="JPA helper version check timed out.",
        )
        if result.returncode != 0:
            raise ScannerError(
                "JPA_HELPER_INVALID",
                "The bundled JPA helper source could not be launched. Use a full JDK 17+ installation, not a JRE.",
                context={"exit_code": result.returncode, "stderr": result.stderr.strip()},
            )
        try:
            document = json.loads(result.stdout)
            helper_version = str(document["helper_version"])
            protocol_version = str(document["protocol_version"])
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ScannerError(
                "JPA_HELPER_INVALID",
                "The JPA helper version response is invalid. Reinstall FilterX.",
                context={"stdout": result.stdout[-1000:]},
            ) from exc
        if helper_version != expected or protocol_version != IR_VERSION:
            raise ScannerError(
                "JPA_HELPER_VERSION_MISMATCH",
                "The JPA helper artifact is incompatible with the installed FilterX package. Reinstall FilterX so both artifacts come from the same release.",
                context={
                    "helper_version": helper_version,
                    "package_version": expected,
                    "helper_protocol": protocol_version,
                    "required_protocol": IR_VERSION,
                },
            )

    def _compile_and_classpath(
        self,
        context: ScannerContext,
        tool: JPABuildTool,
        module_root: Path,
        timeout: float,
    ) -> tuple[Path, str]:
        state_dir = module_root / ".filterx"
        state_dir.mkdir(parents=True, exist_ok=True)
        classpath_file = state_dir / "jpa-runtime-classpath.txt"
        classpath_file.unlink(missing_ok=True)
        compile_command, classpath_command = self.build_commands(context, tool, classpath_file)
        compile_result = self._run(
            compile_command,
            cwd=module_root,
            timeout=timeout,
            timeout_code="JPA_COMPILE_TIMEOUT",
            timeout_message=f"{tool.kind.title()} compilation exceeded the configured timeout.",
        )
        if compile_result.returncode != 0:
            raise ScannerError(
                "JPA_COMPILATION_FAILED",
                "The host project could not be compiled before JPA reflection. Fix its pre-existing compile errors and rerun FilterX.",
                context={
                    "build_tool": tool.kind,
                    "command": list(compile_command),
                    "exit_code": compile_result.returncode,
                    "stdout": compile_result.stdout[-4000:],
                    "stderr": compile_result.stderr[-4000:],
                },
            )

        try:
            if tool.kind == "maven":
                classpath_result = self._run(
                    classpath_command,
                    cwd=module_root,
                    timeout=timeout,
                    timeout_code="JPA_CLASSPATH_TIMEOUT",
                    timeout_message="Maven runtime classpath resolution timed out.",
                )
                if classpath_result.returncode != 0 or not classpath_file.is_file():
                    raise ScannerError(
                        "JPA_CLASSPATH_FAILED",
                        "Maven compiled the project but could not resolve its runtime classpath. Ensure the Maven dependency plugin can run (offline builds may need a populated cache).",
                        context={
                            "command": list(classpath_command),
                            "exit_code": classpath_result.returncode,
                            "stderr": classpath_result.stderr[-4000:],
                        },
                    )
                classes_dir = module_root / "target/classes"
                dependencies = classpath_file.read_text(encoding="utf-8").strip()
                classpath = os.pathsep.join(item for item in (str(classes_dir), dependencies) if item)
                return classes_dir, classpath

            return self._gradle_classpath(context, tool, module_root, timeout)
        finally:
            classpath_file.unlink(missing_ok=True)
            try:
                state_dir.rmdir()
            except OSError:
                pass

    def _gradle_classpath(
        self,
        context: ScannerContext,
        tool: JPABuildTool,
        module_root: Path,
        timeout: float,
    ) -> tuple[Path, str]:
        escaped_module = str(module_root).replace("\\", "\\\\").replace('"', '\\"')
        init_script = f"""
gradle.projectsEvaluated {{
    def selected = gradle.rootProject.allprojects.find {{
        it.projectDir.canonicalFile == new File("{escaped_module}").canonicalFile
    }}
    if (selected == null) {{
        throw new GradleException("FilterX could not find the configured module in this Gradle build")
    }}
    gradle.rootProject.tasks.register("filterxPrintRuntimeClasspath") {{
        doLast {{
            def sourceSets = selected.extensions.findByName("sourceSets")
            if (sourceSets == null) {{
                throw new GradleException("FilterX requires the Java plugin in the selected module")
            }}
            println("FILTERX_CLASSPATH=" + sourceSets.main.runtimeClasspath.asPath)
            println("FILTERX_CLASSES=" + sourceSets.main.output.classesDirs.files.sort().join(File.pathSeparator))
        }}
    }}
}}
""".strip()
        path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".gradle", delete=False) as handle:
                handle.write(init_script + "\n")
                path = Path(handle.name)
            extra = tuple(str(item) for item in self._settings(context).get("gradle_args", []))
            command = (tool.command, *extra, "--init-script", str(path), "filterxPrintRuntimeClasspath", "--quiet", "--no-daemon")
            result = self._run(
                command,
                cwd=module_root,
                timeout=timeout,
                timeout_code="JPA_CLASSPATH_TIMEOUT",
                timeout_message="Gradle runtime classpath resolution timed out.",
            )
            if result.returncode != 0:
                raise ScannerError(
                    "JPA_CLASSPATH_FAILED",
                    "Gradle compiled the project but could not expose the selected module's Java runtime classpath.",
                    context={"command": list(command), "exit_code": result.returncode, "stderr": result.stderr[-4000:]},
                )
            values = {}
            for line in result.stdout.splitlines():
                if line.startswith("FILTERX_CLASSPATH="):
                    values["classpath"] = line.split("=", 1)[1]
                elif line.startswith("FILTERX_CLASSES="):
                    values["classes"] = line.split("=", 1)[1]
            if not values.get("classpath") or not values.get("classes"):
                raise ScannerError(
                    "JPA_CLASSPATH_FAILED",
                    "Gradle did not return FilterX runtime classpath markers. Select the Java entity module with scan.jpa.module_path.",
                    context={"stdout": result.stdout[-4000:]},
                )
            classes_dir = Path(values["classes"].split(os.pathsep)[0])
            return classes_dir, values["classpath"]
        finally:
            if path is not None:
                path.unlink(missing_ok=True)

    def _run(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        timeout: float,
        timeout_code: str,
        timeout_message: str,
    ) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                tuple(command),
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except FileNotFoundError as exc:
            executable = str(command[0])
            java_command = "-version" in command or any(str(item).endswith(".java") for item in command)
            code = "JPA_JAVA_MISSING" if java_command else "JPA_BUILD_TOOL_MISSING"
            message = (
                f"Java was not found at '{executable}'. Install JDK {_MINIMUM_JAVA_VERSION}+ or set scan.jpa.java_command."
                if code == "JPA_JAVA_MISSING"
                else f"Build command '{executable}' was not found. Add a Maven/Gradle wrapper or install the selected build tool."
            )
            raise ScannerError(code, message, context={"command": executable}) from exc
        except subprocess.TimeoutExpired as exc:
            raise ScannerError(timeout_code, timeout_message, context={"timeout_seconds": timeout, "command": list(command)}) from exc


def _package_version() -> str:
    try:
        return metadata.version("filterx-cli")
    except metadata.PackageNotFoundError:
        return _FALLBACK_PACKAGE_VERSION
