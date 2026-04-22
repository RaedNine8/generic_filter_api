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

export interface FilterState {
  filters: FilterRule[];
  search: string | null;
  sortBy: string | null;
  sortOrder: SortOrder;
  page: number;
  pageSize: number;
}

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


  getState(): FilterState {
    return { ...this._state.value };
  }

  getFilters(): FilterRule[] {
    return [...this._state.value.filters];
  }

  getSearch(): string | null {
    return this._state.value.search;
  }


  addFilter(filter: FilterRule): void {
    const state = this._state.value;
    this._state.next({
      ...state,
      filters: [...state.filters, filter],
      page: 1,
    });
  }

  updateFilter(field: string, updates: Partial<FilterRule>): void {
    const state = this._state.value;
    const filters = state.filters.map((f) =>
      f.field === field ? { ...f, ...updates } : f,
    );
    this._state.next({ ...state, filters, page: 1 });
  }

  removeFilter(field: string): void {
    const state = this._state.value;
    this._state.next({
      ...state,
      filters: state.filters.filter((f) => f.field !== field),
      page: 1,
    });
  }

  removeFilterAtIndex(index: number): void {
    const state = this._state.value;
    const filters = [...state.filters];
    filters.splice(index, 1);
    this._state.next({ ...state, filters, page: 1 });
  }

  setFilters(filters: FilterRule[]): void {
    const state = this._state.value;
    this._state.next({ ...state, filters, page: 1 });
  }

  clearFilters(): void {
    const state = this._state.value;
    this._state.next({ ...state, filters: [], page: 1 });
  }


  setSearch(search: string | null): void {
    const state = this._state.value;
    this._state.next({ ...state, search, page: 1 });
  }

  clearSearch(): void {
    this.setSearch(null);
  }


  setSort(sortBy: string | null, sortOrder?: SortOrder): void {
    const state = this._state.value;
    this._state.next({
      ...state,
      sortBy,
      sortOrder: sortOrder ?? state.sortOrder,
    });
  }

  toggleSort(field: string): void {
    const state = this._state.value;
    const newOrder =
      state.sortBy === field && state.sortOrder === SortOrder.ASC
        ? SortOrder.DESC
        : SortOrder.ASC;
    this._state.next({ ...state, sortBy: field, sortOrder: newOrder });
  }


  setPage(page: number): void {
    const state = this._state.value;
    this._state.next({ ...state, page });
  }

  setPageSize(pageSize: number): void {
    const state = this._state.value;
    this._state.next({ ...state, pageSize, page: 1 });
  }

  nextPage(): void {
    const state = this._state.value;
    this._state.next({ ...state, page: state.page + 1 });
  }

  previousPage(): void {
    const state = this._state.value;
    if (state.page > 1) {
      this._state.next({ ...state, page: state.page - 1 });
    }
  }


  setState(state: Partial<FilterState>): void {
    this._state.next({ ...this._state.value, ...state });
  }

  reset(): void {
    this._state.next({ ...this.defaultState });
  }

  resetWithDefaults(defaults: Partial<FilterState>): void {
    this._state.next({ ...this.defaultState, ...defaults });
  }


  toQueryParams(): Record<string, string> {
    const state = this._state.value;
    const params: Record<string, string> = {};

    params["page"] = String(state.page);
    params["size"] = String(state.pageSize);

    if (state.sortBy) {
      params["sort_by"] = state.sortBy;
      params["order"] = state.sortOrder;
    }

    if (state.search) {
      params["search"] = state.search;
    }

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

  fromQueryParams(
    params: Record<string, string>,
    fields: FilterableField[],
  ): void {
    const state: Partial<FilterState> = {};

    if (params["page"]) {
      state.page = parseInt(params["page"], 10) || 1;
    }
    if (params["size"]) {
      state.pageSize = parseInt(params["size"], 10) || 20;
    }

    if (params["sort_by"]) {
      state.sortBy = params["sort_by"];
    }
    if (params["order"]) {
      state.sortOrder = params["order"] as SortOrder;
    }

    if (params["search"]) {
      state.search = params["search"];
    }

    const filters: FilterRule[] = [];
    const fieldNames = fields.map((f) => f.name);
    const operations = Object.values(FilterOperation);

    for (const [key, value] of Object.entries(params)) {
      if (["page", "size", "sort_by", "order", "search"].includes(key)) {
        continue;
      }

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

  private parseFilterValue(value: string, operation: string): any {
    if (value.toLowerCase() === "true") return true;
    if (value.toLowerCase() === "false") return false;
    if (value.toLowerCase() === "null") return null;

    if (
      [FilterOperation.IN, FilterOperation.NOT_IN].includes(
        operation as FilterOperation,
      )
    ) {
      return value.split(",").map((v) => this.parseScalarValue(v.trim()));
    }

    if (operation === FilterOperation.BETWEEN) {
      const parts = value
        .split(",")
        .map((v) => this.parseScalarValue(v.trim()));
      return parts.length === 2 ? parts : value;
    }

    return this.parseScalarValue(value);
  }

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
