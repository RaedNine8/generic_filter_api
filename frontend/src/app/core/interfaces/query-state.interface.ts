import { FilterRule } from "./filter.interface";
import { FilterTreeNode } from "./filter-tree.interface";
import { PaginationParams, SortParams } from "./pagination.interface";

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
 * Query state for tracking current filter/pagination/sort state.
 *
 * Supports both:
 *   - filterTree: the new boolean expression tree (used with POST endpoints)
 *   - filters: legacy flat list (used with URL grammar GET endpoints)
 */
export interface QueryState {
  filterTree: FilterTreeNode | null;
  filters: FilterRule[];
  pagination: PaginationParams;
  sort: SortParams;
  search: string | null;
}
