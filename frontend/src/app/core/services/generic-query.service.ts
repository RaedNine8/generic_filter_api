import { Injectable } from "@angular/core";
import {
  HttpClient,
  HttpParams,
  HttpErrorResponse,
} from "@angular/common/http";
import { Observable, throwError, BehaviorSubject } from "rxjs";
import { catchError, map, tap } from "rxjs/operators";

import { FilterRule, FilterRuleWithMeta } from "../interfaces/filter.interface";
import {
  PaginatedResponse,
  QueryParams,
  PaginationParams,
  SortParams,
} from "../interfaces/pagination.interface";
import { FilterOperation } from "../enums/filter-operation.enum";
import { SortOrder } from "../enums/sort-order.enum";

/**
 * Custom error class for API operations
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public originalError?: any,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

/**
 * Query state for tracking current filter/pagination/sort state
 */
export interface QueryState {
  filters: FilterRule[];
  pagination: PaginationParams;
  sort: SortParams;
  search: string | null;
}

/**
 * Generic Query Service
 *
 * A reusable service for querying any API endpoint with filtering,
 * pagination, sorting, and search capabilities.
 *
 * Features:
 * - URL grammar filter building (field_operation=value)
 * - Pagination with page/size
 * - Sorting with field and order
 * - Full-text search
 * - State management for current query
 *
 * Usage:
 * ```typescript
 * @Injectable({ providedIn: 'root' })
 * export class BookService extends GenericQueryService<Book> {
 *   protected baseUrl = '/api/books';
 *   constructor(http: HttpClient) { super(http); }
 * }
 * ```
 */
@Injectable({
  providedIn: "root",
})
export abstract class GenericQueryService<T> {
  protected abstract baseUrl: string;

  // Default query state
  protected defaultState: QueryState = {
    filters: [],
    pagination: { page: 1, size: 20 },
    sort: { sort_by: null, order: SortOrder.DESC },
    search: null,
  };

  // Current query state as observable
  private _queryState = new BehaviorSubject<QueryState>({
    ...this.defaultState,
  });
  public queryState$ = this._queryState.asObservable();

  // Loading state
  private _loading = new BehaviorSubject<boolean>(false);
  public loading$ = this._loading.asObservable();

  // Current data
  private _data = new BehaviorSubject<PaginatedResponse<T> | null>(null);
  public data$ = this._data.asObservable();

  constructor(protected http: HttpClient) {}

  // ===========================================================================
  // QUERY EXECUTION
  // ===========================================================================

  /**
   * Execute query with current state
   */
  query(): Observable<PaginatedResponse<T>> {
    const state = this._queryState.value;
    return this.queryWithParams(state);
  }

  /**
   * Execute query with specific parameters
   */
  queryWithParams(
    params: Partial<QueryState>,
  ): Observable<PaginatedResponse<T>> {
    const httpParams = this.buildHttpParams(params);
    this._loading.next(true);

    return this.http
      .get<PaginatedResponse<T>>(this.baseUrl, { params: httpParams })
      .pipe(
        tap((response) => {
          this._data.next(response);
          this._loading.next(false);
        }),
        catchError((error) => {
          this._loading.next(false);
          return this.handleError(error);
        }),
      );
  }

  /**
   * Execute query with raw query params object
   */
  queryWithRawParams(params: QueryParams): Observable<PaginatedResponse<T>> {
    let httpParams = new HttpParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        httpParams = httpParams.set(key, String(value));
      }
    });

    this._loading.next(true);

    return this.http
      .get<PaginatedResponse<T>>(this.baseUrl, { params: httpParams })
      .pipe(
        tap((response) => {
          this._data.next(response);
          this._loading.next(false);
        }),
        catchError((error) => {
          this._loading.next(false);
          return this.handleError(error);
        }),
      );
  }

  // ===========================================================================
  // STATE MANAGEMENT
  // ===========================================================================

  /**
   * Get current query state
   */
  getState(): QueryState {
    return { ...this._queryState.value };
  }

  /**
   * Update filters and optionally re-query
   */
  setFilters(
    filters: FilterRule[],
    autoQuery = false,
  ): Observable<PaginatedResponse<T>> | void {
    const state = this._queryState.value;
    this._queryState.next({
      ...state,
      filters,
      pagination: { ...state.pagination, page: 1 }, // Reset to page 1 on filter change
    });

    if (autoQuery) {
      return this.query();
    }
  }

  /**
   * Add a single filter
   */
  addFilter(filter: FilterRule): void {
    const state = this._queryState.value;
    this._queryState.next({
      ...state,
      filters: [...state.filters, filter],
      pagination: { ...state.pagination, page: 1 },
    });
  }

  /**
   * Remove a filter by field name
   */
  removeFilter(field: string): void {
    const state = this._queryState.value;
    this._queryState.next({
      ...state,
      filters: state.filters.filter((f) => f.field !== field),
      pagination: { ...state.pagination, page: 1 },
    });
  }

  /**
   * Clear all filters
   */
  clearFilters(): void {
    const state = this._queryState.value;
    this._queryState.next({
      ...state,
      filters: [],
      pagination: { ...state.pagination, page: 1 },
    });
  }

  /**
   * Set pagination
   */
  setPagination(pagination: Partial<PaginationParams>): void {
    const state = this._queryState.value;
    this._queryState.next({
      ...state,
      pagination: { ...state.pagination, ...pagination },
    });
  }

  /**
   * Go to a specific page
   */
  goToPage(page: number): Observable<PaginatedResponse<T>> {
    this.setPagination({ page });
    return this.query();
  }

  /**
   * Change page size
   */
  setPageSize(size: number): Observable<PaginatedResponse<T>> {
    this.setPagination({ page: 1, size });
    return this.query();
  }

  /**
   * Set sorting
   */
  setSort(sort: Partial<SortParams>): void {
    const state = this._queryState.value;
    this._queryState.next({
      ...state,
      sort: { ...state.sort, ...sort },
    });
  }

  /**
   * Toggle sort order for a field
   */
  toggleSort(field: string): Observable<PaginatedResponse<T>> {
    const state = this._queryState.value;
    const newOrder =
      state.sort.sort_by === field && state.sort.order === SortOrder.ASC
        ? SortOrder.DESC
        : SortOrder.ASC;

    this.setSort({ sort_by: field, order: newOrder });
    return this.query();
  }

  /**
   * Set search query
   */
  setSearch(search: string | null): void {
    const state = this._queryState.value;
    this._queryState.next({
      ...state,
      search,
      pagination: { ...state.pagination, page: 1 },
    });
  }

  /**
   * Reset state to defaults
   */
  resetState(): void {
    this._queryState.next({ ...this.defaultState });
    this._data.next(null);
  }

  // ===========================================================================
  // URL GRAMMAR HELPERS
  // ===========================================================================

  /**
   * Build URL parameter key from field and operation
   * Example: buildUrlParamKey('title', 'ilike') => 'title_ilike'
   */
  buildUrlParamKey(field: string, operation: FilterOperation | string): string {
    return `${field}_${operation}`;
  }

  /**
   * Convert filter rules to URL grammar parameters
   */
  filterRulesToParams(rules: FilterRule[]): Record<string, string> {
    const params: Record<string, string> = {};

    for (const rule of rules) {
      const key = this.buildUrlParamKey(rule.field, rule.operation);

      if (Array.isArray(rule.value)) {
        params[key] = rule.value.join(",");
      } else if (typeof rule.value === "boolean") {
        params[key] = rule.value.toString();
      } else if (rule.value !== null && rule.value !== undefined) {
        params[key] = String(rule.value);
      }
    }

    return params;
  }

  /**
   * Build HttpParams from query state
   */
  protected buildHttpParams(params: Partial<QueryState>): HttpParams {
    let httpParams = new HttpParams();

    // Pagination
    if (params.pagination) {
      httpParams = httpParams.set("page", String(params.pagination.page));
      httpParams = httpParams.set("size", String(params.pagination.size));
    }

    // Sorting
    if (params.sort?.sort_by) {
      httpParams = httpParams.set("sort_by", params.sort.sort_by);
      httpParams = httpParams.set("order", params.sort.order);
    }

    // Search
    if (params.search) {
      httpParams = httpParams.set("search", params.search);
    }

    // Filters (URL grammar)
    if (params.filters && params.filters.length > 0) {
      const filterParams = this.filterRulesToParams(params.filters);
      Object.entries(filterParams).forEach(([key, value]) => {
        httpParams = httpParams.set(key, value);
      });
    }

    return httpParams;
  }

  // ===========================================================================
  // ERROR HANDLING
  // ===========================================================================

  protected handleError = (error: HttpErrorResponse): Observable<never> => {
    let errorMessage: string;
    const status: number = error.status || 0;

    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Client Error: ${error.error.message}`;
    } else {
      // Server-side error
      if (error.error?.detail) {
        errorMessage = error.error.detail;
      } else if (error.error?.message) {
        errorMessage = error.error.message;
      } else {
        errorMessage = `Server Error: ${error.message}`;
      }
    }

    console.error("API Error:", {
      status,
      message: errorMessage,
      error: error.error,
    });

    return throwError(() => new ApiError(status, errorMessage, error));
  };
}
