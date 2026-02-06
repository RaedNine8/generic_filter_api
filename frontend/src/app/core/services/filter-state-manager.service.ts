import { Injectable } from "@angular/core";
import { BehaviorSubject, Observable } from "rxjs";
import { FilterRule } from "../interfaces/filter.interface";
import { FilterableField } from "../interfaces/field-config.interface";
import {
  FilterOperation,
  FILTER_OPERATION_LABELS,
  operationNeedsValue,
} from "../enums/filter-operation.enum";
import { SortOrder } from "../enums/sort-order.enum";

/**
 * Filter State
 * Complete state for a filterable view
 */
export interface FilterState {
  filters: FilterRule[];
  search: string | null;
  sortBy: string | null;
  sortOrder: SortOrder;
  page: number;
  pageSize: number;
}

/**
 * Filter State Manager Service
 *
 * Manages the complete filter state for a view/component.
 * Provides methods to manipulate filters, sorting, pagination, and search.
 *
 * Usage:
 * ```typescript
 * // In component
 * filterManager = new FilterStateManager();
 *
 * // Add filter
 * filterManager.addFilter({ field: 'title', operation: 'ilike', value: 'test' });
 *
 * // Get current state
 * const state = filterManager.getState();
 * ```
 */
@Injectable({
  providedIn: "root",
})
export class FilterStateManager {
  private defaultState: FilterState = {
    filters: [],
    search: null,
    sortBy: null,
    sortOrder: SortOrder.DESC,
    page: 1,
    pageSize: 20,
  };

  private _state = new BehaviorSubject<FilterState>({ ...this.defaultState });
  public state$ = this._state.asObservable();

  // ===========================================================================
  // STATE GETTERS
  // ===========================================================================

  getState(): FilterState {
    return { ...this._state.value };
  }

  getFilters(): FilterRule[] {
    return [...this._state.value.filters];
  }

  getSearch(): string | null {
    return this._state.value.search;
  }

  // ===========================================================================
  // FILTER MANAGEMENT
  // ===========================================================================

  /**
   * Add a new filter rule
   */
  addFilter(filter: FilterRule): void {
    const state = this._state.value;
    this._state.next({
      ...state,
      filters: [...state.filters, filter],
      page: 1, // Reset to first page
    });
  }

  /**
   * Update an existing filter by field name
   */
  updateFilter(field: string, updates: Partial<FilterRule>): void {
    const state = this._state.value;
    const filters = state.filters.map((f) =>
      f.field === field ? { ...f, ...updates } : f,
    );
    this._state.next({ ...state, filters, page: 1 });
  }

  /**
   * Remove a filter by field name
   */
  removeFilter(field: string): void {
    const state = this._state.value;
    this._state.next({
      ...state,
      filters: state.filters.filter((f) => f.field !== field),
      page: 1,
    });
  }

  /**
   * Remove filter at specific index
   */
  removeFilterAtIndex(index: number): void {
    const state = this._state.value;
    const filters = [...state.filters];
    filters.splice(index, 1);
    this._state.next({ ...state, filters, page: 1 });
  }

  /**
   * Set all filters at once
   */
  setFilters(filters: FilterRule[]): void {
    const state = this._state.value;
    this._state.next({ ...state, filters, page: 1 });
  }

  /**
   * Clear all filters
   */
  clearFilters(): void {
    const state = this._state.value;
    this._state.next({ ...state, filters: [], page: 1 });
  }

  // ===========================================================================
  // SEARCH MANAGEMENT
  // ===========================================================================

  /**
   * Set search query
   */
  setSearch(search: string | null): void {
    const state = this._state.value;
    this._state.next({ ...state, search, page: 1 });
  }

  /**
   * Clear search
   */
  clearSearch(): void {
    this.setSearch(null);
  }

  // ===========================================================================
  // SORT MANAGEMENT
  // ===========================================================================

  /**
   * Set sort field and order
   */
  setSort(sortBy: string | null, sortOrder?: SortOrder): void {
    const state = this._state.value;
    this._state.next({
      ...state,
      sortBy,
      sortOrder: sortOrder ?? state.sortOrder,
    });
  }

  /**
   * Toggle sort for a field
   */
  toggleSort(field: string): void {
    const state = this._state.value;
    const newOrder =
      state.sortBy === field && state.sortOrder === SortOrder.ASC
        ? SortOrder.DESC
        : SortOrder.ASC;
    this._state.next({ ...state, sortBy: field, sortOrder: newOrder });
  }

  // ===========================================================================
  // PAGINATION MANAGEMENT
  // ===========================================================================

  /**
   * Set current page
   */
  setPage(page: number): void {
    const state = this._state.value;
    this._state.next({ ...state, page });
  }

  /**
   * Set page size
   */
  setPageSize(pageSize: number): void {
    const state = this._state.value;
    this._state.next({ ...state, pageSize, page: 1 });
  }

  /**
   * Go to next page
   */
  nextPage(): void {
    const state = this._state.value;
    this._state.next({ ...state, page: state.page + 1 });
  }

  /**
   * Go to previous page
   */
  previousPage(): void {
    const state = this._state.value;
    if (state.page > 1) {
      this._state.next({ ...state, page: state.page - 1 });
    }
  }

  // ===========================================================================
  // FULL STATE MANAGEMENT
  // ===========================================================================

  /**
   * Set complete state at once
   */
  setState(state: Partial<FilterState>): void {
    this._state.next({ ...this._state.value, ...state });
  }

  /**
   * Reset to default state
   */
  reset(): void {
    this._state.next({ ...this.defaultState });
  }

  /**
   * Reset with custom defaults
   */
  resetWithDefaults(defaults: Partial<FilterState>): void {
    this._state.next({ ...this.defaultState, ...defaults });
  }

  // ===========================================================================
  // URL QUERY PARAMS HELPERS
  // ===========================================================================

  /**
   * Convert current state to URL query params object
   */
  toQueryParams(): Record<string, string> {
    const state = this._state.value;
    const params: Record<string, string> = {};

    // Pagination
    params["page"] = String(state.page);
    params["size"] = String(state.pageSize);

    // Sorting
    if (state.sortBy) {
      params["sort_by"] = state.sortBy;
      params["order"] = state.sortOrder;
    }

    // Search
    if (state.search) {
      params["search"] = state.search;
    }

    // Filters (URL grammar: field_operation=value)
    for (const filter of state.filters) {
      const key = `${filter.field}_${filter.operation}`;
      if (Array.isArray(filter.value)) {
        params[key] = filter.value.join(",");
      } else if (filter.value !== null && filter.value !== undefined) {
        params[key] = String(filter.value);
      }
    }

    return params;
  }

  /**
   * Load state from URL query params
   */
  fromQueryParams(
    params: Record<string, string>,
    fields: FilterableField[],
  ): void {
    const state: Partial<FilterState> = {};

    // Pagination
    if (params["page"]) {
      state.page = parseInt(params["page"], 10) || 1;
    }
    if (params["size"]) {
      state.pageSize = parseInt(params["size"], 10) || 20;
    }

    // Sorting
    if (params["sort_by"]) {
      state.sortBy = params["sort_by"];
    }
    if (params["order"]) {
      state.sortOrder = params["order"] as SortOrder;
    }

    // Search
    if (params["search"]) {
      state.search = params["search"];
    }

    // Filters - parse field_operation=value patterns
    const filters: FilterRule[] = [];
    const fieldNames = fields.map((f) => f.name);
    const operations = Object.values(FilterOperation);

    for (const [key, value] of Object.entries(params)) {
      // Skip known params
      if (["page", "size", "sort_by", "order", "search"].includes(key)) {
        continue;
      }

      // Try to parse as field_operation
      for (const op of operations) {
        const suffix = `_${op}`;
        if (key.endsWith(suffix)) {
          const fieldName = key.slice(0, -suffix.length);
          if (fieldNames.includes(fieldName)) {
            filters.push({
              field: fieldName,
              operation: op,
              value: this.parseFilterValue(value, op),
            });
            break;
          }
        }
      }
    }

    if (filters.length > 0) {
      state.filters = filters;
    }

    this.setState(state);
  }

  /**
   * Parse filter value based on operation type
   */
  private parseFilterValue(value: string, operation: string): any {
    // Handle null/boolean values
    if (value.toLowerCase() === "true") return true;
    if (value.toLowerCase() === "false") return false;
    if (value.toLowerCase() === "null") return null;

    // Handle list values
    if (
      [FilterOperation.IN, FilterOperation.NOT_IN].includes(
        operation as FilterOperation,
      )
    ) {
      return value.split(",").map((v) => this.parseScalarValue(v.trim()));
    }

    // Handle range values
    if (operation === FilterOperation.BETWEEN) {
      const parts = value
        .split(",")
        .map((v) => this.parseScalarValue(v.trim()));
      return parts.length === 2 ? parts : value;
    }

    return this.parseScalarValue(value);
  }

  /**
   * Parse a scalar value (try number first)
   */
  private parseScalarValue(value: string): any {
    if (value.toLowerCase() === "true") return true;
    if (value.toLowerCase() === "false") return false;
    if (value.toLowerCase() === "null") return null;

    const num = Number(value);
    if (!isNaN(num) && value.trim() !== "") {
      return num;
    }

    return value;
  }
}
