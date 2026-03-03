import { Component, Input, OnInit, OnDestroy, inject } from "@angular/core";
import { CommonModule } from "@angular/common";
import { HttpClient, HttpParams } from "@angular/common/http";
import { Subject, BehaviorSubject, Observable } from "rxjs";
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
import { FilterTreeNode, toBackendPayload, generateNodeId } from "../../../core/interfaces/filter-tree.interface";
import { PaginatedResponse } from "../../../core/interfaces/pagination.interface";
import { SortOrder } from "../../../core/enums/sort-order.enum";
import { SavedFilterService } from "../../../core/services/saved-filter.service";

import { AdvancedSearchPanelComponent } from "../advanced-search-panel/advanced-search-panel.component";
import { DataTableComponent } from "../data-table/data-table.component";

/**
 * Generic Entity List Component
 *
 * A fully reusable list component that works with any entity.
 * Just provide an EntityConfig and it handles everything:
 * - Filtering, sorting, pagination
 * - Quick filters
 * - Saved filters (favorites)
 * - Data table with configurable columns
 *
 * Usage:
 * ```html
 * <app-entity-list [config]="bookConfig"></app-entity-list>
 * ```
 *
 * Or extend this component for custom behavior:
 * ```typescript
 * @Component({...})
 * export class BookListComponent extends EntityListComponent<Book> {
 *   constructor() {
 *     super();
 *     this.config = BOOK_CONFIG;
 *   }
 * }
 * ```
 */
@Component({
  selector: "app-entity-list",
  standalone: true,
  imports: [CommonModule, AdvancedSearchPanelComponent, DataTableComponent],
  template: `
    <div class="entity-list-container">
      <header class="page-header" *ngIf="showHeader">
        <h1 class="page-title">{{ config?.pluralLabel }}</h1>
        <p class="page-description" *ngIf="description">{{ description }}</p>
      </header>

      <section class="search-section">
        <app-advanced-search-panel
          [modelName]="config?.name || ''"
          [fields]="fields"
          [quickFilters]="quickFilters"
          [groupByOptions]="groupByOptions"
          [activeFilters]="filters"
          [activeTree]="filterTree"
          [searchQuery]="search"
          [sortBy]="sortField"
          [sortOrder]="sortOrder"
          [savedFilters]="savedFilters"
          [placeholder]="config?.searchPlaceholder || 'Search...'"
          (filtersChange)="onFiltersChange($event)"
          (treeChange)="onTreeChange($event)"
          (searchChange)="onSearchChange($event)"
          (groupByChange)="onGroupByChange($event)"
          (saveFilter)="onSaveFilter($event)"
          (applySavedFilter)="onApplySavedFilter($event)"
          (deleteSavedFilter)="onDeleteSavedFilter($event)"
        ></app-advanced-search-panel>
      </section>

      <section class="table-section">
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
          [emptyMessage]="config?.emptyMessage || 'No items found'"
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
        max-width: 1400px;
        margin: 0 auto;
        padding: 24px;
      }

      .page-header {
        margin-bottom: 24px;
      }

      .page-title {
        margin: 0 0 8px 0;
        font-size: 28px;
        font-weight: 600;
        color: #1a1a1a;
      }

      .page-description {
        margin: 0;
        font-size: 14px;
        color: #666;
      }

      .search-section {
        margin-bottom: 20px;
      }

      .table-section {
        background: #fff;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
      }

      @media (max-width: 768px) {
        .entity-list-container {
          padding: 16px;
        }

        .page-title {
          font-size: 24px;
        }
      }
    `,
  ],
})
export class EntityListComponent<T = unknown> implements OnInit, OnDestroy {
  // ===== INPUTS =====

  /** Entity configuration - defines fields, columns, filters, etc. */
  @Input() config!: EntityConfig<T>;

  /** Show page header with title */
  @Input() showHeader = true;

  /** Page description text */
  @Input() description = "";

  /** Whether rows are clickable */
  @Input() clickableRows = true;

  /** Custom row click handler */
  @Input() onRowClicked?: (item: T) => void;

  // ===== SERVICES =====
  protected http = inject(HttpClient);
  protected savedFilterService = inject(SavedFilterService);

  // ===== STATE =====
  data: T[] = [];
  pagination: PaginatedResponse<T>["meta"] | null = null;
  loading = false;

  filters: FilterRule[] = [];
  filterTree: FilterTreeNode | null = null;
  search = "";
  sortField: string | null = null;
  sortOrder: SortOrder = SortOrder.ASC;
  groupBy: string | null = null;

  savedFilters: SavedFilter[] = [];

  protected destroy$ = new Subject<void>();

  // ===== COMPUTED FROM CONFIG =====

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

  // ===== LIFECYCLE =====

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

  // ===== DATA LOADING =====

  loadData(): void {
    if (!this.config?.apiEndpoint) {
      console.warn("EntityListComponent: No API endpoint configured");
      return;
    }

    this.loading = true;

    // Use POST /filter if tree is active, otherwise build GET params
    if (this.filterTree) {
      this.loadDataWithTree();
    } else {
      this.loadDataWithParams();
    }
  }

  protected loadDataWithParams(): void {
    const params = this.buildQueryParams();
    this.http
      .get<PaginatedResponse<T>>(this.config.apiEndpoint, { params })
      .pipe(
        takeUntil(this.destroy$),
        finalize(() => (this.loading = false)),
      )
      .subscribe({
        next: (response) => this.handleResponse(response),
        error: (error) => this.handleError(error),
      });
  }

  protected loadDataWithTree(): void {
    // Backend expects FilterNode directly as body, pagination/sort as query params
    const body = toBackendPayload(this.filterTree!);

    let params = new HttpParams();
    params = params.set('page', this.currentPage.toString());
    params = params.set('size', this.currentPageSize.toString());
    if (this.sortField) {
      params = params.set('sort_by', this.sortField);
      params = params.set('order', this.sortOrder);
    }
    if (this.search) {
      params = params.set('search', this.search);
    }

    const url = `${this.config.apiEndpoint}/filter`;
    this.http
      .post<PaginatedResponse<T>>(url, body, { params })
      .pipe(
        takeUntil(this.destroy$),
        finalize(() => (this.loading = false)),
      )
      .subscribe({
        next: (response) => this.handleResponse(response),
        error: (error) => this.handleError(error),
      });
  }

  private handleResponse(response: PaginatedResponse<T>): void {
    this.data = response.data;
    this.pagination = response.meta;
  }

  private handleError(error: any): void {
    console.error("Error loading data:", error);
    this.data = [];
    this.pagination = null;
  }

  protected buildQueryParams(): HttpParams {
    let params = new HttpParams();

    // Pagination
    params = params.set("page", this.currentPage.toString());
    params = params.set("size", this.currentPageSize.toString());

    // Sorting
    if (this.sortField) {
      params = params.set("sort_by", this.sortField);
      params = params.set("order", this.sortOrder);
    }

    // Search
    if (this.search) {
      params = params.set("search", this.search);
    }

    // Filters (URL grammar format: field_operation=value)
    for (const filter of this.filters) {
      const paramName = `${filter.field}_${filter.operation}`;
      const value = Array.isArray(filter.value)
        ? filter.value.join(",")
        : String(filter.value);
      params = params.set(paramName, value);
    }

    return params;
  }

  // ===== SAVED FILTERS =====

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

  // ===== EVENT HANDLERS =====

  onFiltersChange(filters: FilterRule[]): void {
    // Convert flat filters (from quick filters) into tree conditions
    if (filters.length > 0) {
      const conditions: FilterTreeNode[] = filters.map(f => ({
        id: generateNodeId(),
        nodeType: 'condition' as const,
        field: f.field,
        operation: f.operation as any,
        value: f.value
      }));
      this.filterTree = {
        id: generateNodeId(),
        nodeType: 'operator',
        operator: 'AND',
        children: conditions,
        expanded: true
      };
    } else {
      this.filterTree = null;
    }
    this.filters = filters;
    this.currentPage = 1;
    this.loadData();
  }

  onTreeChange(tree: FilterTreeNode | null): void {
    this.filterTree = tree;
    this.currentPage = 1;
    this.loadData();
  }

  onSearchChange(search: string): void {
    this.search = search;
    // Don't reload on every keystroke — the Odoo-style dropdown
    // handles adding structured filters. Only reload when cleared.
    if (!search) {
      this.currentPage = 1;
      this.loadData();
    }
  }

  onSortChange(event: { field: string | null; order: SortOrder }): void {
    this.sortField = event.field;
    this.sortOrder = event.order;
    this.loadData();
  }

  onGroupByChange(field: string | null): void {
    this.groupBy = field;
    // Group by logic would go here - could trigger backend grouping or client-side
    console.log("Group by:", field);
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
      console.log("Row clicked:", item);
    }
  }
}
