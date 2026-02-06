import { SortOrder } from "../enums/sort-order.enum";

/**
 * Pagination parameters for requests
 * Matches backend GenericPaginationParams
 */
export interface PaginationParams {
  page: number;
  size: number;
}

/**
 * Pagination metadata from API responses
 * Matches backend PaginatedResponseMetadata
 */
export interface PaginationMeta {
  page: number;
  size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

/**
 * Sort parameters for requests
 * Matches backend GenericSortParams
 */
export interface SortParams {
  sort_by: string | null;
  order: SortOrder;
}

/**
 * Generic paginated response from API
 * Matches backend GenericPaginatedResponse
 */
export interface PaginatedResponse<T> {
  data: T[];
  meta: PaginationMeta;
}

/**
 * Complete query parameters combining pagination, sorting, filtering, and search
 */
export interface QueryParams {
  page?: number;
  size?: number;
  sort_by?: string;
  order?: SortOrder;
  search?: string;
  [key: string]: any; // For dynamic filter params (field_operation=value)
}
