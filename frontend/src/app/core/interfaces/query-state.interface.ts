import { FilterRule } from "./filter.interface";
import { FilterTreeNode } from "./filter-tree.interface";
import { PaginationParams, SortParams } from "./pagination.interface";

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

export interface QueryState {
  filterTree: FilterTreeNode | null;
  filters: FilterRule[];
  pagination: PaginationParams;
  sort: SortParams;
  search: string | null;
}
