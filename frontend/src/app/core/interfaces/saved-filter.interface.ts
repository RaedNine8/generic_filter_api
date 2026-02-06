import { FilterRule } from "./filter.interface";
import { SortOrder } from "../enums/sort-order.enum";

/**
 * Saved filter response from API
 * Matches backend SavedFilterResponse
 */
export interface SavedFilter {
  id: number;
  name: string;
  description?: string | null;
  model_name: string;
  filters: FilterRule[];
  sort_by?: string | null;
  sort_order: SortOrder | string;
  page_size: number;
  search_query?: string | null;
  created_at: string;
  updated_at?: string | null;
}

/**
 * Request body to create a new saved filter
 * Matches backend SavedFilterCreate
 */
export interface SavedFilterCreate {
  name: string;
  description?: string;
  model_name: string;
  filters: FilterRule[];
  sort_by?: string;
  sort_order?: SortOrder | string;
  page_size?: number;
  search_query?: string;
}

/**
 * Request body to update an existing saved filter
 * Matches backend SavedFilterUpdate
 */
export interface SavedFilterUpdate {
  name?: string;
  description?: string;
  filters?: FilterRule[];
  sort_by?: string;
  sort_order?: SortOrder | string;
  page_size?: number;
  search_query?: string;
}

/**
 * Response when applying a saved filter
 */
export interface SavedFilterApplyResponse<T = any> {
  data: T[];
  meta: {
    page: number;
    size: number;
    total_items: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
  };
}
