import { SortOrder } from "../enums/sort-order.enum";

export interface PaginationParams {
  page: number;
  size: number;
}

export interface PaginationMeta {
  page: number;
  size: number;
  total_items: number;
  total_pages: number;
}

export interface SortParams {
  sort_by: string | null;
  order: SortOrder;
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: PaginationMeta;
}

export interface QueryParams {
  page?: number;
  size?: number;
  sort_by?: string;
  order?: SortOrder;
  search?: string;
  [key: string]: any;
}
