import { Component, Input, OnInit, OnDestroy, inject } from "@angular/core";
import { CommonModule } from "@angular/common";
import { Subject } from "rxjs";
import { takeUntil, finalize } from "rxjs/operators";

import {
  EntityConfig,
  FieldConfig,
  ColumnConfig,
  QuickFilterConfig,
  GroupByConfig,
} from "../../../core/interfaces/entity-config.interface";
import { FilterRule } from "../../../core/interfaces/filter.interface";
import {
  SavedFilter,
  SavedFilterCreate,
} from "../../../core/interfaces/saved-filter.interface";
import {
  FilterTreeNode,
  generateNodeId,
} from "../../../core/interfaces/filter-tree.interface";
import { PaginatedResponse } from "../../../core/interfaces/pagination.interface";
import { SortOrder } from "../../../core/enums/sort-order.enum";
import { FilterOperation } from "../../../core/enums/filter-operation.enum";
import { QueryState } from "../../../core/interfaces/query-state.interface";
import { EntityQueryService } from "../../../core/services/entity-query.service";
import { SavedFilterService } from "../../../core/services/saved-filter.service";

import { AdvancedSearchPanelComponent } from "../advanced-search-panel/advanced-search-panel.component";
import { DataTableComponent } from "../data-table/data-table.component";

@Component({
  selector: "app-entity-list",
  standalone: true,
  imports: [CommonModule, AdvancedSearchPanelComponent, DataTableComponent],
  providers: [EntityQueryService],
  template: `
    <div class="entity-list-container">
      <header class="page-header" *ngIf="showHeader">
        <h1 class="page-title">{{ config.pluralLabel }}</h1>
        <p class="page-description" *ngIf="description">{{ description }}</p>
      </header>

      <section class="search-section">
        <app-advanced-search-panel
          [modelName]="config.name"
          [apiEndpoint]="config.apiEndpoint"
          [fields]="fields"
          [quickFilters]="quickFilters"
          [groupByOptions]="groupByOptions"
          [activeGroupBy]="groupBy"
          [activeFilters]="filters"
          [activeTree]="filterTree"
          [searchQuery]="search"
          [sortBy]="sortField"
          [sortOrder]="sortOrder"
          [savedFilters]="savedFilters"
          [placeholder]="config.searchPlaceholder || 'Search...'"
          (filtersChange)="onFiltersChange($event)"
          (treeChange)="onTreeChange($event)"
          (globalSearch)="onGlobalSearch($event)"
          (groupByChange)="onGroupByChange($event)"
          (saveFilter)="onSaveFilter($event)"
          (applySavedFilter)="onApplySavedFilter($event)"
          (deleteSavedFilter)="onDeleteSavedFilter($event)"
        ></app-advanced-search-panel>
      </section>

      <section class="group-summary" *ngIf="groupBy && groupedBuckets.length > 0">
        <h3 class="group-summary-title">Grouped By {{ groupByLabel }}</h3>
        <div class="group-buckets">
          <span class="group-bucket" *ngFor="let bucket of groupedBuckets; trackBy: trackByBucketKey">
            <span class="bucket-key">{{ bucket.key ?? 'None' }}</span>
            <span class="bucket-count">{{ bucket.count }}</span>
          </span>
        </div>
      </section>

      <section class="query-context" *ngIf="loading || pagination || hasActiveCriteria">
        <div class="context-left">
          <span class="context-pill result-pill" [class.loading]="loading">
            {{ contextResultLabel }}
          </span>
          <span class="context-pill" *ngIf="sortField">Sorted: {{ sortLabel }}</span>
          <span class="context-pill" *ngIf="groupByLabel">Group: {{ groupByLabel }}</span>
        </div>
        <div class="context-right">
          <button
            type="button"
            class="context-action"
            *ngIf="hasActiveCriteria"
            (click)="clearAllCriteria()"
          >
            Clear all filters
          </button>
        </div>
      </section>

      <section class="table-section">
        <div class="table-error" *ngIf="errorMessage">
          <div class="table-error-content">
            <strong>Could not load data.</strong>
            <span>{{ errorMessage }}</span>
          </div>
          <button type="button" class="error-retry-btn" (click)="retryLoad()">
            Retry
          </button>
        </div>

        <app-data-table
          [data]="data"
          [columns]="columns"
          [loading]="loading"
          [pagination]="pagination"
          [sortField]="sortField"
          [sortOrder]="sortOrder"
          [pageSizeOptions]="pageSizeOptions"
          [showPagination]="true"
          [hoverRows]="true"
          [clickableRows]="clickableRows"
          [striped]="true"
          [emptyMessage]="tableEmptyMessage"
          (sortChange)="onSortChange($event)"
          (pageChange)="onPageChange($event)"
          (pageSizeChange)="onPageSizeChange($event)"
          (rowClick)="onRowClick($event)"
        ></app-data-table>
      </section>
    </div>
  `,
  styles: [
    `
      .entity-list-container {
        max-width: 1420px;
        margin: 0 auto;
        padding: var(--space-6);
      }

      .page-header {
        margin-bottom: var(--space-5);
      }

      .page-title {
        margin: 0 0 var(--space-2) 0;
        font-size: 30px;
        font-weight: 700;
        color: var(--color-text);
        letter-spacing: -0.015em;
      }

      .page-description {
        margin: 0;
        font-size: 14px;
        color: var(--color-text-muted);
      }

      .search-section {
        margin-bottom: var(--space-4);
      }

      .query-context {
        margin-bottom: var(--space-4);
        padding: var(--space-3) var(--space-4);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-md);
        background: var(--color-bg-elevated);
        box-shadow: var(--shadow-sm);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: var(--space-3);
        flex-wrap: wrap;
      }

      .context-left {
        display: flex;
        align-items: center;
        gap: var(--space-2);
        flex-wrap: wrap;
      }

      .context-pill {
        display: inline-flex;
        align-items: center;
        padding: 6px 12px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
        background: var(--color-bg-soft);
        color: var(--color-text-muted);
        border: 1px solid var(--color-border);
      }

      .result-pill {
        color: var(--color-primary-strong);
        background: #e8f2fb;
        border-color: #c8dff3;
      }

      .result-pill.loading {
        color: var(--color-info);
      }

      .context-right {
        display: flex;
        align-items: center;
        gap: var(--space-2);
      }

      .context-action {
        padding: 8px 14px;
        border-radius: var(--radius-sm);
        border: 1px solid #f4b4b4;
        background: #fff7f7;
        color: var(--color-danger);
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        transition: 0.2s ease;
      }

      .context-action:hover {
        background: #ffecec;
        border-color: #ea9e9e;
      }

      .table-section {
        background: var(--color-bg-elevated);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-md);
        border: 1px solid var(--color-border);
        overflow: hidden;
      }

      .group-summary {
        margin-bottom: var(--space-4);
        padding: var(--space-3) var(--space-4);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-md);
        background: var(--color-bg-elevated);
      }

      .group-summary-title {
        margin: 0 0 var(--space-2) 0;
        font-size: 14px;
        color: var(--color-text-muted);
      }

      .group-buckets {
        display: flex;
        flex-wrap: wrap;
        gap: var(--space-2);
      }

      .group-bucket {
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
        padding: 6px 10px;
        border-radius: 999px;
        background: #eef6ff;
        border: 1px solid #cadff4;
        color: #275278;
        font-size: 12px;
        font-weight: 600;
      }

      .bucket-count {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 22px;
        height: 22px;
        padding: 0 6px;
        border-radius: 999px;
        background: #dceeff;
        color: #143c5f;
      }

      .table-error {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: var(--space-3);
        padding: var(--space-3) var(--space-4);
        background: #fff5f5;
        border-bottom: 1px solid #f3bebe;
      }

      .table-error-content {
        display: grid;
        gap: 2px;
        font-size: 13px;
        color: #8b2c2c;
      }

      .error-retry-btn {
        padding: 8px 14px;
        border-radius: var(--radius-sm);
        border: 1px solid #f0a7a7;
        background: #fff;
        color: #9b2c2c;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        cursor: pointer;
        transition: 0.2s ease;
      }

      .error-retry-btn:hover {
        background: #ffeaea;
      }

      @media (max-width: 768px) {
        .entity-list-container {
          padding: var(--space-4);
        }

        .page-title {
          font-size: 24px;
        }

        .query-context {
          padding: var(--space-3);
        }

        .table-error {
          align-items: flex-start;
          flex-direction: column;
        }
      }
    `,
  ],
})
export class EntityListComponent<T = unknown> implements OnInit, OnDestroy {
  @Input() config!: EntityConfig<T>;

  @Input() showHeader = true;

  @Input() description = "";

  @Input() clickableRows = true;

  @Input() onRowClicked?: (item: T) => void;

  protected entityQueryService = inject<EntityQueryService<T>>(EntityQueryService);
  protected savedFilterService = inject(SavedFilterService);

  data: T[] = [];
  pagination: PaginatedResponse<T>["meta"] | null = null;
  loading = false;
  errorMessage: string | null = null;

  filters: FilterRule[] = [];
  filterTree: FilterTreeNode | null = null;
  search = "";
  sortField: string | null = null;
  sortOrder: SortOrder = SortOrder.ASC;
  groupBy: string | null = null;
  groupedBuckets: Array<{ key: unknown; count: number }> = [];

  savedFilters: SavedFilter[] = [];

  protected destroy$ = new Subject<void>();

  get fields(): FieldConfig[] {
    return this.config?.fields || [];
  }

  get columns(): ColumnConfig<T>[] {
    return this.config?.columns || [];
  }

  get quickFilters(): QuickFilterConfig[] {
    return this.config?.quickFilters || [];
  }

  get groupByOptions(): GroupByConfig[] {
    return this.config?.groupByOptions || [];
  }

  get pageSizeOptions(): number[] {
    return this.config?.defaults?.pageSizeOptions || [10, 20, 50, 100];
  }

  protected currentPage = 1;
  protected currentPageSize = 20;

  ngOnInit(): void {
    this.initializeDefaults();
    this.loadData();
    this.loadSavedFilters();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  protected initializeDefaults(): void {
    if (this.config?.defaults) {
      this.sortField = this.config.defaults.sortField ?? null;
      this.sortOrder = this.config.defaults.sortOrder ?? SortOrder.ASC;
      this.currentPageSize = this.config.defaults.pageSize ?? 20;
    }
  }

  loadData(): void {
    if (!this.config?.apiEndpoint) {
      console.warn("EntityListComponent: No API endpoint configured");
      return;
    }

    this.entityQueryService.setBaseUrl(this.config.apiEndpoint);
    this.loading = true;
    this.errorMessage = null;

    const state = this.buildQueryState();
    this.entityQueryService
      .queryWithState(state)
      .pipe(
        takeUntil(this.destroy$),
        finalize(() => (this.loading = false)),
      )
      .subscribe({
        next: (response) => {
          this.handleResponse(response);
          if (this.groupBy) {
            this.loadGroupedData(state);
          } else {
            this.groupedBuckets = [];
          }
        },
        error: (error) => this.handleError(error),
      });
  }

  private handleResponse(response: PaginatedResponse<T>): void {
    this.data = response.data;
    this.pagination = response.meta;
    this.errorMessage = null;
  }

  private handleError(error: any): void {
    console.error("Error loading data:", error);
    this.data = [];
    this.pagination = null;
    this.errorMessage =
      error?.error?.detail || error?.message || "Unexpected API error";
  }

  protected buildQueryState(): QueryState {
    return {
      filterTree: this.filterTree,
      filters: this.filters,
      pagination: {
        page: this.currentPage,
        size: this.currentPageSize,
      },
      sort: {
        sort_by: this.sortField,
        order: this.sortOrder,
      },
      search: this.search || null,
    };
  }

  protected loadGroupedData(state: QueryState): void {
    if (!this.groupBy) {
      this.groupedBuckets = [];
      return;
    }

    this.entityQueryService
      .queryGroupedWithState(this.groupBy, state)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (buckets) => {
          this.groupedBuckets = buckets;
        },
        error: () => {
          this.groupedBuckets = [];
        },
      });
  }

  loadSavedFilters(): void {
    if (!this.config?.name) return;

    this.savedFilterService
      .getFilters(this.config.name)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (filters) => {
          this.savedFilters = filters;
        },
        error: (error) => {
          console.error("Error loading saved filters:", error);
        },
      });
  }

  onSaveFilter(filterData: SavedFilterCreate): void {
    this.savedFilterService
      .createFilter(filterData)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (savedFilter) => {
          this.savedFilters = [...this.savedFilters, savedFilter];
        },
        error: (error) => {
          console.error("Error saving filter:", error);
        },
      });
  }

  onApplySavedFilter(filter: SavedFilter): void {
    this.filters = filter.filters || [];
    this.filterTree = filter.filter_tree || null;
    this.search = filter.search_query || "";
    this.sortField = filter.sort_by || this.config?.defaults?.sortField || null;
    this.sortOrder = (filter.sort_order as SortOrder) || SortOrder.ASC;

    if (filter.page_size) {
      this.currentPageSize = filter.page_size;
    }

    this.currentPage = 1;
    this.loadData();
  }

  onDeleteSavedFilter(filterId: number): void {
    this.savedFilterService
      .deleteFilter(filterId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.savedFilters = this.savedFilters.filter(
            (f) => f.id !== filterId,
          );
        },
        error: (error) => {
          console.error("Error deleting filter:", error);
        },
      });
  }

  onFiltersChange(filters: FilterRule[]): void {
    if (filters.length > 0) {
      const conditions: FilterTreeNode[] = filters.map((f) => ({
        id: generateNodeId(),
        nodeType: "condition" as const,
        field: f.field,
        operation: f.operation as any,
        value: f.value,
      }));
      this.filterTree = {
        id: generateNodeId(),
        nodeType: "operator",
        operator: "AND",
        children: conditions,
        expanded: true,
      };
    } else {
      this.filterTree = null;
    }
    this.filters = filters;
    this.currentPage = 1;
    this.loadData();
  }

  onTreeChange(tree: FilterTreeNode | null): void {
    this.filterTree = this.normalizeIncomingTree(tree);
    if (this.filterTree) {
      this.filters = [];
    }
    this.currentPage = 1;
    this.loadData();
  }

  onGlobalSearch(query: string): void {
    this.search = query;
    this.currentPage = 1;
    this.loadData();
  }

  onSortChange(event: { field: string | null; order: SortOrder }): void {
    this.sortField = event.field;
    this.sortOrder = event.order;
    this.loadData();
  }

  onGroupByChange(field: string | null): void {
    this.groupBy = field;
    this.loadData();
  }

  onPageChange(page: number): void {
    this.currentPage = page;
    this.loadData();
  }

  onPageSizeChange(size: number): void {
    this.currentPageSize = size;
    this.currentPage = 1;
    this.loadData();
  }

  onRowClick(item: T): void {
    if (this.onRowClicked) {
      this.onRowClicked(item);
    } else {
    }
  }

  clearAllCriteria(): void {
    this.filters = [];
    this.filterTree = null;
    this.search = "";
    this.groupBy = null;
    this.groupedBuckets = [];
    this.currentPage = 1;
    this.loadData();
  }

  retryLoad(): void {
    this.loadData();
  }

  get hasActiveCriteria(): boolean {
    return this.filters.length > 0 || !!this.filterTree || !!this.search;
  }

  get contextResultLabel(): string {
    if (this.loading) {
      return "Updating results...";
    }
    if (!this.pagination) {
      return "No results yet";
    }
    const total = this.pagination.total_items;
    return `${total} result${total === 1 ? "" : "s"}`;
  }

  get sortLabel(): string {
    if (!this.sortField) {
      return "Default";
    }
    const label =
      this.columns.find((column) => column.field === this.sortField)?.header ||
      this.sortField;
    return `${label} ${this.sortOrder === SortOrder.ASC ? "(Asc)" : "(Desc)"}`;
  }

  get groupByLabel(): string | null {
    if (!this.groupBy) {
      return null;
    }
    const label =
      this.groupByOptions.find((option) => option.field === this.groupBy)
        ?.label || this.groupBy;
    return label;
  }

  trackByBucketKey(index: number, bucket: { key: unknown; count: number }): string {
    return `${index}-${String(bucket.key)}`;
  }

  get tableEmptyMessage(): string {
    if (this.hasActiveCriteria) {
      return "No matches for current criteria";
    }
    return this.config?.emptyMessage || "No items found";
  }

  private normalizeIncomingTree(
    tree: FilterTreeNode | null,
  ): FilterTreeNode | null {
    if (!tree) {
      return null;
    }

    if (tree.nodeType === "operator") {
      return {
        ...tree,
        children: (tree.children || [])
          .map((child) => this.normalizeIncomingTree(child))
          .filter((child): child is FilterTreeNode => !!child),
      };
    }

    const operation = tree.operation;
    let value = tree.value;

    if (
      operation === FilterOperation.IS_NULL ||
      operation === FilterOperation.IS_NOT_NULL
    ) {
      value = true;
    } else if (
      operation === FilterOperation.IN ||
      operation === FilterOperation.NOT_IN
    ) {
      if (Array.isArray(value)) {
        value = value.filter(
          (v) => v !== null && v !== undefined && `${v}`.trim() !== "",
        );
      } else if (typeof value === "string") {
        value = value
          .split(",")
          .map((v) => v.trim())
          .filter((v) => v.length > 0);
      } else if (value === null || value === undefined || value === "") {
        value = [];
      } else {
        value = [value];
      }
    } else if (operation === FilterOperation.BETWEEN) {
      if (Array.isArray(value)) {
        value = value.slice(0, 2);
      } else if (typeof value === "string") {
        value = value
          .split(",")
          .map((v) => v.trim())
          .slice(0, 2);
      } else {
        value = [null, null];
      }
      while (value.length < 2) {
        value.push(null);
      }
    }

    return {
      ...tree,
      value,
    };
  }
}
