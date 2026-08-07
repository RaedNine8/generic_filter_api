from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from filterx.core.config import load_effective_config
from filterx.core.io import load_json
from filterx.core.ir import FilterxIR, from_legacy_scan, ir_from_dict
from filterx.core.patcher import PatchOp, apply_patch_operations, list_patch_bundles, rollback_patch_bundle

from .base import RendererTarget


@dataclass(frozen=True)
class WebTarget:
    name: str
    config_key: str
    generated_root: str
    package_requirements: Mapping[str, str]
    dev_requirements: Mapping[str, str]


REACT_VITE = WebTarget(
    "react-vite",
    "react_vite",
    "src/filterx-generated",
    {"react": "^19.0.0", "react-dom": "^19.0.0"},
    {"@types/react": "^19.0.0", "@types/react-dom": "^19.0.0", "@vitejs/plugin-react": "^4.3.0", "typescript": "^5.7.0", "vite": "^6.0.0"},
)
NEXTJS = WebTarget(
    "nextjs",
    "nextjs",
    "src/filterx-generated",
    {"next": "^15.0.0", "react": "^19.0.0", "react-dom": "^19.0.0"},
    {"@types/node": "^22.0.0", "@types/react": "^19.0.0", "@types/react-dom": "^19.0.0", "typescript": "^5.7.0"},
)
VUE = WebTarget(
    "vue",
    "vue",
    "src/filterx-generated",
    {"vue": "^3.5.0"},
    {"@vitejs/plugin-vue": "^5.2.0", "typescript": "^5.7.0", "vite": "^6.0.0", "vue-tsc": "^2.2.0"},
)


def _dry_run(args: Any, cfg: Mapping[str, Any]) -> bool:
    value = getattr(args, "dry_run", None)
    return bool(cfg["safety"].get("dry_run_default", True) if value is None else value)


def _target_config(cfg: Mapping[str, Any], target: WebTarget) -> dict[str, Any]:
    frontend = cfg["frontend"]
    configured = frontend.get(target.config_key, {})
    if not isinstance(configured, dict):
        configured = {}
    return {
        "workspace_root": str(configured.get("workspace_root", frontend.get("workspace_root", "frontend"))),
        "generated_root": str(configured.get("generated_root", target.generated_root)),
        "host_file": str(configured.get("host_file", "src/App.tsx" if target is REACT_VITE else "src/App.vue")),
        "host_anchor": str(configured.get("host_anchor", "// FILTERX:APP")),
        "api_base_url": str(configured.get("api_base_url", "/api/filterx")),
    }


def _load_ir(project_root: Path, cfg: Mapping[str, Any]) -> FilterxIR:
    ir_path = project_root / ".filterx/ir.json"
    if ir_path.exists():
        return ir_from_dict(load_json(ir_path))
    scan_path = project_root / cfg["output"]["scan_file"]
    if not scan_path.exists():
        raise ValueError("Run 'filterx scan' before frontend install; no IR or scan artifact was found.")
    return from_legacy_scan(load_json(scan_path), cfg)


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
    return """export type FilterOperator = 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'like' | 'ilike' | 'starts_with' | 'ends_with' | 'in' | 'not_in' | 'between' | 'is_null' | 'is_not_null';
export type FilterNode = FilterCondition | FilterGroup;
export interface FilterCondition { node_type: 'condition'; field: string; operation: FilterOperator; value?: unknown }
export interface FilterGroup { node_type: 'group'; operator: 'AND' | 'OR'; children: FilterNode[] }
export interface QueryMeta { page: number; size: number; total_items: number; total_pages: number }
export interface QueryResponse<T> { data: T[]; meta: QueryMeta }
export interface GroupBucket { key: unknown; count: number }
export interface FieldConfig { name: string; type: string; nullable: boolean; operations: FilterOperator[]; enumValues: string[] }
export interface EntityConfig { name: string; table: string; route: string; fields: FieldConfig[]; relationships: { name: string; target: string; collection: boolean }[] }

""" + "\n\n".join(entities) + "\n"


def _render_entities(ir: FilterxIR) -> str:
    values = []
    for entity in ir.entities:
        payload = {
            "name": entity.name,
            "table": entity.identity.table,
            "route": _slug(entity.identity.table or entity.name),
            "fields": [
                {
                    "name": field.name,
                    "type": field.type.value,
                    "nullable": field.nullable,
                    "operations": list(field.operations),
                    "enumValues": list(field.enum_values),
                }
                for field in entity.fields
            ],
            "relationships": [
                {"name": rel.name, "target": rel.target_entity, "collection": rel.collection}
                for rel in entity.relationships
            ],
        }
        values.append(json.dumps(payload, separators=(",", ":")))
    return "import type { EntityConfig } from './types';\n\nexport const FILTERX_ENTITIES: EntityConfig[] = [\n  " + ",\n  ".join(values) + "\n];\n"


def _render_api(api_base: str) -> str:
    return f"""import type {{ FilterNode, GroupBucket, QueryResponse }} from './types';

export interface QueryState {{ page: number; size: number; search: string; sortBy: string; order: 'asc' | 'desc'; filterTree?: FilterNode }}
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


REACT_COMPONENT = r'''import { useCallback, useEffect, useMemo, useState } from 'react';
import { exportEntity, groupEntity, queryEntity, type QueryState } from './api';
import { FILTERX_ENTITIES } from './entities';
import type { EntityConfig, FilterCondition, FilterGroup, FilterNode, FilterOperator, GroupBucket, QueryResponse } from './types';
import './filterx.css';

const OPS: FilterOperator[] = ['eq','ne','gt','gte','lt','lte','like','ilike','starts_with','ends_with','in','not_in','between','is_null','is_not_null'];
const emptyCondition = (field = ''): FilterCondition => ({ node_type: 'condition', field, operation: 'eq', value: '' });
const emptyGroup = (): FilterGroup => ({ node_type: 'group', operator: 'AND', children: [] });

function FilterBuilder({ entity, value, onChange }: { entity: EntityConfig; value: FilterGroup; onChange: (next: FilterGroup) => void }) {
  const update = (index: number, node: FilterNode) => onChange({ ...value, children: value.children.map((item, i) => i === index ? node : item) });
  return <div className="fx-builder"><div className="fx-builder-head"><strong>Custom filters</strong><select value={value.operator} onChange={event => onChange({ ...value, operator: event.target.value as 'AND' | 'OR' })}><option>AND</option><option>OR</option></select><button onClick={() => onChange({ ...value, children: [...value.children, emptyCondition(entity.fields[0]?.name)] })}>+ condition</button><button onClick={() => onChange({ ...value, children: [...value.children, emptyGroup()] })}>+ group</button></div>{value.children.map((node, index) => node.node_type === 'group' ? <div className="fx-nested" key={index}><FilterBuilder entity={entity} value={node} onChange={next => update(index, next)} /></div> : <div className="fx-condition" key={index}><select value={node.field} onChange={event => update(index, { ...node, field: event.target.value })}>{entity.fields.map(field => <option key={field.name}>{field.name}</option>)}</select><select value={node.operation} onChange={event => update(index, { ...node, operation: event.target.value as FilterOperator })}>{OPS.map(op => <option key={op}>{op}</option>)}</select>{!['is_null','is_not_null'].includes(node.operation) && <input value={String(node.value ?? '')} onChange={event => update(index, { ...node, value: ['in','not_in','between'].includes(node.operation) ? event.target.value.split(',').map(v => v.trim()) : event.target.value })} />}<button aria-label="Remove filter" onClick={() => onChange({ ...value, children: value.children.filter((_, i) => i !== index) })}>×</button></div>)}</div>;
}

export function FilterxEntityPage({ entity }: { entity: EntityConfig }) {
  const [state, setState] = useState<QueryState>({ page: 1, size: 20, search: '', sortBy: entity.fields[0]?.name ?? '', order: 'asc' });
  const [draft, setDraft] = useState<FilterGroup>(emptyGroup());
  const [result, setResult] = useState<QueryResponse<Record<string, unknown>>>({ data: [], meta: { page: 1, size: 20, total_items: 0, total_pages: 0 } });
  const [groupField, setGroupField] = useState(''); const [groups, setGroups] = useState<GroupBucket[]>([]); const [error, setError] = useState('');
  const load = useCallback(() => queryEntity<Record<string, unknown>>(entity.route, state).then(setResult).catch(error => setError(String(error))), [entity.route, state]);
  useEffect(() => { void load(); }, [load]);
  const visible = useMemo(() => entity.fields.filter(field => result.data.some(row => Object.prototype.hasOwnProperty.call(row, field.name))), [entity.fields, result.data]);
  const sort = (field: string) => setState(old => ({ ...old, page: 1, sortBy: field, order: old.sortBy === field && old.order === 'asc' ? 'desc' : 'asc' }));
  const apply = () => setState(old => ({ ...old, page: 1, filterTree: draft.children.length ? draft : undefined }));
  const group = async () => { if (groupField) setGroups(await groupEntity(entity.route, groupField, state.filterTree)); };
  return <main className="fx-shell"><header><div><span className="fx-kicker">FilterX explorer</span><h1>{entity.name}</h1><p>Filter, search, sort, group, paginate, and export live data.</p></div><div className="fx-export"><button onClick={() => exportEntity(entity.route, 'csv', state)}>CSV</button><button onClick={() => exportEntity(entity.route, 'xlsx', state)}>Excel</button><button onClick={() => exportEntity(entity.route, 'json', state)}>JSON</button></div></header><section className="fx-toolbar"><input aria-label="Search" placeholder="Search…" value={state.search} onChange={event => setState(old => ({ ...old, page: 1, search: event.target.value }))} /><select value={groupField} onChange={event => setGroupField(event.target.value)}><option value="">Group by…</option>{entity.fields.map(field => <option key={field.name}>{field.name}</option>)}</select><button disabled={!groupField} onClick={group}>Group</button></section><FilterBuilder entity={entity} value={draft} onChange={setDraft} /><div className="fx-actions"><button className="fx-primary" onClick={apply}>Apply filters</button><button onClick={() => { setDraft(emptyGroup()); setState(old => ({ ...old, page: 1, filterTree: undefined })); }}>Clear</button></div>{error && <p className="fx-error">{error}</p>}{groups.length > 0 && <section className="fx-groups">{groups.map((bucket, index) => <article key={index}><strong>{String(bucket.key ?? 'Null')}</strong><span>{bucket.count}</span></article>)}</section>}<div className="fx-table-wrap"><table><thead><tr>{visible.map(field => <th key={field.name}><button onClick={() => sort(field.name)}>{field.name}{state.sortBy === field.name ? (state.order === 'asc' ? ' ↑' : ' ↓') : ''}</button></th>)}</tr></thead><tbody>{result.data.map((row, index) => <tr key={index}>{visible.map(field => <td key={field.name}>{typeof row[field.name] === 'object' ? JSON.stringify(row[field.name]) : String(row[field.name] ?? '')}</td>)}</tr>)}</tbody></table></div><footer className="fx-pagination"><span>{result.meta.total_items} results</span><button disabled={state.page <= 1} onClick={() => setState(old => ({ ...old, page: old.page - 1 }))}>Previous</button><span>Page {result.meta.page} / {Math.max(1, result.meta.total_pages)}</span><button disabled={state.page >= result.meta.total_pages} onClick={() => setState(old => ({ ...old, page: old.page + 1 }))}>Next</button><select value={state.size} onChange={event => setState(old => ({ ...old, page: 1, size: Number(event.target.value) }))}><option>10</option><option>20</option><option>50</option></select></footer></main>;
}

export function FilterxApp() { const [route, setRoute] = useState(FILTERX_ENTITIES[0]?.route ?? ''); const entity = FILTERX_ENTITIES.find(item => item.route === route) ?? FILTERX_ENTITIES[0]; if (!entity) return <p>No FilterX entities were generated.</p>; return <><nav className="fx-nav"><strong>FilterX</strong>{FILTERX_ENTITIES.map(item => <button className={item.route === route ? 'active' : ''} key={item.route} onClick={() => setRoute(item.route)}>{item.name}</button>)}</nav><FilterxEntityPage entity={entity} /></>; }
'''


CSS = """:root{font-family:Inter,ui-sans-serif,system-ui;color:#172033;background:#f4f7fb}.fx-nav{display:flex;gap:.5rem;align-items:center;padding:1rem 4vw;background:#101828;color:white}.fx-nav strong{margin-right:auto}.fx-nav button,.fx-export button,.fx-toolbar button,.fx-actions button,.fx-pagination button,.fx-builder button{border:1px solid #d0d5dd;border-radius:.6rem;padding:.55rem .8rem;background:white;cursor:pointer}.fx-nav button{background:#1d2939;color:white;border-color:#344054}.fx-nav .active,.fx-primary{background:#6d5ce7!important;color:white!important}.fx-shell{max-width:1280px;margin:auto;padding:2rem 4vw}.fx-shell header{display:flex;justify-content:space-between;gap:2rem;align-items:end}.fx-kicker{color:#6d5ce7;font-weight:700;text-transform:uppercase;font-size:.75rem}.fx-shell h1{font-size:2.4rem;margin:.25rem 0}.fx-export,.fx-toolbar,.fx-actions,.fx-builder-head,.fx-condition,.fx-pagination{display:flex;gap:.6rem;align-items:center;flex-wrap:wrap}.fx-toolbar,.fx-builder,.fx-groups,.fx-table-wrap{background:white;border:1px solid #e4e7ec;border-radius:1rem;padding:1rem;margin-top:1rem;box-shadow:0 8px 24px #1018280b}.fx-toolbar input{flex:1}.fx-toolbar input,.fx-toolbar select,.fx-condition input,.fx-condition select,.fx-builder select,.fx-pagination select{padding:.6rem;border:1px solid #d0d5dd;border-radius:.5rem}.fx-condition{margin-top:.7rem}.fx-nested{border-left:3px solid #d6d1fa;padding-left:1rem}.fx-actions{margin-top:1rem}.fx-table-wrap{overflow:auto;padding:0}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:.85rem;border-bottom:1px solid #eaecf0;white-space:nowrap}th button{border:0;background:none;font-weight:700;cursor:pointer}.fx-pagination{justify-content:flex-end;margin-top:1rem}.fx-pagination span:first-child{margin-right:auto}.fx-groups{display:flex;gap:1rem}.fx-groups article{display:flex;gap:2rem;padding:.8rem 1rem;border-radius:.7rem;background:#f7f5ff}.fx-error{color:#b42318}@media(max-width:700px){.fx-shell header{align-items:start;flex-direction:column}.fx-condition>*{width:100%}}"""


VUE_BUILDER = r'''<script setup lang="ts">
import type { EntityConfig, FilterCondition, FilterGroup, FilterNode, FilterOperator } from './types';
const props=defineProps<{entity:EntityConfig;modelValue:FilterGroup}>(); const emit=defineEmits<{(event:'update:modelValue',value:FilterGroup):void}>();
const operations:FilterOperator[]=['eq','ne','gt','gte','lt','lte','like','ilike','starts_with','ends_with','in','not_in','between','is_null','is_not_null'];
function changed(children:FilterNode[]){emit('update:modelValue',{...props.modelValue,children})} function update(index:number,node:FilterNode){changed(props.modelValue.children.map((item,i)=>i===index?node:item))}
function condition():FilterCondition{return{node_type:'condition',field:props.entity.fields[0]?.name??'',operation:'eq',value:''}} function group():FilterGroup{return{node_type:'group',operator:'AND',children:[]}}
</script>
<template><section class="fx-builder"><div class="fx-builder-head"><strong>Custom filters</strong><select :value="modelValue.operator" @change="emit('update:modelValue',{...modelValue,operator:($event.target as HTMLSelectElement).value as 'AND'|'OR'})"><option>AND</option><option>OR</option></select><button @click="changed([...modelValue.children,condition()])">+ condition</button><button @click="changed([...modelValue.children,group()])">+ group</button></div><template v-for="(node,index) in modelValue.children" :key="index"><FilterxFilterBuilder v-if="node.node_type==='group'" class="fx-nested" :entity="entity" :model-value="node" @update:model-value="next=>update(index,next)"/><div v-else class="fx-condition"><select :value="node.field" @change="update(index,{...node,field:($event.target as HTMLSelectElement).value})"><option v-for="field in entity.fields" :key="field.name">{{field.name}}</option></select><select :value="node.operation" @change="update(index,{...node,operation:($event.target as HTMLSelectElement).value as FilterOperator})"><option v-for="op in operations" :key="op">{{op}}</option></select><input v-if="!['is_null','is_not_null'].includes(node.operation)" :value="String(node.value??'')" @input="update(index,{...node,value:($event.target as HTMLInputElement).value})"><button @click="changed(modelValue.children.filter((_,i)=>i!==index))">×</button></div></template></section></template>
'''


VUE_COMPONENT = r'''<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { exportEntity, groupEntity, queryEntity, type QueryState } from './api';
import { FILTERX_ENTITIES } from './entities';
import FilterxFilterBuilder from './FilterxFilterBuilder.vue';
import type { FilterGroup, GroupBucket, QueryResponse } from './types';
import './filterx.css';
const route=ref(FILTERX_ENTITIES[0]?.route??''); const entity=computed(()=>FILTERX_ENTITIES.find(item=>item.route===route.value)??FILTERX_ENTITIES[0]);
const state=ref<QueryState>({page:1,size:20,search:'',sortBy:entity.value?.fields[0]?.name??'',order:'asc'}); const filters=ref<FilterGroup>({node_type:'group',operator:'AND',children:[]});
const result=ref<QueryResponse<Record<string,unknown>>>({data:[],meta:{page:1,size:20,total_items:0,total_pages:0}}); const groupField=ref(''); const groups=ref<GroupBucket[]>([]); const error=ref('');
const visible=computed(()=>entity.value?.fields.filter(field=>result.value.data.some(row=>Object.prototype.hasOwnProperty.call(row,field.name)))??[]);
async function load(){if(!entity.value)return;try{result.value=await queryEntity(entity.value.route,state.value)}catch(caught){error.value=String(caught)}}
function sort(field:string){state.value={...state.value,page:1,sortBy:field,order:state.value.sortBy===field&&state.value.order==='asc'?'desc':'asc'}}
async function group(){if(entity.value&&groupField.value)groups.value=await groupEntity(entity.value.route,groupField.value,state.value.filterTree)}
watch([route,state],load,{deep:true}); onMounted(load);
</script>
<template><nav class="fx-nav"><strong>FilterX</strong><button v-for="item in FILTERX_ENTITIES" :key="item.route" :class="{active:item.route===route}" @click="route=item.route">{{item.name}}</button></nav><main v-if="entity" class="fx-shell"><header><div><span class="fx-kicker">FilterX explorer</span><h1>{{entity.name}}</h1><p>Filter, search, sort, group, paginate, and export live data.</p></div><div class="fx-export"><button v-for="format in ['csv','xlsx','json'] as const" :key="format" @click="exportEntity(entity.route,format,state)">{{format.toUpperCase()}}</button></div></header><section class="fx-toolbar"><input v-model="state.search" aria-label="Search" placeholder="Search…"><select v-model="groupField"><option value="">Group by…</option><option v-for="field in entity.fields" :key="field.name">{{field.name}}</option></select><button :disabled="!groupField" @click="group">Group</button></section><FilterxFilterBuilder v-model="filters" :entity="entity"/><div class="fx-actions"><button class="fx-primary" @click="state={...state,page:1,filterTree:filters.children.length?filters:undefined}">Apply filters</button><button @click="filters={node_type:'group',operator:'AND',children:[]};state={...state,page:1,filterTree:undefined}">Clear</button></div><p v-if="error" class="fx-error">{{error}}</p><section v-if="groups.length" class="fx-groups"><article v-for="(bucket,index) in groups" :key="index"><strong>{{String(bucket.key??'Null')}}</strong><span>{{bucket.count}}</span></article></section><div class="fx-table-wrap"><table><thead><tr><th v-for="field in visible" :key="field.name"><button @click="sort(field.name)">{{field.name}}{{state.sortBy===field.name?(state.order==='asc'?' ↑':' ↓'):''}}</button></th></tr></thead><tbody><tr v-for="(row,index) in result.data" :key="index"><td v-for="field in visible" :key="field.name">{{typeof row[field.name]==='object'?JSON.stringify(row[field.name]):String(row[field.name]??'')}}</td></tr></tbody></table></div><footer class="fx-pagination"><span>{{result.meta.total_items}} results</span><button :disabled="state.page<=1" @click="state={...state,page:state.page-1}">Previous</button><span>Page {{result.meta.page}} / {{Math.max(1,result.meta.total_pages)}}</span><button :disabled="state.page>=result.meta.total_pages" @click="state={...state,page:state.page+1}">Next</button><select v-model.number="state.size"><option>10</option><option>20</option><option>50</option></select></footer></main></template>
'''


def _patch_host(project_root: Path, workspace: str, host_file: str, anchor: str, target: WebTarget) -> PatchOp | None:
    rel = f"{workspace.rstrip('/')}/{host_file.lstrip('/')}"
    path = project_root / rel
    if not path.exists() or target is NEXTJS:
        return None
    content = path.read_text(encoding="utf-8")
    if anchor not in content:
        return None
    if target is REACT_VITE:
        import_line = "import { FilterxApp } from './filterx-generated/FilterxApp';"
        if import_line not in content:
            content = import_line + "\n" + content
        content = content.replace(anchor, "<FilterxApp />")
    else:
        import_line = "import FilterxApp from './filterx-generated/FilterxApp.vue';"
        if import_line not in content:
            if "<script setup" in content and "</script>" in content:
                content = content.replace("</script>", f"{import_line}\n</script>", 1)
            else:
                content = f"<script setup lang=\"ts\">\n{import_line}\n</script>\n" + content
        content = content.replace(anchor, "<FilterxApp />")
    return PatchOp(kind="generated_file", path=rel, owner="host", content=content, description=f"Mount generated {target.name} FilterX application")


def _operations(project_root: Path, cfg: Mapping[str, Any], ir: FilterxIR, target: WebTarget) -> tuple[list[PatchOp], dict[str, Any]]:
    settings = _target_config(cfg, target)
    workspace = settings["workspace_root"].rstrip("/")
    root = f"{workspace}/{settings['generated_root'].strip('/')}"
    package = f"{workspace}/package.json"
    if not (project_root / package).exists():
        raise ValueError(f"{target.name} package manifest not found: {project_root / package}")
    files = {
        "types.ts": _render_types(ir),
        "entities.ts": _render_entities(ir),
        "api.ts": _render_api(settings["api_base_url"]),
        "filterx.css": CSS,
    }
    if target is REACT_VITE or target is NEXTJS:
        files["FilterxApp.tsx"] = ("'use client';\n" if target is NEXTJS else "") + REACT_COMPONENT
        files["index.ts"] = "export * from './FilterxApp';\nexport * from './types';\nexport * from './entities';\n"
    else:
        files["FilterxApp.vue"] = VUE_COMPONENT
        files["FilterxFilterBuilder.vue"] = VUE_BUILDER
        files["index.ts"] = "export { default as FilterxApp } from './FilterxApp.vue';\nexport * from './types';\nexport * from './entities';\n"
    operations = [PatchOp(kind="generated_file", path=f"{root}/{name}", content=content) for name, content in files.items()]
    operations.append(PatchOp(kind="structured_merge", path=package, owner="host", structured_format="json", merge={"dependencies": dict(target.package_requirements), "devDependencies": dict(target.dev_requirements)}))
    host = _patch_host(project_root, workspace, settings["host_file"], settings["host_anchor"], target)
    if host:
        operations.append(host)
    if target is NEXTJS:
        operations.append(PatchOp(kind="generated_file", path=f"{workspace}/src/app/filterx/page.tsx", content="import { FilterxApp } from '../../filterx-generated/FilterxApp';\nexport default function FilterxPage(){ return <FilterxApp />; }\n"))
    return operations, {**settings, "root": root, "workspace": workspace}


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
        result = apply_patch_operations(project_root=project_root, operations=operations, manifest_path=project_root / cfg["safety"]["idempotency_manifest"], patch_dir=project_root / cfg["output"]["patch_dir"], dry_run=_dry_run(args, cfg), check_mode=bool(getattr(args, "check", False)), strict_conflict_mode=bool(cfg["safety"].get("strict_conflict_mode", True)), description=f"frontend.install.{self.name}")
        payload = {"framework": self.name, "dry_run": result.dry_run, "patch_id": result.patch_id, "generated_root": settings["root"], "entity_count": len(ir.entities), "touched_files": result.touched_files, "issues": [{"code": issue.code, "message": issue.message, "context": issue.context} for issue in result.issues]}
        print(json.dumps(payload, indent=2) if getattr(args, "json", False) else f"FilterX {self.name} frontend install completed.")
        return 3 if result.has_conflicts else 0

    def validate(self, args: Any) -> int:
        project_root = Path(args.project_root).resolve()
        cfg = load_effective_config(project_root, Path(args.config).resolve() if args.config else None).raw
        settings = _target_config(cfg, self.web_target)
        root = project_root / settings["workspace_root"] / settings["generated_root"]
        required = ["types.ts", "entities.ts", "api.ts", "filterx.css", "FilterxApp.vue" if self.web_target is VUE else "FilterxApp.tsx"]
        errors = [{"code": "FRONTEND_GENERATED_FILE_MISSING", "path": str(root / name)} for name in required if not (root / name).exists()]
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
