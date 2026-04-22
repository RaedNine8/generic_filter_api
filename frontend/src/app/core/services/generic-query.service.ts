import { Injectable } from "@angular/core";
import {
  HttpClient,
  HttpParams,
  HttpErrorResponse,
} from "@angular/common/http";
import { Observable, throwError, BehaviorSubject } from "rxjs";
import { catchError, tap } from "rxjs/operators";

import { FilterRule } from "../interfaces/filter.interface";
import {
  FilterTreeNode,
  toBackendPayload,
} from "../interfaces/filter-tree.interface";
import {
  PaginatedResponse,
  QueryParams,
  PaginationParams,
  SortParams,
} from "../interfaces/pagination.interface";
import { FilterOperation } from "../enums/filter-operation.enum";
import { SortOrder } from "../enums/sort-order.enum";
import { ApiError, QueryState } from "../interfaces/query-state.interface";

@Injectable({
  providedIn: "root",
})
export abstract class GenericQueryService<T> {
  protected abstract baseUrl: string;

  protected defaultState: QueryState = {
    filterTree: null,
    filters: [],
    pagination: { page: 1, size: 20 },
    sort: { sort_by: "created_at", order: SortOrder.ASC },
    search: null,
  };

  private _queryState = new BehaviorSubject<QueryState>({
    ...this.defaultState,
  });
  public queryState$ = this._queryState.asObservable();

  private _loading = new BehaviorSubject<boolean>(false);
  public loading$ = this._loading.asObservable();

  private _data = new BehaviorSubject<PaginatedResponse<T> | null>(null);
  public data$ = this._data.asObservable();

  constructor(protected http: HttpClient) {}

  query(): Observable<PaginatedResponse<T>> {
    const state = this._queryState.value;

    if (state.filterTree) {
      return this.queryWithTree(state);
    }
    return this.queryWithUrlGrammar(state);
  }

  queryWithState(state: QueryState): Observable<PaginatedResponse<T>> {
    if (state.filterTree) {
      return this.queryWithTree(state);
    }
    return this.queryWithUrlGrammar(state);
  }

  queryGroupedWithState(
    field: string,
    state: QueryState,
  ): Observable<Array<{ key: unknown; count: number }>> {
    const encodedField = encodeURIComponent(field);
    const params = this.buildFilterSearchParams(state);
    this._loading.next(true);

    const request$ = state.filterTree
      ? (() => {
          const treePayload = toBackendPayload(state.filterTree);
          if (!treePayload) {
            return this.http.get<Array<{ key: unknown; count: number }>>(
              `${this.baseUrl}/group-by/${encodedField}`,
              { params },
            );
          }
          return this.http.post<Array<{ key: unknown; count: number }>>(
            `${this.baseUrl}/group-by/${encodedField}/filter`,
            treePayload,
            { params },
          );
        })()
      : this.http.get<Array<{ key: unknown; count: number }>>(
          `${this.baseUrl}/group-by/${encodedField}`,
          { params },
        );

    return request$.pipe(
      tap(() => {
        this._loading.next(false);
      }),
      catchError((error) => {
        this._loading.next(false);
        return this.handleError(error);
      }),
    );
  }

  getMetadata(): Observable<any> {
    return this.http
      .get<any>(`${this.baseUrl}/metadata`)
      .pipe(catchError((error) => this.handleError(error)));
  }

  private queryWithTree(state: QueryState): Observable<PaginatedResponse<T>> {
    const httpParams = this.buildPaginationSortParams(state);
    const body = toBackendPayload(state.filterTree!);

    if (!body) {
      return this.queryWithUrlGrammar({ ...state, filterTree: null });
    }

    this._loading.next(true);
    return this.http
      .post<PaginatedResponse<T>>(`${this.baseUrl}/filter`, body, {
        params: httpParams,
      })
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

  private queryWithUrlGrammar(
    state: QueryState,
  ): Observable<PaginatedResponse<T>> {
    const httpParams = this.buildHttpParams(state);
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

  getState(): QueryState {
    return { ...this._queryState.value };
  }

  setFilterTree(
    tree: FilterTreeNode | null,
    autoQuery = false,
  ): Observable<PaginatedResponse<T>> | void {
    const state = this._queryState.value;
    this._queryState.next({
      ...state,
      filterTree: tree,
      filters: [],
      pagination: { ...state.pagination, page: 1 },
    });
    if (autoQuery) {
      return this.query();
    }
  }

  setFilters(
    filters: FilterRule[],
    autoQuery = false,
  ): Observable<PaginatedResponse<T>> | void {
    const state = this._queryState.value;
    this._queryState.next({
      ...state,
      filters,
      filterTree: null,
      pagination: { ...state.pagination, page: 1 },
    });
    if (autoQuery) {
      return this.query();
    }
  }

  addFilter(filter: FilterRule): void {
    const state = this._queryState.value;
    this._queryState.next({
      ...state,
      filters: [...state.filters, filter],
      pagination: { ...state.pagination, page: 1 },
    });
  }

  removeFilter(field: string): void {
    const state = this._queryState.value;
    this._queryState.next({
      ...state,
      filters: state.filters.filter((f) => f.field !== field),
      pagination: { ...state.pagination, page: 1 },
    });
  }

  clearFilters(): void {
    const state = this._queryState.value;
    this._queryState.next({
      ...state,
      filters: [],
      filterTree: null,
      pagination: { ...state.pagination, page: 1 },
    });
  }

  setPagination(pagination: Partial<PaginationParams>): void {
    const state = this._queryState.value;
    this._queryState.next({
      ...state,
      pagination: { ...state.pagination, ...pagination },
    });
  }

  goToPage(page: number): Observable<PaginatedResponse<T>> {
    this.setPagination({ page });
    return this.query();
  }

  setPageSize(size: number): Observable<PaginatedResponse<T>> {
    this.setPagination({ page: 1, size });
    return this.query();
  }

  setSort(sort: Partial<SortParams>): void {
    const state = this._queryState.value;
    this._queryState.next({
      ...state,
      sort: { ...state.sort, ...sort },
    });
  }

  toggleSort(field: string): Observable<PaginatedResponse<T>> {
    const state = this._queryState.value;
    const newOrder =
      state.sort.sort_by === field && state.sort.order === SortOrder.ASC
        ? SortOrder.DESC
        : SortOrder.ASC;
    this.setSort({ sort_by: field, order: newOrder });
    return this.query();
  }

  setSearch(search: string | null): void {
    const state = this._queryState.value;
    this._queryState.next({
      ...state,
      search,
      pagination: { ...state.pagination, page: 1 },
    });
  }

  resetState(): void {
    this._queryState.next({ ...this.defaultState });
    this._data.next(null);
  }

  buildUrlParamKey(field: string, operation: FilterOperation | string): string {
    return `${field}_${operation}`;
  }

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

  protected buildHttpParams(params: Partial<QueryState>): HttpParams {
    let httpParams = this.buildPaginationSortParams(params);

    if (params.filters && params.filters.length > 0) {
      const filterParams = this.filterRulesToParams(params.filters);
      Object.entries(filterParams).forEach(([key, value]) => {
        httpParams = httpParams.set(key, value);
      });
    }
    return httpParams;
  }

  protected buildFilterSearchParams(params: Partial<QueryState>): HttpParams {
    let httpParams = new HttpParams();

    if (params.search) {
      httpParams = httpParams.set("search", params.search);
    }

    if (params.filters && params.filters.length > 0) {
      const filterParams = this.filterRulesToParams(params.filters);
      Object.entries(filterParams).forEach(([key, value]) => {
        httpParams = httpParams.set(key, value);
      });
    }

    return httpParams;
  }

  protected buildPaginationSortParams(params: Partial<QueryState>): HttpParams {
    let httpParams = new HttpParams();

    if (params.pagination) {
      httpParams = httpParams.set("page", String(params.pagination.page));
      httpParams = httpParams.set("size", String(params.pagination.size));
    }
    if (params.sort?.sort_by) {
      httpParams = httpParams.set("sort_by", params.sort.sort_by);
      httpParams = httpParams.set("order", params.sort.order);
    }
    if (params.search) {
      httpParams = httpParams.set("search", params.search);
    }
    return httpParams;
  }

  protected handleError = (error: HttpErrorResponse): Observable<never> => {
    let errorMessage: string;
    const status: number = error.status || 0;

    if (error.error instanceof ErrorEvent) {
      errorMessage = `Client Error: ${error.error.message}`;
    } else {
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
