import { FilterRule } from "./filter.interface";
import { SortOrder } from "../enums/sort-order.enum";
import { FilterTreeNode } from "./filter-tree.interface";

export interface SavedFilter {
  id: number;
  name: string;
  description?: string | null;
  model_name: string;
  filters: FilterRule[];
  filter_tree?: FilterTreeNode | null;
  sort_by?: string | null;
  sort_order: SortOrder;
  page_size: number;
  search_query?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface SavedFilterCreate {
  name: string;
  description?: string;
  model_name: string;
  filters: FilterRule[];
  filter_tree?: FilterTreeNode;
  sort_by?: string;
  sort_order?: SortOrder;
  page_size?: number;
  search_query?: string;
}

export interface SavedFilterUpdate {
  name?: string;
  description?: string;
  filters?: FilterRule[];
  filter_tree?: FilterTreeNode;
  sort_by?: string;
  sort_order?: SortOrder;
  page_size?: number;
  search_query?: string;
}

export interface SavedFilterApplyResponse<T = any> {
  data: T[];
  meta: {
    page: number;
    size: number;
    total_items: number;
    total_pages: number;
  };
}
