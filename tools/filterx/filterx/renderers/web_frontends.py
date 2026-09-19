from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from filterx.core.config import load_effective_config
from filterx.core.frontend_lifecycle import (
    customization_root,
    finish_frontend_install,
    presentation_operations,
    schema_from_ir,
)
from filterx.core.io import load_json
from filterx.core.ir import FilterxIR, from_legacy_scan, ir_from_dict
from filterx.core.patcher import PatchOp, list_patch_bundles, rollback_patch_bundle

from .base import RendererTarget


@dataclass(frozen=True)
class WebTarget:
    name: str
    config_key: str
    generated_root: str
    package_requirements: Mapping[str, str]
    dev_requirements: Mapping[str, str]


REACT_VITE = WebTarget(
    "react-vite", "react_vite", "src/filterx-generated",
    {"react": "^19.0.0", "react-dom": "^19.0.0"},
    {"@types/react": "^19.0.0", "@types/react-dom": "^19.0.0", "@vitejs/plugin-react": "^4.3.0", "typescript": "^5.7.0", "vite": "^6.0.0"},
)
NEXTJS = WebTarget(
    "nextjs", "nextjs", "src/filterx-generated",
    {"next": "^15.0.0", "react": "^19.0.0", "react-dom": "^19.0.0"},
    {"@types/node": "^22.0.0", "@types/react": "^19.0.0", "@types/react-dom": "^19.0.0", "typescript": "^5.7.0"},
)
VUE = WebTarget(
    "vue", "vue", "src/filterx-generated",
    {"vue": "^3.5.0"},
    {"@vitejs/plugin-vue": "^5.2.0", "typescript": "^5.7.0", "vite": "^6.0.0", "vue-tsc": "^2.2.0"},
)

_TEMPLATES = Path(__file__).resolve().parents[1] / "reference_runtime" / "web_frontends"
REACT_COMPONENT = (_TEMPLATES / "FilterxApp.tsx").read_text(encoding="utf-8")
VUE_COMPONENT = (_TEMPLATES / "FilterxApp.vue").read_text(encoding="utf-8")
VUE_BUILDER = (_TEMPLATES / "FilterxFilterBuilder.vue").read_text(encoding="utf-8")
CSS = (_TEMPLATES / "filterx.css").read_text(encoding="utf-8")
CONTRACTS = (_TEMPLATES / "contracts.ts").read_text(encoding="utf-8")
DISPLAY = (_TEMPLATES / "display.ts").read_text(encoding="utf-8")


def _dry_run(args: Any, cfg: Mapping[str, Any]) -> bool:
    value = getattr(args, "dry_run", None)
    return bool(cfg["safety"].get("dry_run_default", True) if value is None else value)


def _target_config(cfg: Mapping[str, Any], target: WebTarget) -> dict[str, Any]:
    frontend = cfg["frontend"]
    configured = frontend.get(target.config_key, {})
    if not isinstance(configured, dict):
        configured = {}
    default_host = "src/app/filterx/page.tsx" if target is NEXTJS else "src/App.vue" if target is VUE else "src/App.tsx"
    return {
        "workspace_root": str(configured.get("workspace_root", frontend.get("workspace_root", "frontend"))),
        "generated_root": str(configured.get("generated_root", target.generated_root)),
        "host_file": str(configured.get("host_file", default_host)),
        "host_anchor": str(configured.get("host_anchor", "<!-- FILTERX:APP -->" if target is VUE else "// FILTERX:APP")),
        "api_base_url": str(configured.get("api_base_url", "/api/filterx")),
    }


def _load_ir(project_root: Path, cfg: Mapping[str, Any]) -> FilterxIR:
    ir_path = project_root / cfg["output"].get("ir_file", ".filterx/ir.json")
    scan_path = project_root / cfg["output"]["scan_file"]
    framework = str(cfg.get("scan", {}).get("framework", "sqlalchemy")).strip().lower()
    # SQLAlchemy does not emit IR by default. A later canonical scan must not be
    # shadowed by an IR left by --emit-ir or by a different backend scanner.
    if framework == "sqlalchemy" and scan_path.exists():
        if not ir_path.exists() or scan_path.stat().st_mtime_ns >= ir_path.stat().st_mtime_ns:
            return from_legacy_scan(load_json(scan_path), cfg)
        payload = load_json(ir_path)
        if payload.get("source_framework") != framework:
            return from_legacy_scan(load_json(scan_path), cfg)
        return ir_from_dict(payload)
    if ir_path.exists():
        ir = ir_from_dict(load_json(ir_path))
        # Preserve IR-only integrations with the historical default scanner.
        # Explicit non-SQLAlchemy scanners require their own lossless IR, never
        # the legacy scan adapter (which would discard security/type details).
        if framework != "sqlalchemy" and ir.source_framework != framework:
            raise ValueError(f"IR source '{ir.source_framework}' does not match scan.framework '{framework}'. Run 'filterx scan' again.")
        if framework != "sqlalchemy" and scan_path.exists() and scan_path.stat().st_mtime_ns > ir_path.stat().st_mtime_ns:
            raise ValueError("The scan is newer than its IR. Run 'filterx scan' again before frontend install.")
        return ir
    if framework != "sqlalchemy" and scan_path.exists():
        raise ValueError(f"Missing IR for scan.framework '{framework}'. Run 'filterx scan' again; a legacy scan alone is insufficient.")
    raise ValueError("Run 'filterx scan' before frontend install; no IR or scan artifact was found.")


def _slug(value: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", value).replace("_", "-")
    return value.lower()


def _ts_type(field_type: str, enum_values: tuple[str, ...]) -> str:
    if enum_values:
        return " | ".join(json.dumps(item) for item in enum_values)
    if field_type in {"integer", "decimal"}:
        return "number"
    if field_type == "boolean":
        return "boolean"
    if field_type == "json/blob":
        return "unknown"
    return "string"


def _render_types(ir: FilterxIR) -> str:
    entities: list[str] = []
    for entity in ir.entities:
        fields = []
        for field in entity.fields:
            optional = "?" if field.nullable else ""
            null = " | null" if field.nullable else ""
            fields.append(f"  {field.name}{optional}: {_ts_type(field.type.value, field.enum_values)}{null};")
        entities.append(f"export interface {entity.name} {{\n" + "\n".join(fields) + "\n}")
    return "export * from './contracts';\n\n" + "\n\n".join(entities) + "\n"


def _render_entities(ir: FilterxIR) -> str:
    values = []
    for entity in ir.entities:
        payload = {
            "name": entity.name,
            "table": entity.identity.table,
            "route": _slug(entity.identity.table or entity.name),
            "fields": [
                {"name": field.name, "type": field.type.value, "nullable": field.nullable,
                 "operations": list(field.operations), "enumValues": list(field.enum_values)}
                for field in entity.fields
            ],
            "relationships": [
                {"name": rel.name, "target": rel.target_entity, "collection": rel.collection}
                for rel in entity.relationships
            ],
        }
        values.append(json.dumps(payload, separators=(",", ":")))
    return "import type { EntityConfig } from './contracts';\n\nexport const FILTERX_ENTITIES: EntityConfig[] = [\n  " + ",\n  ".join(values) + "\n];\n"


def _render_api(api_base: str) -> str:
    return f"""import type {{ FilterNode, GroupBucket, QueryResponse, QueryState }} from './contracts';
export type {{ QueryState }} from './contracts';
const API_BASE = {json.dumps(api_base)};

async function checked<T>(response: Response): Promise<T> {{
  if (!response.ok) {{
    const payload = await response.json().catch(() => ({{ error: {{ message: response.statusText }} }}));
    throw new Error(payload?.error?.message ?? `FilterX request failed (${{response.status}})`);
  }}
  return response.json() as Promise<T>;
}}

export async function queryEntity<T>(route: string, state: QueryState): Promise<QueryResponse<T>> {{
  const query = new URLSearchParams({{ page: String(state.page), size: String(state.size) }});
  if (state.search) query.set('search', state.search);
  if (state.sortBy) {{ query.set('sort_by', state.sortBy); query.set('order', state.order); }}
  if (state.filterTree) return checked(await fetch(`${{API_BASE}}/${{route}}/filter?${{query}}`, {{ method: 'POST', headers: {{ 'content-type': 'application/json' }}, body: JSON.stringify({{ filter_tree: state.filterTree }}) }}));
  return checked(await fetch(`${{API_BASE}}/${{route}}?${{query}}`));
}}

export async function groupEntity(route: string, field: string, filterTree?: FilterNode): Promise<GroupBucket[]> {{
  if (filterTree) return checked(await fetch(`${{API_BASE}}/${{route}}/group-by/${{field}}/filter`, {{ method: 'POST', headers: {{ 'content-type': 'application/json' }}, body: JSON.stringify({{ filter_tree: filterTree }}) }}));
  return checked(await fetch(`${{API_BASE}}/${{route}}/group-by/${{field}}`));
}}

export async function exportEntity(route: string, format: 'csv' | 'xlsx' | 'json', state: QueryState): Promise<void> {{
    const query = new URLSearchParams({{ format, sort_by: state.sortBy, order: state.order }});
  if (state.search) query.set('search', state.search);
    const response = await fetch(`${{API_BASE}}/${{route}}/export?${{query}}`, {{ method: 'POST', headers: {{ 'content-type': 'application/json' }}, body: JSON.stringify({{ filter_tree: state.filterTree ?? null }}) }});
  if (!response.ok) await checked(response);
  const blob = await response.blob();
  const href = URL.createObjectURL(blob); const link = document.createElement('a');
  link.href = href; link.download = `${{route}}.${{format}}`; link.click(); URL.revokeObjectURL(href);
}}
"""


def _relative_import(source: str, destination: str) -> str:
    """Module specifier relative to a host/wrapper, not to a fixed src layout."""
    relative = os.path.relpath(destination, start=os.path.dirname(source)).replace("\\", "/")
    return relative if relative.startswith(".") else f"./{relative}"


def _read_host(path: Path) -> str:
    # Preserve the user's line endings when migrating only a single import.
    with path.open(encoding="utf-8", newline="") as stream:
        return stream.read()


def _patch_host(project_root: Path, workspace: str, host_file: str, anchor: str, target: WebTarget,
                *, generated_root: str | None = None, custom_root: str | None = None) -> PatchOp | None:
    rel = f"{workspace.rstrip('/')}/{host_file.lstrip('/')}"
    path = project_root / rel
    if not path.exists():
        return None
    content = original = _read_host(path)
    root = generated_root or f"{workspace}/src/filterx-generated"
    custom = custom_root or f"{workspace}/src/filterx-custom"
    extension = ".vue" if target is VUE else ""
    shell = _relative_import(rel, f"{custom}/FilterxShell{extension}")
    # Keep the local FilterxApp binding: preserve all host markup, props and edits.
    import_line = (f"import FilterxApp from '{shell}';" if target is VUE
                   else f"import {{ FilterxShell as FilterxApp }} from '{shell}';")
    legacy_paths = {_relative_import(rel, f"{root}/FilterxApp{extension}"),
                    "./filterx-generated/FilterxApp.vue" if target is VUE else "./filterx-generated/FilterxApp"}
    if target is NEXTJS:
        legacy_paths.add("../../filterx-generated/FilterxApp")
    for legacy_path in legacy_paths:
        legacy = (f"import FilterxApp from '{legacy_path}';" if target is VUE
                  else f"import {{ FilterxApp }} from '{legacy_path}';")
        content = re.sub(r"(?m)^" + re.escape(legacy) + r"(?=\r?$)", lambda _: import_line, content)
    if target is not NEXTJS and anchor and anchor in content:
        newline = "\r\n" if "\r\n" in content else "\n"
        if import_line not in content:
            if target is REACT_VITE:
                content = import_line + newline + content
            elif "<script setup" in content and "</script>" in content:
                content = content.replace("</script>", f"{import_line}{newline}</script>", 1)
            else:
                content = f'<script setup lang="ts">{newline}{import_line}{newline}</script>{newline}' + content
        content = content.replace(anchor, "<FilterxApp />")
    if content == original:
        return None
    return PatchOp(kind="generated_file", path=rel, owner="host", content=content,
                   description=f"Mount user-owned {target.name} FilterX shell")


def _operations(project_root: Path, cfg: Mapping[str, Any], ir: FilterxIR, target: WebTarget) -> tuple[list[PatchOp], dict[str, Any]]:
    settings = _target_config(cfg, target)
    workspace = settings["workspace_root"].replace("\\", "/").rstrip("/")
    generated = settings["generated_root"].replace("\\", "/").strip("/")
    root = f"{workspace}/{generated}"
    custom = customization_root(cfg, target.name).replace("\\", "/").rstrip("/")
    package = f"{workspace}/package.json"
    if not (project_root / package).exists():
        raise ValueError(f"{target.name} package manifest not found: {project_root / package}")
    files = {"contracts.ts": CONTRACTS, "types.ts": _render_types(ir), "entities.ts": _render_entities(ir),
             "api.ts": _render_api(settings["api_base_url"]), "display.ts": DISPLAY, "filterx.css": CSS}
    client = "'use client';\n" if target is NEXTJS else ""
    extension = ".vue" if target is VUE else ".tsx"
    if target is VUE:
        files["FilterxApp.vue"] = VUE_COMPONENT
        files["FilterxFilterBuilder.vue"] = VUE_BUILDER
        files["index.ts"] = "export { default as FilterxApp } from './FilterxApp.vue';\nexport * from './types';\nexport * from './entities';\n"
    else:
        files["FilterxApp.tsx"] = client + REACT_COMPONENT
        files["index.ts"] = "export * from './FilterxApp';\nexport * from './types';\nexport * from './entities';\n"
    operations = [PatchOp(kind="generated_file", path=f"{root}/{name}", content=content,
                          metadata={"layer": "schema" if name in {"types.ts", "entities.ts"} else "runtime"})
                  for name, content in files.items()]
    shell_path = f"{custom}/FilterxShell{extension}"
    app_import = _relative_import(shell_path, f"{root}/FilterxApp" + (".vue" if target is VUE else ""))
    if target is VUE:
        contracts_import = _relative_import(shell_path, f"{root}/contracts")
        shell = (f'<script setup lang="ts">\nimport FilterxApp from {json.dumps(app_import)};\n'
                 f"import type {{ FilterxContext, FilterxCellContext }} from {json.dumps(contracts_import)};\n"
                 "import './theme.css';\n"
                 "defineSlots<{ header?(props: FilterxContext): unknown; toolbar?(props: FilterxContext): unknown; cell?(props: FilterxCellContext): unknown }>();\n</script>\n"
                 "<!-- User-owned: customize header/toolbar/cell slots here. -->\n"
                 "<template><FilterxApp>\n"
                 '  <template v-if="$slots.header" #header="context"><slot name="header" v-bind="context" /></template>\n'
                 '  <template v-if="$slots.toolbar" #toolbar="context"><slot name="toolbar" v-bind="context" /></template>\n'
                 '  <template v-if="$slots.cell" #cell="context"><slot name="cell" v-bind="context" /></template>\n'
                 "</FilterxApp></template>\n")
    else:
        shell = (client + f"import {{ FilterxApp, type FilterxAppProps }} from {json.dumps(app_import)};\n"
                 "import './theme.css';\n\n// User-owned: customize renderHeader, renderToolbar and renderCell here.\n"
                 "export function FilterxShell(props: FilterxAppProps) { return <FilterxApp {...props} />; }\n")
    operations.extend([
        PatchOp(kind="generated_file", path=shell_path, content=shell, owner="host", write_policy="create_once", metadata={"layer": "custom"}),
        PatchOp(kind="generated_file", path=f"{custom}/theme.css", content="/* User-owned FilterX theme. Override .fx-* styles here. */\n", owner="host", write_policy="create_once", metadata={"layer": "custom"}),
    ])
    operations.extend(presentation_operations(project_root, cfg, target.name, schema_from_ir(ir)))
    installed_package = load_json(project_root / package)
    # The host selects framework versions. Reconcile missing dependencies only;
    # upgrades must not downgrade or replace a version deliberately chosen there.
    missing_dependencies = {name: version for name, version in target.package_requirements.items()
                            if name not in installed_package.get("dependencies", {})}
    missing_dev_dependencies = {name: version for name, version in target.dev_requirements.items()
                                if name not in installed_package.get("devDependencies", {})}
    operations.append(PatchOp(kind="structured_merge", path=package, owner="host", structured_format="json",
                              merge={"dependencies": missing_dependencies, "devDependencies": missing_dev_dependencies}))
    host = _patch_host(project_root, workspace, settings["host_file"], settings["host_anchor"], target, generated_root=root, custom_root=custom)
    if host:
        operations.append(host)
    if target is NEXTJS and not host:
        page_path = f"{workspace}/{settings['host_file'].lstrip('/')}"
        shell_import = _relative_import(page_path, f"{custom}/FilterxShell")
        operations.append(PatchOp(kind="generated_file", path=page_path,
                                  content=f"import {{ FilterxShell }} from {json.dumps(shell_import)};\nexport default function FilterxPage() {{ return <FilterxShell />; }}\n",
                                  owner="host", write_policy="create_once", metadata={"layer": "custom"}))
    host_path = f"{workspace}/{settings['host_file'].lstrip('/')}"
    warnings = []
    if not host and (target is not NEXTJS or (project_root / host_path).exists()):
        source = _read_host(project_root / host_path) if (project_root / host_path).exists() else ""
        shell_import = _relative_import(host_path, f"{custom}/FilterxShell" + (".vue" if target is VUE else ""))
        if shell_import not in source:
            warnings.append({"code": "FRONTEND_HOST_NOT_MOUNTED", "path": host_path,
                             "message": f"Host file is missing or has no recognized FilterX mount. Import {shell_import} manually"
                             + (f" or add {settings['host_anchor']} in the host template." if target is not NEXTJS and settings["host_anchor"] else "; the existing page was preserved.")})
    return operations, {**settings, "root": root, "workspace": workspace, "custom_root": custom, "warnings": warnings}


class WebFrontendRenderer:
    version = "1.0.0"
    target = RendererTarget.FRONTEND

    def __init__(self, web_target: WebTarget) -> None:
        self.web_target = web_target
        self.name = web_target.name

    def install(self, args: Any) -> int:
        project_root = Path(args.project_root).resolve()
        cfg = load_effective_config(project_root, Path(args.config).resolve() if args.config else None).raw
        if not cfg["frontend"].get("enabled", True):
            print(json.dumps({"skipped": True, "reason": "frontend disabled in config"}, indent=2) if getattr(args, "json", False) else "FilterX frontend install skipped: frontend.enabled is false.")
            return 0
        try:
            ir = _load_ir(project_root, cfg)
            operations, settings = _operations(project_root, cfg, ir, self.web_target)
        except ValueError as exc:
            payload = {"errors": [{"code": "FRONTEND_TARGET_INVALID", "message": str(exc)}]}
            print(json.dumps(payload, indent=2) if getattr(args, "json", False) else str(exc))
            return 2
        payload = {"framework": self.name, "generated_root": settings["root"], "entity_count": len(ir.entities)}
        if settings["warnings"]:
            payload["warnings"] = settings["warnings"]
        return finish_frontend_install(args, cfg, operations, schema_from_ir(ir), payload)

    def validate(self, args: Any) -> int:
        project_root = Path(args.project_root).resolve()
        cfg = load_effective_config(project_root, Path(args.config).resolve() if args.config else None).raw
        settings = _target_config(cfg, self.web_target)
        root = project_root / settings["workspace_root"] / settings["generated_root"]
        required = ["contracts.ts", "types.ts", "entities.ts", "presentation.ts", "display.ts", "api.ts", "filterx.css", "FilterxApp.vue" if self.web_target is VUE else "FilterxApp.tsx"]
        if self.web_target is VUE:
            required.append("FilterxFilterBuilder.vue")
        errors = [{"code": "FRONTEND_GENERATED_FILE_MISSING", "path": str(root / name)} for name in required if not (root / name).exists()]
        custom = project_root / customization_root(cfg, self.name)
        for name in ("FilterxShell.vue" if self.web_target is VUE else "FilterxShell.tsx", "theme.css", "presentation.json"):
            if not (custom / name).exists():
                errors.append({"code": "FRONTEND_CUSTOM_FILE_MISSING", "path": str(custom / name)})
        package = project_root / settings["workspace_root"] / "package.json"
        if not package.exists():
            errors.append({"code": "FRONTEND_PACKAGE_JSON_MISSING", "path": str(package)})
        else:
            dependencies = load_json(package).get("dependencies", {})
            for dependency in self.web_target.package_requirements:
                if dependency not in dependencies:
                    errors.append({"code": "FRONTEND_DEPENDENCY_MISSING", "dependency": dependency})
            dev_dependencies = load_json(package).get("devDependencies", {})
            for dependency in self.web_target.dev_requirements:
                if dependency not in dev_dependencies:
                    errors.append({"code": "FRONTEND_DEPENDENCY_MISSING", "dependency": dependency})
        payload = {"framework": self.name, "errors": errors, "warnings": [], "error_count": len(errors), "warning_count": 0}
        print(json.dumps(payload, indent=2) if getattr(args, "json", False) else f"FilterX {self.name} validation: {len(errors)} errors.")
        return 4 if errors else 0

    def remove(self, args: Any) -> int:
        project_root = Path(args.project_root).resolve()
        cfg = load_effective_config(project_root, Path(args.config).resolve() if args.config else None).raw
        patch_dir = project_root / cfg["output"]["patch_dir"]
        candidates = []
        for patch_id in list_patch_bundles(patch_dir):
            meta = patch_dir / patch_id / "meta.json"
            if meta.exists() and load_json(meta).get("description") == f"frontend.install.{self.name}":
                candidates.append(patch_id)
        if not candidates:
            print(f"No {self.name} frontend install patch bundles available for rollback.")
            return 2
        patch_id = getattr(args, "patch_id", None) or candidates[-1]
        if _dry_run(args, cfg) or bool(getattr(args, "check", False)):
            print(json.dumps({"dry_run": True, "would_rollback_patch_id": patch_id}, indent=2) if getattr(args, "json", False) else f"Would roll back {patch_id}.")
            return 0
        result = rollback_patch_bundle(project_root, patch_dir, patch_id)
        print(json.dumps({"patch_id": patch_id, **result}, indent=2) if getattr(args, "json", False) else f"FilterX {self.name} frontend removed.")
        return 0


class ReactViteRenderer(WebFrontendRenderer):
    def __init__(self) -> None:
        super().__init__(REACT_VITE)


class NextjsRenderer(WebFrontendRenderer):
    def __init__(self) -> None:
        super().__init__(NEXTJS)


class VueRenderer(WebFrontendRenderer):
    def __init__(self) -> None:
        super().__init__(VUE)
