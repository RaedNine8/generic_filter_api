from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from filterx.core.config import load_effective_config
from filterx.core.io import load_json
from filterx.core.patcher import (
    PatchOp,
    apply_patch_operations,
    list_patch_bundles,
    rollback_patch_bundle,
)


GENERATED_ROUTES_RE = re.compile(
    r"\n?// FILTERX GENERATED ROUTES START\n.*?// FILTERX GENERATED ROUTES END\n?",
    re.DOTALL,
)

REFERENCE_RUNTIME_FILES = [
    "core/index.ts",
    "core/enums/index.ts",
    "core/enums/filter-operation.enum.ts",
    "core/enums/sort-order.enum.ts",
    "core/interfaces/index.ts",
    "core/interfaces/entity-config.interface.ts",
    "core/interfaces/field-config.interface.ts",
    "core/interfaces/filter.interface.ts",
    "core/interfaces/filter-tree.interface.ts",
    "core/interfaces/pagination.interface.ts",
    "core/interfaces/query-state.interface.ts",
    "core/interfaces/saved-filter.interface.ts",
    "core/services/index.ts",
    "core/services/entity-query.service.ts",
    "core/services/filter-state-manager.service.ts",
    "core/services/generic-query.service.ts",
    "core/services/saved-filter.service.ts",
    "shared/index.ts",
    "shared/components/index.ts",
    "shared/components/advanced-search-panel/advanced-search-panel.component.html",
    "shared/components/advanced-search-panel/advanced-search-panel.component.scss",
    "shared/components/advanced-search-panel/advanced-search-panel.component.ts",
    "shared/components/data-table/data-table.component.html",
    "shared/components/data-table/data-table.component.scss",
    "shared/components/data-table/data-table.component.ts",
    "shared/components/entity-list/entity-list.component.ts",
    "shared/components/filter-builder/filter-builder.component.html",
    "shared/components/filter-builder/filter-builder.component.scss",
    "shared/components/filter-builder/filter-builder.component.ts",
    "shared/components/pagination/pagination.component.html",
    "shared/components/pagination/pagination.component.scss",
    "shared/components/pagination/pagination.component.ts",
    "shared/components/search-box/search-box.component.html",
    "shared/components/search-box/search-box.component.scss",
    "shared/components/search-box/search-box.component.ts",
    "shared/components/sort-header/sort-header.component.ts",
]


def _resolve_dry_run(args: Any, cfg: dict[str, Any]) -> bool:
    dry_run = getattr(args, "dry_run", None)
    if dry_run is None:
        return bool(cfg["safety"].get("dry_run_default", True))
    return bool(dry_run)


def _csv_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _to_snake(value: str) -> str:
    out = []
    for idx, char in enumerate(value):
        if char.isupper() and idx > 0 and (value[idx - 1].islower() or (idx + 1 < len(value) and value[idx + 1].islower())):
            out.append("_")
        out.append(char.lower())
    return "".join(out).replace("__", "_")


def _to_kebab(value: str) -> str:
    return _to_snake(value).replace("_", "-")


def _to_camel(value: str) -> str:
    snake = _to_snake(value)
    parts = [p for p in snake.split("_") if p]
    if not parts:
        return ""
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


def _styled_name(value: str, style: str) -> str:
    if style == "snake":
        return _to_snake(value)
    if style == "camel":
        return _to_camel(value)
    return _to_kebab(value)


def _to_pascal(value: str) -> str:
    normalized = _to_snake(value)
    return "".join(part.capitalize() for part in normalized.split("_") if part)


def _ts_field_type(field_type: str) -> str:
    if field_type in {"integer", "float"}:
        return "number"
    if field_type == "boolean":
        return "boolean"
    return "string"


def _ui_field_type(field_type: str) -> str:
    if field_type in {"integer", "float"}:
        return "number"
    if field_type == "boolean":
        return "boolean"
    if field_type in {"date", "datetime"}:
        return "date"
    return "text"


def _singularize(value: str) -> str:
        lowered = value.strip().lower().replace("-", "_")
        if lowered.endswith("ies") and len(lowered) > 3:
                return lowered[:-3] + "y"
        if lowered.endswith("s") and len(lowered) > 1:
                return lowered[:-1]
        return lowered


def _entity_route_path(entity: dict[str, Any], style: str) -> str:
        table_name = str(entity.get("table") or "").replace("_", "-").strip("/")
        if table_name:
                return table_name
        return f"{_styled_name(str(entity.get('model', 'entity')), style)}s"


def _render_filterx_models_ts() -> str:
        return r'''export type FilterOperator =
    | 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte'
    | 'like' | 'ilike' | 'starts_with' | 'ends_with'
    | 'in' | 'not_in' | 'is_null' | 'is_not_null' | 'between';

export type FilterFieldType = 'string' | 'number' | 'boolean' | 'date' | 'datetime' | 'enum';

export interface EntityFieldMetadata {
    name: string;
    type: string;
    nullable?: boolean;
    ops?: FilterOperator[];
    is_fk?: boolean;
}

export interface EntityRelationshipMetadata {
    name: string;
    related_model: string;
    related_table?: string;
    cardinality?: string;
    display_field?: string;
    uselist?: boolean;
    related_fields?: Array<{ name: string; type: string; ops?: FilterOperator[] }>;
}

export interface EntityMetadata {
    model: string;
    table: string;
    fields: EntityFieldMetadata[];
    relationships: EntityRelationshipMetadata[];
}

export interface MetadataResponse {
    entities: EntityMetadata[];
    entity_count: number;
}

export interface QueryMeta {
    page: number;
    size: number;
    total_items: number;
    total_pages: number;
}

export interface QueryResponse<T = Record<string, unknown>> {
    data: T[];
    meta: QueryMeta;
}

export interface GroupBucket {
    key: unknown;
    count: number;
}

export interface FilterFieldOption {
    path: string;
    label: string;
    type: FilterFieldType;
    operations: FilterOperator[];
}

export interface FilterTreeGroup {
    id: string;
    kind: 'group';
    operator: 'AND' | 'OR';
    children: FilterTreeNode[];
}

export interface FilterTreeCondition {
    id: string;
    kind: 'condition';
    field: string;
    operation: FilterOperator;
    value: unknown;
}

export type FilterTreeNode = FilterTreeGroup | FilterTreeCondition;

export const FILTER_OPERATION_DEFINITIONS: Record<FilterOperator, { label: string; requiresValue: boolean; multiValue?: boolean; rangeValue?: boolean }> = {
    eq: { label: 'Equals', requiresValue: true },
    ne: { label: 'Not equal', requiresValue: true },
    gt: { label: 'Greater than', requiresValue: true },
    gte: { label: 'Greater or equal', requiresValue: true },
    lt: { label: 'Less than', requiresValue: true },
    lte: { label: 'Less or equal', requiresValue: true },
    like: { label: 'Contains', requiresValue: true },
    ilike: { label: 'Contains, case-insensitive', requiresValue: true },
    starts_with: { label: 'Starts with', requiresValue: true },
    ends_with: { label: 'Ends with', requiresValue: true },
    in: { label: 'In list', requiresValue: true, multiValue: true },
    not_in: { label: 'Not in list', requiresValue: true, multiValue: true },
    is_null: { label: 'Is null', requiresValue: false },
    is_not_null: { label: 'Is not null', requiresValue: false },
    between: { label: 'Between', requiresValue: true, rangeValue: true },
};

let nextTreeId = 1;

export function createTreeId(): string {
    const id = nextTreeId;
    nextTreeId += 1;
    return `fx-node-${id}`;
}

export function humanize(value: string): string {
    return value.replace(/[._-]+/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

export function singularize(value: string): string {
    const lowered = value.trim().toLowerCase().replace(/-/g, '_');
    if (lowered.endsWith('ies') && lowered.length > 3) return `${lowered.slice(0, -3)}y`;
    if (lowered.endsWith('s') && lowered.length > 1) return lowered.slice(0, -1);
    return lowered;
}

export function entityKeys(entity: EntityMetadata): string[] {
    const values = [entity.model, entity.table]
        .map((value) => value.toLowerCase())
        .flatMap((value) => [value, value.replace(/_/g, '-'), singularize(value), singularize(value).replace(/_/g, '-')]);
    return [...new Set(values.filter((value) => value.length > 0))];
}

export function normalizeFieldType(value: string): FilterFieldType {
    switch (value) {
        case 'integer':
        case 'float':
        case 'decimal':
        case 'number':
            return 'number';
        case 'boolean':
            return 'boolean';
        case 'date':
            return 'date';
        case 'datetime':
            return 'datetime';
        case 'enum':
            return 'enum';
        default:
            return 'string';
    }
}

export function createConditionNode(field = '', operation: FilterOperator = 'eq', value: unknown = ''): FilterTreeCondition {
    return { id: createTreeId(), kind: 'condition', field, operation, value };
}

export function createGroupNode(operator: 'AND' | 'OR' = 'AND', children: FilterTreeNode[] = []): FilterTreeGroup {
    return { id: createTreeId(), kind: 'group', operator, children };
}

export function toBackendTree(node: FilterTreeNode | null): Record<string, unknown> | null {
    if (!node) return null;
    if (node.kind === 'condition') {
        const definition = FILTER_OPERATION_DEFINITIONS[node.operation];
        const value = node.value;
        if (definition.requiresValue) {
            if (value === null || value === undefined || value === '') return null;
            if (Array.isArray(value) && value.length === 0) return null;
        }
        return { node_type: 'condition', field: node.field, operation: node.operation, value };
    }
    const children = node.children.map((child) => toBackendTree(child)).filter((child): child is Record<string, unknown> => !!child);
    if (children.length === 0) return null;
    return { node_type: 'operator', operator: node.operator, children };
}
'''


def _render_filterx_explorer_component_ts() -> str:
        return r'''import { CommonModule } from '@angular/common';
import { HttpClient, HttpClientModule, HttpParams } from '@angular/common/http';
import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';

import {
    EntityMetadata,
    FILTER_OPERATION_DEFINITIONS,
    FilterFieldOption,
    FilterOperator,
    FilterTreeCondition,
    FilterTreeGroup,
    FilterTreeNode,
    GroupBucket,
    MetadataResponse,
    QueryMeta,
    QueryResponse,
    createConditionNode,
    createGroupNode,
    entityKeys,
    humanize,
    normalizeFieldType,
    toBackendTree,
} from './filterx.models';

@Component({
    selector: 'filterx-generated-explorer',
    standalone: true,
    imports: [CommonModule, FormsModule, HttpClientModule],
    templateUrl: './filterx-explorer.component.html',
    styleUrl: './filterx-explorer.component.css',
})
export class FilterxGeneratedExplorerComponent implements OnInit, OnDestroy {
    private readonly http = inject(HttpClient);
    private readonly route = inject(ActivatedRoute);
    private readonly destroy$ = new Subject<void>();

    protected readonly operationDefinitions = FILTER_OPERATION_DEFINITIONS;
    protected readonly operationKeys = Object.keys(FILTER_OPERATION_DEFINITIONS) as FilterOperator[];

    protected entitySlug = 'entities';
    protected pageTitle = 'FilterX';
    protected metadata: EntityMetadata | null = null;
    protected fieldOptions: FilterFieldOption[] = [];
    protected visibleColumns: FilterFieldOption[] = [];
    protected rows: Array<Record<string, unknown>> = [];
    protected groupedBuckets: GroupBucket[] = [];
    protected pagination: QueryMeta | null = null;
    protected loading = false;
    protected metadataLoading = false;
    protected errorMessage = '';
    protected search = '';
    protected sortBy = '';
    protected sortOrder: 'asc' | 'desc' = 'asc';
    protected groupBy = '';
    protected page = 1;
    protected pageSize = 20;
    protected pageSizeOptions = [10, 20, 50, 100];
    protected filterRoot: FilterTreeGroup = createGroupNode('AND', []);

    ngOnInit(): void {
        this.route.data.pipe(takeUntil(this.destroy$)).subscribe((data) => {
            this.entitySlug = String(data['entity'] || 'entities');
            this.pageTitle = String(data['title'] || humanize(this.entitySlug));
            this.page = 1;
            this.groupedBuckets = [];
            this.resetTree();
            this.loadMetadataAndData();
        });
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    protected loadMetadataAndData(): void {
        this.metadataLoading = true;
        this.errorMessage = '';
        this.http.get<MetadataResponse>('/api/filterx/metadata').pipe(takeUntil(this.destroy$)).subscribe({
            next: (response) => {
                this.metadata = this.findEntityMetadata(response.entities, this.entitySlug);
                if (!this.metadata) {
                    this.rows = [];
                    this.pagination = null;
                    this.fieldOptions = [];
                    this.visibleColumns = [];
                    this.errorMessage = `FilterX metadata did not include an entity for "${this.entitySlug}".`;
                    this.metadataLoading = false;
                    return;
                }
                this.fieldOptions = this.buildFieldOptions(this.metadata);
                this.visibleColumns = this.buildColumns(this.metadata, this.fieldOptions);
                this.sortBy = this.defaultSortField(this.metadata);
                this.metadataLoading = false;
                this.loadData();
            },
            error: (error) => {
                this.metadataLoading = false;
                this.rows = [];
                this.pagination = null;
                this.errorMessage = this.describeError(error, 'Could not load FilterX metadata. Is the backend running?');
            },
        });
    }

    protected loadData(): void {
        if (!this.metadata) return;
        const params = this.buildQueryParams();
        const treePayload = toBackendTree(this.filterRoot);
        const endpoint = `/api/filterx/${this.entitySlug}`;
        this.loading = true;
        this.errorMessage = '';
        const request$ = treePayload
            ? this.http.post<QueryResponse>(`${endpoint}/filter`, treePayload, { params })
            : this.http.get<QueryResponse>(`${endpoint}/query`, { params });
        request$.pipe(takeUntil(this.destroy$)).subscribe({
            next: (response) => {
                this.rows = response.data;
                this.pagination = response.meta;
                this.loading = false;
                this.loadGroupedData(treePayload);
            },
            error: (error) => {
                this.rows = [];
                this.pagination = null;
                this.groupedBuckets = [];
                this.loading = false;
                this.errorMessage = this.describeError(error, 'The FilterX query failed.');
            },
        });
    }

    protected runQuery(): void { this.page = 1; this.loadData(); }
    protected resetTree(): void { this.filterRoot = createGroupNode('AND', []); }
    protected resetAll(): void { this.search = ''; this.groupBy = ''; this.sortBy = this.defaultSortField(this.metadata); this.sortOrder = 'asc'; this.page = 1; this.pageSize = 20; this.resetTree(); this.loadData(); }
    protected addRootCondition(): void { this.filterRoot.children.push(this.createDefaultCondition()); }
    protected addCondition(group: FilterTreeGroup): void { group.children.push(this.createDefaultCondition()); }
    protected addGroup(group: FilterTreeGroup): void { group.children.push(createGroupNode('AND', [this.createDefaultCondition()])); }
    protected removeNode(parent: FilterTreeGroup | null, node: FilterTreeNode): void { if (parent) parent.children = parent.children.filter((child) => child.id !== node.id); }
    protected toggleGroupOperator(group: FilterTreeGroup): void { group.operator = group.operator === 'AND' ? 'OR' : 'AND'; }
    protected isGroup(node: FilterTreeNode): node is FilterTreeGroup { return node.kind === 'group'; }
    protected fieldOptionFor(path: string): FilterFieldOption | undefined { return this.fieldOptions.find((option) => option.path === path); }
    protected operationsFor(condition: FilterTreeCondition): FilterOperator[] { return this.fieldOptionFor(condition.field)?.operations || this.operationKeys; }
    protected needsValue(operation: FilterOperator): boolean { return FILTER_OPERATION_DEFINITIONS[operation].requiresValue; }
    protected isListOperation(operation: FilterOperator): boolean { return !!FILTER_OPERATION_DEFINITIONS[operation].multiValue; }
    protected isRangeOperation(operation: FilterOperator): boolean { return !!FILTER_OPERATION_DEFINITIONS[operation].rangeValue; }
    protected isBooleanField(condition: FilterTreeCondition): boolean { return this.fieldOptionFor(condition.field)?.type === 'boolean'; }

    protected onConditionFieldChange(condition: FilterTreeCondition): void {
        const option = this.fieldOptionFor(condition.field) || this.fieldOptions[0];
        if (!option) return;
        condition.field = option.path;
        if (!option.operations.includes(condition.operation)) condition.operation = option.operations[0] || 'eq';
        this.resetConditionValue(condition, option.type);
    }

    protected onConditionOperationChange(condition: FilterTreeCondition): void { this.resetConditionValue(condition, this.fieldOptionFor(condition.field)?.type || 'string'); }
    protected setSingleValue(condition: FilterTreeCondition, value: string): void { condition.value = this.coerceValue(value, this.fieldOptionFor(condition.field)?.type || 'string'); }
    protected setListValue(condition: FilterTreeCondition, value: string): void { condition.value = value.split(',').map((item) => item.trim()).filter(Boolean).map((item) => this.coerceValue(item, this.fieldOptionFor(condition.field)?.type || 'string')); }
    protected setRangeValue(condition: FilterTreeCondition, index: 0 | 1, value: string): void { const range = Array.isArray(condition.value) ? [...condition.value] : ['', '']; range[index] = this.coerceValue(value, this.fieldOptionFor(condition.field)?.type || 'string'); condition.value = range; }
    protected setBooleanValue(condition: FilterTreeCondition, value: string): void { condition.value = value === 'true' ? true : value === 'false' ? false : null; }
    protected getSingleValue(condition: FilterTreeCondition): string { return condition.value === null || condition.value === undefined ? '' : String(condition.value); }
    protected getListValue(condition: FilterTreeCondition): string { return Array.isArray(condition.value) ? condition.value.join(', ') : ''; }
    protected getRangeValue(condition: FilterTreeCondition, index: 0 | 1): string { return Array.isArray(condition.value) && condition.value[index] !== undefined ? String(condition.value[index] ?? '') : ''; }
    protected booleanValue(condition: FilterTreeCondition): string { return condition.value === true ? 'true' : condition.value === false ? 'false' : ''; }
    protected inputType(condition: FilterTreeCondition): string { const type = this.fieldOptionFor(condition.field)?.type || 'string'; return type === 'number' ? 'number' : type === 'date' ? 'date' : type === 'datetime' ? 'datetime-local' : 'text'; }
    protected goToPage(page: number): void { if (!this.pagination || page < 1 || page > this.pagination.total_pages || page === this.page) return; this.page = page; this.loadData(); }
    protected onPageSizeChange(): void { this.page = 1; this.loadData(); }
    protected onGroupByChange(): void { this.loadData(); }
    protected onSortFieldChange(field: string): void { this.sortBy = field; this.page = 1; this.loadData(); }
    protected toggleSort(field: string): void { this.sortOrder = this.sortBy === field && this.sortOrder === 'asc' ? 'desc' : 'asc'; this.sortBy = field; this.page = 1; this.loadData(); }
    protected trackByNodeId(index: number, node: FilterTreeNode): string { return node.id; }
    protected trackByColumn(index: number, column: FilterFieldOption): string { return column.path; }
    protected trackByPage(index: number, page: number): number { return page; }
    protected trackByBucket(index: number, bucket: GroupBucket): string { return `${index}-${String(bucket.key)}`; }

    protected displayValue(row: Record<string, unknown>, path: string): string {
        const raw = this.nestedValue(row, path);
        const option = this.fieldOptionFor(path);
        if (raw === null || raw === undefined || raw === '') return '—';
        if (option?.type === 'boolean') return raw === true ? 'Yes' : raw === false ? 'No' : '—';
        if (option?.type === 'date' || option?.type === 'datetime') {
            const parsed = new Date(String(raw));
            if (Number.isNaN(parsed.getTime())) return String(raw);
            return option.type === 'date' ? parsed.toLocaleDateString() : parsed.toLocaleString();
        }
        return String(raw);
    }

    protected pages(): number[] { return !this.pagination || this.pagination.total_pages <= 1 ? [] : Array.from({ length: this.pagination.total_pages }, (_, index) => index + 1); }

    private loadGroupedData(treePayload: Record<string, unknown> | null): void {
        if (!this.groupBy) { this.groupedBuckets = []; return; }
        const params = this.search.trim() ? new HttpParams().set('search', this.search.trim()) : new HttpParams();
        const encodedGroupField = encodeURIComponent(this.groupBy);
        const endpoint = `/api/filterx/${this.entitySlug}/group-by/${encodedGroupField}`;
        const request$ = treePayload ? this.http.post<GroupBucket[]>(`${endpoint}/filter`, treePayload, { params }) : this.http.get<GroupBucket[]>(endpoint, { params });
        request$.pipe(takeUntil(this.destroy$)).subscribe({ next: (buckets) => { this.groupedBuckets = buckets; }, error: () => { this.groupedBuckets = []; } });
    }

    private buildQueryParams(): HttpParams { let params = new HttpParams().set('page', String(this.page)).set('size', String(this.pageSize)).set('order', this.sortOrder); if (this.sortBy) params = params.set('sort_by', this.sortBy); if (this.search.trim()) params = params.set('search', this.search.trim()); return params; }
    private buildFieldOptions(entity: EntityMetadata): FilterFieldOption[] { const directFields = entity.fields.map((field) => ({ path: field.name, label: humanize(field.name), type: normalizeFieldType(field.type), operations: field.ops?.length ? field.ops : this.operationKeys })); const relationFields = entity.relationships.filter((relationship) => !relationship.uselist && relationship.cardinality !== 'o2m' && relationship.cardinality !== 'm2m').flatMap((relationship) => (relationship.related_fields || []).map((field) => ({ path: `${relationship.name}.${field.name}`, label: `${humanize(relationship.name)} ${humanize(field.name)}`, type: normalizeFieldType(field.type), operations: field.ops?.length ? field.ops : this.operationKeys }))); return [...directFields, ...relationFields]; }
    private buildColumns(entity: EntityMetadata, options: FilterFieldOption[]): FilterFieldOption[] { const direct = entity.fields.map((field) => options.find((option) => option.path === field.name)).filter((option): option is FilterFieldOption => !!option); const relationDisplays = entity.relationships.filter((relationship) => !relationship.uselist && relationship.display_field).map((relationship) => options.find((option) => option.path === `${relationship.name}.${relationship.display_field}`)).filter((option): option is FilterFieldOption => !!option); return [...direct, ...relationDisplays]; }
    private createDefaultCondition(): FilterTreeCondition { const defaultOption = this.fieldOptions[0]; const node = createConditionNode(defaultOption?.path || '', defaultOption?.operations[0] || 'eq'); this.resetConditionValue(node, defaultOption?.type || 'string'); return node; }
    private resetConditionValue(condition: FilterTreeCondition, type: FilterFieldOption['type']): void { if (this.isRangeOperation(condition.operation)) { condition.value = ['', '']; return; } if (this.isListOperation(condition.operation)) { condition.value = []; return; } if (!this.needsValue(condition.operation)) { condition.value = true; return; } condition.value = type === 'boolean' ? null : ''; }
    private findEntityMetadata(entities: EntityMetadata[], slug: string): EntityMetadata | null { const normalizedSlug = slug.toLowerCase().replace(/-/g, '_'); return entities.find((entity) => entityKeys(entity).includes(normalizedSlug) || entityKeys(entity).includes(slug.toLowerCase())) || null; }
    private defaultSortField(entity: EntityMetadata | null): string { if (!entity) return ''; return entity.fields.find((field) => field.name === 'id')?.name || entity.fields[0]?.name || ''; }
    private coerceValue(value: string, type: FilterFieldOption['type']): unknown { if (value === '') return ''; if (type === 'number') { const parsed = Number(value); return Number.isNaN(parsed) ? value : parsed; } if (type === 'boolean') return value === 'true' ? true : value === 'false' ? false : null; return value; }
    private nestedValue(row: Record<string, unknown>, path: string): unknown { return path.split('.').reduce<unknown>((current, key) => { if (!current || typeof current !== 'object') return undefined; return (current as Record<string, unknown>)[key]; }, row); }
    private describeError(error: unknown, fallback: string): string { if (error && typeof error === 'object') { const asRecord = error as Record<string, unknown>; const nestedError = asRecord['error']; if (nestedError && typeof nestedError === 'object') { const detail = (nestedError as Record<string, unknown>)['detail']; if (typeof detail === 'string' && detail.length > 0) return detail; } const message = asRecord['message']; if (typeof message === 'string' && message.length > 0) return message; } return fallback; }
}
'''


def _render_filterx_explorer_component_html() -> str:
        return r'''<div class="filterx-page">
    <section class="filterx-hero">
        <div>
            <p class="filterx-kicker">Generated FilterX UI</p>
            <h1>{{ pageTitle }}</h1>
            <p class="filterx-subtitle">Odoo-style search, nested AND/OR tree filters, grouping, sorting, and table paging against <strong>/api/filterx</strong>.</p>
        </div>
        <div class="filterx-hero-meta" *ngIf="metadata">
            <span>{{ metadata.model }}</span>
            <span>{{ metadata.table }}</span>
            <span>{{ metadata.fields.length }} fields</span>
            <span>{{ metadata.relationships.length }} relations</span>
        </div>
    </section>

    <section class="filterx-searchbar" *ngIf="metadata">
        <div class="filterx-search-shell">
            <span class="filterx-search-icon">⌕</span>
            <input type="text" [(ngModel)]="search" placeholder="Search records or use custom filters..." (keydown.enter)="runQuery()" />
            <button type="button" class="filterx-primary" (click)="runQuery()">Search</button>
        </div>
        <button type="button" class="filterx-secondary" (click)="resetAll()">Clear</button>
    </section>

    <section class="filterx-controls" *ngIf="metadata">
        <label><span>Sort by</span><select [ngModel]="sortBy" (ngModelChange)="onSortFieldChange($event)"><option *ngFor="let option of visibleColumns; trackBy: trackByColumn" [ngValue]="option.path">{{ option.label }}</option></select></label>
        <label><span>Order</span><select [(ngModel)]="sortOrder" (ngModelChange)="loadData()"><option value="asc">Ascending</option><option value="desc">Descending</option></select></label>
        <label><span>Group by</span><select [(ngModel)]="groupBy" (ngModelChange)="onGroupByChange()"><option value="">No grouping</option><option *ngFor="let option of visibleColumns; trackBy: trackByColumn" [ngValue]="option.path">{{ option.label }}</option></select></label>
        <label><span>Page size</span><select [(ngModel)]="pageSize" (ngModelChange)="onPageSizeChange()"><option *ngFor="let size of pageSizeOptions; trackBy: trackByPage" [ngValue]="size">{{ size }}</option></select></label>
    </section>

    <section class="filterx-panel" *ngIf="metadata">
        <div class="filterx-panel-header">
            <div><h2>Custom Filter Tree</h2><p>Create nested groups and relationship filters like <strong>company.name</strong>.</p></div>
            <div class="filterx-actions"><button type="button" class="filterx-secondary" (click)="addRootCondition()">Add condition</button><button type="button" class="filterx-secondary" (click)="addGroup(filterRoot)">Add group</button><button type="button" class="filterx-primary" (click)="runQuery()">Apply tree</button></div>
        </div>
        <ng-container *ngTemplateOutlet="treeNodeTemplate; context: { $implicit: filterRoot, parent: null }"></ng-container>
    </section>

    <section class="filterx-groups" *ngIf="groupBy && groupedBuckets.length > 0">
        <h2>Grouped Summary</h2>
        <div class="filterx-buckets"><span class="filterx-bucket" *ngFor="let bucket of groupedBuckets; trackBy: trackByBucket"><span>{{ bucket.key ?? 'None' }}</span><strong>{{ bucket.count }}</strong></span></div>
    </section>

    <section class="filterx-results">
        <div class="filterx-panel-header">
            <div><h2>Results</h2><p *ngIf="pagination">Page {{ pagination.page }} of {{ pagination.total_pages || 1 }} · {{ pagination.total_items }} rows</p></div>
            <span class="filterx-status" [class.loading]="loading || metadataLoading">{{ loading || metadataLoading ? 'Loading…' : 'Ready' }}</span>
        </div>
        <div class="filterx-error" *ngIf="errorMessage">{{ errorMessage }}</div>
        <div class="filterx-table-wrap" *ngIf="visibleColumns.length > 0"><table><thead><tr><th *ngFor="let column of visibleColumns; trackBy: trackByColumn"><button type="button" class="filterx-sort" (click)="toggleSort(column.path)">{{ column.label }} <span *ngIf="sortBy === column.path">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span></button></th></tr></thead><tbody><tr *ngIf="!loading && rows.length === 0"><td [attr.colspan]="visibleColumns.length">No rows match the current query.</td></tr><tr *ngFor="let row of rows"><td *ngFor="let column of visibleColumns; trackBy: trackByColumn">{{ displayValue(row, column.path) }}</td></tr></tbody></table></div>
        <div class="filterx-pagination" *ngIf="pagination && pagination.total_pages > 1"><button type="button" class="filterx-secondary" (click)="goToPage(page - 1)">Previous</button><button type="button" *ngFor="let pageNumber of pages(); trackBy: trackByPage" class="filterx-page-btn" [class.active]="pageNumber === page" (click)="goToPage(pageNumber)">{{ pageNumber }}</button><button type="button" class="filterx-secondary" (click)="goToPage(page + 1)">Next</button></div>
    </section>
</div>

<ng-template #treeNodeTemplate let-node let-parent="parent">
    <div class="filterx-tree-node" [class.group]="isGroup(node)">
        <ng-container *ngIf="isGroup(node); else conditionTemplate">
            <div class="filterx-group-card">
                <div class="filterx-group-head"><button type="button" class="filterx-operator" (click)="toggleGroupOperator(node)">{{ node.operator }}</button><div class="filterx-actions"><button type="button" class="filterx-link" (click)="addCondition(node)">Add condition</button><button type="button" class="filterx-link" (click)="addGroup(node)">Add group</button><button *ngIf="parent" type="button" class="filterx-link danger" (click)="removeNode(parent, node)">Remove group</button></div></div>
                <div class="filterx-empty" *ngIf="node.children.length === 0">No conditions yet. Add one to begin.</div>
                <div class="filterx-children" *ngIf="node.children.length > 0"><ng-container *ngFor="let child of node.children; trackBy: trackByNodeId"><ng-container *ngTemplateOutlet="treeNodeTemplate; context: { $implicit: child, parent: node }"></ng-container></ng-container></div>
            </div>
        </ng-container>
        <ng-template #conditionTemplate>
            <div class="filterx-condition-card">
                <div class="filterx-condition-grid">
                    <label><span>Field</span><select [(ngModel)]="node.field" (ngModelChange)="onConditionFieldChange(node)"><option *ngFor="let option of fieldOptions; trackBy: trackByColumn" [ngValue]="option.path">{{ option.label }}</option></select></label>
                    <label><span>Operation</span><select [(ngModel)]="node.operation" (ngModelChange)="onConditionOperationChange(node)"><option *ngFor="let operation of operationsFor(node)" [ngValue]="operation">{{ operationDefinitions[operation].label }}</option></select></label>
                    <label *ngIf="needsValue(node.operation) && !isRangeOperation(node.operation) && !isListOperation(node.operation) && !isBooleanField(node)"><span>Value</span><input [type]="inputType(node)" [ngModel]="getSingleValue(node)" (ngModelChange)="setSingleValue(node, $event)" /></label>
                    <label *ngIf="needsValue(node.operation) && !isRangeOperation(node.operation) && !isListOperation(node.operation) && isBooleanField(node)"><span>Value</span><select [ngModel]="booleanValue(node)" (ngModelChange)="setBooleanValue(node, $event)"><option value="">Select</option><option value="true">True</option><option value="false">False</option></select></label>
                    <label *ngIf="isListOperation(node.operation)"><span>Values</span><input type="text" placeholder="Comma-separated values" [ngModel]="getListValue(node)" (ngModelChange)="setListValue(node, $event)" /></label>
                    <div class="filterx-range" *ngIf="isRangeOperation(node.operation)"><label><span>From</span><input [type]="inputType(node)" [ngModel]="getRangeValue(node, 0)" (ngModelChange)="setRangeValue(node, 0, $event)" /></label><label><span>To</span><input [type]="inputType(node)" [ngModel]="getRangeValue(node, 1)" (ngModelChange)="setRangeValue(node, 1, $event)" /></label></div>
                </div>
                <button type="button" class="filterx-link danger" (click)="removeNode(parent, node)">Remove</button>
            </div>
        </ng-template>
    </div>
</ng-template>
'''


def _render_filterx_explorer_component_css() -> str:
        return r'''.filterx-page { display: grid; gap: 1.25rem; color: #172033; }
.filterx-hero, .filterx-searchbar, .filterx-controls, .filterx-panel, .filterx-groups, .filterx-results { background: #fff; border: 1px solid #d7dde7; border-radius: 18px; box-shadow: 0 14px 34px rgba(15, 23, 42, .06); padding: 1.25rem; }
.filterx-hero, .filterx-panel-header, .filterx-group-head { display: flex; justify-content: space-between; gap: 1rem; align-items: flex-start; }
.filterx-kicker { margin: 0 0 .3rem; color: #875a7b; font-size: .78rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
h1, h2 { margin: 0; color: #172033; } h1 { font-size: clamp(2rem, 4vw, 3rem); }
.filterx-subtitle, .filterx-panel p, .filterx-results p { margin: .45rem 0 0; color: #5d6880; line-height: 1.5; }
.filterx-hero-meta, .filterx-actions, .filterx-pagination, .filterx-buckets { display: flex; flex-wrap: wrap; gap: .65rem; }
.filterx-hero-meta span, .filterx-status, .filterx-bucket strong { display: inline-flex; align-items: center; min-height: 2rem; padding: 0 .75rem; border-radius: 999px; background: #f3edf2; color: #875a7b; font-size: .85rem; font-weight: 800; }
.filterx-searchbar { display: flex; gap: .75rem; align-items: stretch; }
.filterx-search-shell { display: flex; align-items: center; gap: .65rem; flex: 1; border: 1px solid #cdd6e4; border-radius: 14px; background: #f8fafc; padding-left: .85rem; }
.filterx-search-shell input { border: none; background: transparent; min-height: 3rem; padding: 0; }
.filterx-search-icon { color: #875a7b; font-size: 1.25rem; }
.filterx-controls { display: grid; grid-template-columns: repeat(4, minmax(10rem, 1fr)); gap: .9rem; }
label { display: grid; gap: .35rem; } label span { color: #52607a; font-size: .75rem; font-weight: 800; letter-spacing: .05em; text-transform: uppercase; }
input, select, button { font: inherit; } input, select { width: 100%; min-height: 2.7rem; border: 1px solid #cdd6e4; border-radius: 12px; background: #f8fafc; color: #172033; padding: 0 .8rem; }
.filterx-primary, .filterx-secondary, .filterx-page-btn { min-height: 2.7rem; border-radius: 12px; padding: 0 1rem; font-weight: 800; cursor: pointer; }
.filterx-primary { border: 1px solid #875a7b; background: #875a7b; color: #fff; }
.filterx-secondary, .filterx-page-btn { border: 1px solid #cdd6e4; background: #f4f7fb; color: #21304f; }
.filterx-page-btn.active { border-color: #875a7b; background: #f3edf2; color: #875a7b; }
.filterx-tree-node, .filterx-children { display: grid; gap: .8rem; }
.filterx-group-card, .filterx-condition-card { border: 1px solid #d9e0ea; border-radius: 16px; background: #fbfcfe; padding: 1rem; }
.filterx-group-card { border-left: 6px solid #875a7b; }
.filterx-condition-grid { display: grid; grid-template-columns: repeat(2, minmax(12rem, 1fr)); gap: .85rem; }
.filterx-range { display: grid; grid-template-columns: 1fr 1fr; gap: .85rem; grid-column: 1 / -1; }
.filterx-link { border: none; background: transparent; padding: 0; color: #0b5f9e; font-weight: 800; cursor: pointer; }
.filterx-link.danger { color: #ad1f35; }
.filterx-operator { min-height: 2.25rem; min-width: 4.5rem; border: 1px solid #172033; border-radius: 999px; background: #172033; color: #fff; font-weight: 900; cursor: pointer; }
.filterx-empty, .filterx-error { margin-top: .8rem; padding: .85rem 1rem; border-radius: 12px; background: #fff3f4; color: #7b2430; }
.filterx-bucket { display: inline-flex; align-items: center; gap: .5rem; padding: .45rem .55rem .45rem .8rem; border-radius: 999px; background: #f3f8ff; color: #21304f; }
.filterx-bucket strong { background: #e9dde7; min-height: 1.7rem; }
.filterx-table-wrap { overflow-x: auto; } table { width: 100%; border-collapse: collapse; } th, td { padding: .85rem; border-bottom: 1px solid #e2e8f0; text-align: left; vertical-align: top; } tbody tr:hover { background: #f8fafc; }
.filterx-sort { border: none; background: transparent; color: #172033; font-weight: 900; cursor: pointer; }
.filterx-status.loading { background: #eef4ff; color: #0b5f9e; }
@media (max-width: 900px) { .filterx-controls, .filterx-condition-grid, .filterx-range { grid-template-columns: 1fr; } .filterx-hero, .filterx-searchbar, .filterx-panel-header, .filterx-group-head { flex-direction: column; } }
'''


def _render_proxy_conf_cjs() -> str:
        return """module.exports = {\n  '/api': {\n    target: 'http://127.0.0.1:8000',\n    secure: false,\n    changeOrigin: true,\n    logLevel: 'warn',\n  },\n};\n"""


def _build_angular_json_with_proxy(project_root: Path, frontend_root: str) -> tuple[str, str] | None:
    angular_json_rel = f"{frontend_root.rstrip('/')}/angular.json"
    angular_json_path = project_root / angular_json_rel
    if not angular_json_path.exists():
        return None

    try:
        payload = json.loads(angular_json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None

    projects = payload.get("projects")
    if not isinstance(projects, dict):
        return None

    def ensure_primeicons_style(target: dict[str, Any]) -> None:
        nonlocal changed
        options = target.setdefault("options", {})
        if not isinstance(options, dict):
            return
        styles = options.setdefault("styles", [])
        if not isinstance(styles, list):
            return
        primeicons_style = "node_modules/primeicons/primeicons.css"
        if primeicons_style in styles:
            return
        src_style_index = next(
            (
                index
                for index, style in enumerate(styles)
                if isinstance(style, str) and style.startswith("src/styles")
            ),
            0,
        )
        styles.insert(src_style_index, primeicons_style)
        changed = True

    changed = False
    for project in projects.values():
        if not isinstance(project, dict):
            continue
        architect = project.get("architect")
        if not isinstance(architect, dict):
            continue
        serve = architect.get("serve")
        if not isinstance(serve, dict):
            continue
        options = serve.setdefault("options", {})
        if not isinstance(options, dict):
            continue
        if options.get("proxyConfig") != "proxy.conf.cjs":
            options["proxyConfig"] = "proxy.conf.cjs"
            changed = True

        build = architect.get("build")
        if isinstance(build, dict):
            ensure_primeicons_style(build)
            configurations = build.get("configurations")
            if isinstance(configurations, dict):
                production = configurations.get("production")
                if isinstance(production, dict):
                    budgets = production.get("budgets")
                    if isinstance(budgets, list):
                        for budget in budgets:
                            if not isinstance(budget, dict):
                                continue
                            if budget.get("type") == "anyComponentStyle":
                                if budget.get("maximumWarning") != "16kB":
                                    budget["maximumWarning"] = "16kB"
                                    changed = True
                                if budget.get("maximumError") != "24kB":
                                    budget["maximumError"] = "24kB"
                                    changed = True

        test = architect.get("test")
        if isinstance(test, dict):
            ensure_primeicons_style(test)

    if not changed:
        return None
    return angular_json_rel, json.dumps(payload, indent=2) + "\n"


def _build_package_json_with_ui_deps(project_root: Path, frontend_root: str) -> tuple[str, str] | None:
    package_rel = f"{frontend_root.rstrip('/')}/package.json"
    package_path = project_root / package_rel
    if not package_path.exists():
        return None
    try:
        payload = json.loads(package_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    dependencies = payload.setdefault("dependencies", {})
    if not isinstance(dependencies, dict):
        return None
    changed = False
    required = {
        "@angular/animations": "^19.2.0",
        "primeng": "^19.1.4",
        "primeicons": "^7.0.0",
        "@primeng/themes": "^19.1.4",
    }
    for name, version in required.items():
        if name not in dependencies:
            dependencies[name] = version
            changed = True
    if not changed:
        return None
    return package_rel, json.dumps(payload, indent=2) + "\n"


def _build_app_config_with_primeng(project_root: Path, app_config_file: str, app_config_anchor: str) -> tuple[str, str] | None:
    path = project_root / app_config_file
    if not path.exists():
        return None
    content = path.read_text(encoding="utf-8")
    changed = False
    if "provideAnimationsAsync" not in content:
        content = content.replace(
            "import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';",
            "import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';\nimport { provideAnimationsAsync } from '@angular/platform-browser/animations/async';",
        ).replace(
            'import { ApplicationConfig, provideZoneChangeDetection } from "@angular/core";',
            'import { ApplicationConfig, provideZoneChangeDetection } from "@angular/core";\nimport { provideAnimationsAsync } from "@angular/platform-browser/animations/async";',
        )
        changed = True
    if "providePrimeNG" not in content:
        marker = "import { provideRouter } from '@angular/router';"
        if marker in content:
            content = content.replace(marker, marker + "\nimport { providePrimeNG } from 'primeng/config';\nimport Aura from '@primeng/themes/aura';")
        else:
            marker = 'import { provideRouter } from "@angular/router";'
            content = content.replace(marker, marker + '\nimport { providePrimeNG } from "primeng/config";\nimport Aura from "@primeng/themes/aura";')
        changed = True
    provider_snippet = "    provideAnimationsAsync(),\n    providePrimeNG({\n      theme: {\n        preset: Aura,\n      },\n    }),"
    if "providePrimeNG({" not in content or "preset: Aura" not in content:
        if app_config_anchor in content:
            content = content.replace(app_config_anchor, provider_snippet + "\n    " + app_config_anchor)
        else:
            content = content.replace("  ],", provider_snippet + "\n  ],")
        changed = True
    elif "provideAnimationsAsync()" not in content:
        if app_config_anchor in content:
            content = content.replace(app_config_anchor, "    provideAnimationsAsync(),\n    " + app_config_anchor)
        else:
            content = content.replace("  ],", "    provideAnimationsAsync(),\n  ],")
        changed = True
    if not changed:
        return None
    return app_config_file, content


def _build_routes_file_with_generated_block(routes_file: Path, snippet: str) -> str | None:
    if not routes_file.exists():
        return None
    content = routes_file.read_text(encoding="utf-8")
    if GENERATED_ROUTES_RE.search(content):
        return GENERATED_ROUTES_RE.sub("\n" + snippet + "\n", content)
    return None


def _extract_existing_route_paths(routes_file: Path) -> set[str]:
    if not routes_file.exists():
        return set()
    content = GENERATED_ROUTES_RE.sub("\n", routes_file.read_text(encoding="utf-8"))
    matches = re.findall(r"path\s*:\s*['\"]([^'\"]+)['\"]", content)
    out = set()
    for match in matches:
        if match and match != "**":
            out.add(match.rstrip("/"))
    return out


def _reference_app_root() -> Path | None:
    candidates = [
        Path(__file__).resolve().parents[4] / "frontend" / "src" / "app",
        Path.cwd() / "filter_test_project" / "frontend" / "src" / "app",
        Path.cwd().parent / "filter_test_project" / "frontend" / "src" / "app",
    ]
    for candidate in candidates:
        if (candidate / "shared" / "components" / "entity-list" / "entity-list.component.ts").exists():
            return candidate
    return None


def _copy_reference_runtime_ops(frontend_root: str) -> list[PatchOp]:
    source_root = _reference_app_root()
    if source_root is None:
        return []
    ops: list[PatchOp] = []
    for rel in REFERENCE_RUNTIME_FILES:
        source = source_root / rel
        if not source.exists():
            continue
        content = source.read_text(encoding="utf-8")
        if rel == "core/services/generic-query.service.ts":
            content = content.replace(
                ".get<PaginatedResponse<T>>(this.baseUrl, { params: httpParams })",
                ".get<PaginatedResponse<T>>(this.baseUrl, { params: httpParams })",
            )
        if rel == "core/services/saved-filter.service.ts":
            content = content.replace(
                "import { Observable, throwError } from \"rxjs\";",
                "import { Observable, of, throwError } from \"rxjs\";",
            )
            content = content.replace(
                "  private readonly baseUrl = \"/api/saved-filters\";",
                "  private readonly baseUrl = \"/api/saved-filters\";\n  private readonly savedFiltersAvailable = false;",
            )
            content = content.replace(
                "  createFilter(filter: SavedFilterCreate): Observable<SavedFilter> {\n    return this.http\n      .post<SavedFilter>(this.baseUrl, filter)\n      .pipe(catchError(this.handleError));\n  }",
                "  createFilter(filter: SavedFilterCreate): Observable<SavedFilter> {\n    if (!this.savedFiltersAvailable) {\n      return of({ id: Date.now(), ...filter } as SavedFilter);\n    }\n    return this.http\n      .post<SavedFilter>(this.baseUrl, filter)\n      .pipe(catchError(this.handleError));\n  }",
            )
            content = content.replace(
                "  getFilters(modelName?: string): Observable<SavedFilter[]> {",
                "  getFilters(modelName?: string): Observable<SavedFilter[]> {\n    if (!this.savedFiltersAvailable) {\n      return of([]);\n    }",
            )
            content = content.replace(
                "  deleteFilter(filterId: number): Observable<void> {\n    return this.http\n      .delete<void>(`${this.baseUrl}/${filterId}`)\n      .pipe(catchError(this.handleError));\n  }",
                "  deleteFilter(filterId: number): Observable<void> {\n    if (!this.savedFiltersAvailable) {\n      return of(void 0);\n    }\n    return this.http\n      .delete<void>(`${this.baseUrl}/${filterId}`)\n      .pipe(catchError(this.handleError));\n  }",
            )
        ops.append(
            PatchOp(
                kind="generated_file",
                path=f"{frontend_root.rstrip('/')}/src/app/{rel}",
                content=content,
                owner="filterx-generated",
                description=f"Install FilterX reference UI runtime file {rel}",
            )
        )
    styles_source = source_root.parent / "styles.scss"
    if styles_source.exists():
        ops.append(
            PatchOp(
                kind="generated_file",
                path=f"{frontend_root.rstrip('/')}/src/styles.css",
                content=styles_source.read_text(encoding="utf-8"),
                owner="host",
                description="Install FilterX reference global styles",
            )
        )
    return ops


def _build_entity_config_ts(entity: dict[str, Any], style: str) -> tuple[str, str]:
    model_name = str(entity.get("model", "Entity"))
    interface_name = _to_pascal(model_name)
    config_name = f"{_to_snake(model_name).upper()}_GENERATED_CONFIG"
    route_path = _entity_route_path(entity, style)

    fields = list(entity.get("fields", []))
    relationships = list(entity.get("relationships", []))
    field_lines = []
    interface_lines = []
    column_lines = []
    group_by_lines = []
    for field in fields:
        name = str(field.get("name", "field"))
        ts_type = _ts_field_type(str(field.get("type", "string")))
        ui_type = _ui_field_type(str(field.get("type", "string")))
        interface_lines.append(f"  '{name}': {ts_type};")
        field_lines.append(f"    createFieldConfig('{name}', '{name.replace('_', ' ').title()}', '{ui_type}'),")
        column_lines.append(f"    createColumnConfig<{interface_name}>('{name}', '{name.replace('_', ' ').title()}', {{ type: '{ui_type}' }}),")
        group_by_lines.append(f"    {{ field: '{name}', label: '{name.replace('_', ' ').title()}' }},")

    for rel in relationships:
        if rel.get("uselist") or rel.get("cardinality") in {"o2m", "m2m"}:
            continue
        rel_name = str(rel.get("name") or "")
        display_field = str(rel.get("display_field") or "")
        if not rel_name or not display_field:
            continue
        rel_path = f"{rel_name}.{display_field}"
        rel_label = f"{rel_name.replace('_', ' ').title()} {display_field.replace('_', ' ').title()}"
        field_lines.append(f"    createFieldConfig('{rel_path}', '{rel_label}', 'text'),")
        column_lines.append(f"    createColumnConfig<{interface_name}>('{rel_path}', '{rel_label}', {{ type: 'text' }}),")
        group_by_lines.append(f"    {{ field: '{rel_path}', label: '{rel_label}' }},")

    content = (
        "import { SortOrder } from '../../core/enums/sort-order.enum';\n"
        "import {\n"
        "  EntityConfig,\n"
        "  createFieldConfig,\n"
        "  createColumnConfig,\n"
        "} from '../../core/interfaces/entity-config.interface';\n\n"
        f"export interface {interface_name} {{\n"
        + "\n".join(interface_lines)
        + "\n  [key: string]: unknown;"
        + "\n}\n\n"
        f"export const {config_name}: EntityConfig<{interface_name}> = {{\n"
        f"  name: '{interface_name}',\n"
        f"  pluralLabel: '{route_path.replace('-', ' ').title()}',\n"
        f"  singularLabel: '{interface_name}',\n"
        f"  apiEndpoint: '/api/filterx/{route_path}',\n"
        f"  searchPlaceholder: 'Search {interface_name.lower()}...',\n"
        f"  emptyMessage: 'No {interface_name.lower()} records found',\n"
        "  defaults: {\n"
        "    pageSize: 20,\n"
        "    sortField: 'id',\n"
        "    sortOrder: SortOrder.ASC,\n"
        "    pageSizeOptions: [10, 20, 50],\n"
        "  },\n"
        "  fields: [\n"
        + "\n".join(field_lines)
        + "\n  ],\n"
        "  columns: [\n"
        + "\n".join(column_lines)
        + "\n  ],\n"
        "  groupByOptions: [\n"
        + "\n".join(group_by_lines)
        + "\n  ],\n"
        "};\n"
    )
    return f"{_styled_name(model_name, style)}.config.ts", content


def _build_entity_page_ts(entity: dict[str, Any], style: str) -> tuple[str, str]:
    model_name = str(entity.get("model", "Entity"))
    model_slug = _styled_name(model_name, style)
    interface_name = _to_pascal(model_name)
    class_name = f"{interface_name}FilterxPageComponent"
    config_name = f"{_to_snake(model_name).upper()}_GENERATED_CONFIG"
    description = f"Browse and filter {interface_name.lower()} records using the generated FilterX search panel."
    content = (
        "import { Component } from '@angular/core';\n"
        "import { EntityListComponent } from '../../shared/components/entity-list/entity-list.component';\n"
        f"import {{ {config_name}, {interface_name} }} from '../entities/{model_slug}.config';\n\n"
        "@Component({\n"
        f"  selector: 'filterx-{model_slug}-page',\n"
        "  standalone: true,\n"
        "  imports: [EntityListComponent],\n"
        "  template: `\n"
        "    <app-entity-list\n"
        "      [config]=\"config\"\n"
        "      [showHeader]=\"true\"\n"
        f"      [description]=\"'{description}'\"\n"
        "      [clickableRows]=\"true\"\n"
        "      [onRowClicked]=\"handleRowClick\"\n"
        "    ></app-entity-list>\n"
        "  `,\n"
        "})\n"
        f"export class {class_name} {{\n"
        f"  config = {config_name};\n\n"
        f"  handleRowClick = (item: {interface_name}): void => {{\n"
        "    console.debug('FilterX row clicked', item);\n"
        "  };\n"
        "}\n"
    )
    return f"{model_slug}.page.ts", content


def _build_route_entry(entity: dict[str, Any], project_root: Path, frontend_root: str, style: str) -> tuple[str, str, str] | None:
    model_name = str(entity.get("model", "Entity"))
    model_slug = _styled_name(model_name, style)
    class_name = f"{_to_pascal(model_name)}FilterxPageComponent"
    route_path = _entity_route_path(entity, style).rstrip("/")
    title = route_path.replace("-", " ").title()
    generated_entry = (
        "  {\n"
        f"    path: '{route_path}',\n"
        "    loadComponent: () =>\n"
        f"      import('./pages/{model_slug}.page').then((m) => m.{class_name}),\n"
        f"    data: {{ entity: '{route_path}', title: '{title}' }},\n"
        f"    title: '{title} - FilterX Generated',\n"
        "  },"
    )
    host_entry = (
        "  {\n"
        f"    path: '{route_path}',\n"
        "    loadComponent: () =>\n"
        f"      import('./filterx-generated/pages/{model_slug}.page').then((m) => m.{class_name}),\n"
        f"    data: {{ entity: '{route_path}', title: '{title}' }},\n"
        f"    title: '{title} - FilterX Generated',\n"
        "  },"
    )
    return route_path, generated_entry, host_entry


def _run_install_impl(args: Any) -> int:
    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config).resolve() if args.config else None
    effective = load_effective_config(project_root, config_path)
    cfg = effective.raw

    if not cfg["frontend"].get("enabled", True):
        if args.json:
            print(json.dumps({"skipped": True, "reason": "frontend disabled in config"}, indent=2))
        else:
            print("FilterX frontend install skipped: frontend.enabled is false.")
        return 0

    dry_run = _resolve_dry_run(args, cfg)
    check_mode = bool(getattr(args, "check", False))
    strict_conflict_mode = bool(cfg["safety"].get("strict_conflict_mode", True))

    scan_path = project_root / cfg["output"]["scan_file"]
    if not scan_path.exists():
        payload = {
            "errors": [
                {
                    "code": "SCAN_FILE_MISSING",
                    "path": str(scan_path),
                    "message": "Run 'filterx scan' before frontend install.",
                }
            ]
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print("FilterX frontend install failed: scan artifact is missing.")
        return 2

    style = str(getattr(args, "style", None) or cfg["frontend"].get("entity_style", "kebab"))
    frontend_root = str(cfg["frontend"].get("workspace_root", "frontend"))
    generated_root = str(cfg["frontend"]["generated_root"])
    routes_file = str(getattr(args, "routes_file", None) or cfg["frontend"]["routes_file"])
    routes_anchor = str(getattr(args, "routes_anchor", None) or cfg["frontend"]["routes_anchor"])
    include_route_patch = not bool(getattr(args, "no_route_patch", False))
    force_routes = bool(getattr(args, "force", False))

    scan_payload = load_json(scan_path)
    entities = list(scan_payload.get("entities", []))
    allow = set(_csv_list(getattr(args, "entities", None)))
    if allow:
        entities = [entity for entity in entities if entity.get("model") in allow]

    root = Path(generated_root).as_posix().rstrip("/")
    ops: list[PatchOp] = []

    frontend_workspace_root = project_root / frontend_root
    if frontend_workspace_root.exists():
        ops.append(
            PatchOp(
                kind="generated_file",
                path=f"{frontend_root}/proxy.conf.cjs",
                content=_render_proxy_conf_cjs(),
                description="Generated Angular dev proxy for FilterX API calls",
            )
        )

    package_patch = _build_package_json_with_ui_deps(project_root, frontend_root)
    if package_patch is not None:
        package_rel, package_content = package_patch
        ops.append(
            PatchOp(
                kind="generated_file",
                path=package_rel,
                content=package_content,
                owner="host",
                description="Install FilterX reference UI npm dependencies",
            )
        )

    angular_proxy_patch = _build_angular_json_with_proxy(project_root, frontend_root)
    if angular_proxy_patch is not None:
        angular_json_rel, angular_json_content = angular_proxy_patch
        ops.append(
            PatchOp(
                kind="generated_file",
                path=angular_json_rel,
                content=angular_json_content,
                owner="host",
                description="Configure Angular dev server proxy for FilterX API calls",
            )
        )

    app_config_file = str(getattr(args, "app_config_file", None) or cfg["frontend"].get("app_config_file", ""))
    app_config_anchor = str(getattr(args, "app_config_anchor", None) or cfg["frontend"].get("app_config_anchor", ""))
    if app_config_file:
        app_config_patch = _build_app_config_with_primeng(project_root, app_config_file, app_config_anchor)
        if app_config_patch is not None:
            app_config_rel, app_config_content = app_config_patch
            ops.append(
                PatchOp(
                    kind="generated_file",
                    path=app_config_rel,
                    content=app_config_content,
                    owner="host",
                    description="Configure PrimeNG providers for the FilterX reference UI",
                )
            )

    ops.extend(_copy_reference_runtime_ops(frontend_root))
    ops.extend(
        [
            PatchOp(kind="delete_file", path=f"{root}/filterx.models.ts", description="Remove legacy generated explorer model contracts"),
            PatchOp(kind="delete_file", path=f"{root}/filterx-explorer.component.ts", description="Remove legacy generated explorer component"),
            PatchOp(kind="delete_file", path=f"{root}/filterx-explorer.component.html", description="Remove legacy generated explorer template"),
            PatchOp(kind="delete_file", path=f"{root}/filterx-explorer.component.css", description="Remove legacy generated explorer styles"),
        ]
    )

    entity_export_lines = []
    for entity in entities:
        file_name, file_content = _build_entity_config_ts(entity, style)
        model_name = str(entity.get("model", "Entity"))
        export_name = f"{_to_snake(model_name).upper()}_GENERATED_CONFIG"
        entity_export_lines.append(f"export {{ {export_name} }} from './{file_name[:-3]}';")
        ops.append(
            PatchOp(
                kind="generated_file",
                path=f"{root}/entities/{file_name}",
                content=file_content,
                description=f"Generated frontend entity config for {model_name}",
            )
        )
        page_name, page_content = _build_entity_page_ts(entity, style)
        ops.append(
            PatchOp(
                kind="generated_file",
                path=f"{root}/pages/{page_name}",
                content=page_content,
                description=f"Generated FilterX entity page for {model_name}",
            )
        )

    generated_routes_entries: list[str] = []
    host_routes_entries: list[str] = []
    existing_paths = _extract_existing_route_paths(project_root / routes_file)
    for entity in entities:
        route_data = _build_route_entry(entity, project_root, frontend_root, style)
        if route_data is None:
            continue
        route_path, generated_route_entry, host_route_entry = route_data
        generated_routes_entries.append(generated_route_entry)
        if route_path not in existing_paths or force_routes:
            host_routes_entries.append(host_route_entry)

    routes_ts = (
        "import { Routes } from '@angular/router';\n\n"
        "export const FILTERX_GENERATED_ROUTES: Routes = [\n"
        + ("\n".join(generated_routes_entries) if generated_routes_entries else "")
        + "\n];\n"
    )
    ops.extend(
        [
            PatchOp(
                kind="generated_file",
                path=f"{root}/routes.ts",
                content=routes_ts,
                description="Generated frontend route entries",
            ),
            PatchOp(
                kind="generated_file",
                path=f"{root}/entities/index.ts",
                content=("\n".join(entity_export_lines) + "\n") if entity_export_lines else "",
                description="Generated frontend entities index",
            ),
            PatchOp(
                kind="generated_file",
                path=f"{root}/index.ts",
                content="export * from './routes';\nexport * from './entities';\n",
                description="Generated frontend root index",
            ),
            PatchOp(
                kind="generated_file",
                path=f"{root}/services/filterx-entity-query.service.ts",
                content="export { EntityQueryService as FilterxEntityQueryService } from '../../core/services/entity-query.service';\n",
                description="Generated frontend query service alias",
            ),
        ]
    )

    if include_route_patch and host_routes_entries:
        snippet = "// FILTERX GENERATED ROUTES START\n" + "\n".join(host_routes_entries) + "\n// FILTERX GENERATED ROUTES END"
        replaced_routes = _build_routes_file_with_generated_block(project_root / routes_file, snippet)
        if replaced_routes is not None:
            ops.append(
                PatchOp(
                    kind="generated_file",
                    path=routes_file,
                    content=replaced_routes,
                    owner="host",
                    description="Replace generated routes in app.routes.ts",
                )
            )
        else:
            ops.append(
                PatchOp(
                    kind="anchor_insert",
                    path=routes_file,
                    anchor=routes_anchor,
                    snippet=snippet,
                    insert_mode="after",
                    owner="host",
                    description="Insert generated routes into app.routes.ts",
                )
            )

    manifest_path = project_root / cfg["safety"]["idempotency_manifest"]
    patch_dir = project_root / cfg["output"]["patch_dir"]
    result = apply_patch_operations(
        project_root=project_root,
        operations=ops,
        manifest_path=manifest_path,
        patch_dir=patch_dir,
        dry_run=dry_run,
        check_mode=check_mode,
        strict_conflict_mode=strict_conflict_mode,
        description="frontend.install",
    )

    payload = {
        "dry_run": result.dry_run,
        "check_mode": check_mode,
        "patch_id": result.patch_id,
        "generated_root": str((project_root / generated_root).resolve()),
        "entity_count": len(entities),
        "generated_route_count": len(host_routes_entries),
        "touched_files": result.touched_files,
        "applied_ops": result.applied_ops,
        "skipped_ops": result.skipped_ops,
        "issues": [
            {"code": issue.code, "message": issue.message, "context": issue.context}
            for issue in result.issues
        ],
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("FilterX frontend install completed.")
        print(f"- Dry run: {payload['dry_run']}")
        print(f"- Applied ops: {payload['applied_ops']}")
        print(f"- Skipped ops: {payload['skipped_ops']}")

    if result.has_conflicts:
        return 3
    if getattr(args, "fail_on_warning", False) and result.issues:
        return 3
    return 0


def _frontend_remove_candidates(patch_dir: Path) -> list[str]:
    candidates: list[str] = []
    for patch_id in list_patch_bundles(patch_dir):
        meta_path = patch_dir / patch_id / "meta.json"
        if not meta_path.exists():
            continue
        try:
            meta = load_json(meta_path)
        except Exception:
            continue
        if meta.get("description") == "frontend.install":
            candidates.append(patch_id)
    return candidates


def run_install(args: Any) -> int:
    return _run_install_impl(args)


def run_validate(args: Any) -> int:
    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config).resolve() if args.config else None
    effective = load_effective_config(project_root, config_path)
    cfg = effective.raw

    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    root = Path(cfg["frontend"]["generated_root"]).as_posix().rstrip("/")
    required = [
        f"{root}/index.ts",
        f"{root}/routes.ts",
        f"{root}/entities/index.ts",
        f"{root}/services/filterx-entity-query.service.ts",
        f"{cfg['frontend'].get('workspace_root', 'frontend')}/src/app/core/services/generic-query.service.ts",
        f"{cfg['frontend'].get('workspace_root', 'frontend')}/src/app/shared/components/entity-list/entity-list.component.ts",
        f"{cfg['frontend'].get('workspace_root', 'frontend')}/src/app/shared/components/advanced-search-panel/advanced-search-panel.component.ts",
        f"{cfg['frontend'].get('workspace_root', 'frontend')}/src/app/shared/components/data-table/data-table.component.ts",
        f"{cfg['frontend'].get('workspace_root', 'frontend')}/src/app/shared/components/filter-builder/filter-builder.component.ts",
    ]
    for rel in required:
        if not (project_root / rel).exists():
            errors.append({"code": "FRONTEND_GENERATED_FILE_MISSING", "path": str(project_root / rel)})

    routes_file = project_root / cfg["frontend"]["routes_file"]
    routes_anchor = cfg["frontend"]["routes_anchor"]
    if not routes_file.exists():
        errors.append({"code": "FRONTEND_ROUTES_FILE_MISSING", "path": str(routes_file)})
    else:
        content = routes_file.read_text(encoding="utf-8")
        if routes_anchor not in content:
            warnings.append(
                {
                    "code": "FRONTEND_ROUTES_ANCHOR_NOT_FOUND",
                    "path": str(routes_file),
                    "anchor": routes_anchor,
                }
            )

    payload = {
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings),
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("FilterX frontend validation completed.")
        print(f"- Errors: {payload['error_count']}")
        print(f"- Warnings: {payload['warning_count']}")

    if payload["errors"]:
        return 4
    if getattr(args, "fail_on_warning", False) and payload["warnings"]:
        return 3
    return 0


def run_remove(args: Any) -> int:
    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config).resolve() if args.config else None
    effective = load_effective_config(project_root, config_path)
    cfg = effective.raw

    patch_dir = project_root / cfg["output"]["patch_dir"]
    candidates = _frontend_remove_candidates(patch_dir)

    if getattr(args, "list", False):
        payload = {"patch_dir": str(patch_dir), "frontend_install_patches": candidates}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print("Available frontend remove patch bundles:")
            if not candidates:
                print("- (none)")
            for patch_id in candidates:
                print(f"- {patch_id}")
        return 0

    if not candidates:
        print("No frontend install patch bundles available for rollback.")
        return 2

    patch_id = getattr(args, "patch_id", None) or candidates[-1]
    if patch_id not in candidates:
        print(f"Frontend patch id '{patch_id}' not found.")
        return 2

    dry_run = _resolve_dry_run(args, cfg)
    check_mode = bool(getattr(args, "check", False))
    if dry_run or check_mode:
        payload = {
            "dry_run": True,
            "check_mode": check_mode,
            "would_rollback_patch_id": patch_id,
            "patch_dir": str(patch_dir),
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print("FilterX frontend remove preview.")
            print(f"- Patch ID: {patch_id}")
        return 0

    result = rollback_patch_bundle(project_root, patch_dir, patch_id)
    payload = {
        "patch_id": patch_id,
        "restored": result.get("restored", []),
        "removed": result.get("removed", []),
        "count": result.get("count", 0),
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"FilterX frontend remove completed for patch: {patch_id}")
        print(f"- Restored files: {len(payload['restored'])}")
        print(f"- Removed files: {len(payload['removed'])}")

    return 0
