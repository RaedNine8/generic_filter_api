import { FilterRule } from "./filter.interface";
import { FilterOperation } from "../enums/filter-operation.enum";
import { SortOrder } from "../enums/sort-order.enum";

export type FieldType =
  | "text"
  | "number"
  | "boolean"
  | "date"
  | "datetime"
  | "select";

export interface SelectOption {
  label: string;
  value: string | number | boolean;
}

export interface FieldConfig {
  name: string;
  label: string;
  type: FieldType;
  sortable?: boolean;
  searchable?: boolean;
  defaultOperation?: FilterOperation;
  options?: SelectOption[];
  format?: (value: unknown) => string;
}

export interface ColumnConfig<T = unknown> {
  field: string;
  header: string;
  sortable?: boolean;
  type?:
    | "text"
    | "number"
    | "currency"
    | "date"
    | "datetime"
    | "boolean"
    | "custom";
  width?: string;
  template?: string;
  format?: (value: unknown, row: T) => string;
}

export interface QuickFilterConfig {
  id: string;
  label: string;
  icon?: string;
  category?: string;
  filters: FilterRule[];
  isHeader?: boolean;
}

export interface GroupByConfig {
  field: string;
  label: string;
  icon?: string;
}

export interface DefaultsConfig {
  pageSize?: number;
  sortField?: string | null;
  sortOrder?: SortOrder;
  pageSizeOptions?: number[];
}

export interface EntityConfig<T = unknown> {
  name: string;

  pluralLabel: string;

  singularLabel: string;

  apiEndpoint: string;

  searchPlaceholder?: string;

  emptyMessage?: string;

  fields: FieldConfig[];

  columns: ColumnConfig<T>[];

  quickFilters?: QuickFilterConfig[];

  groupByOptions?: GroupByConfig[];

  defaults?: DefaultsConfig;
}

export function createFieldConfig(
  name: string,
  label: string,
  type: FieldType,
  options?: Partial<FieldConfig>,
): FieldConfig {
  const defaults: Partial<FieldConfig> = {
    sortable: true,
    searchable: type === "text",
  };

  if (type === "text") {
    defaults.defaultOperation = FilterOperation.ILIKE;
  } else if (type === "number" || type === "date" || type === "datetime") {
    defaults.defaultOperation = FilterOperation.EQUALS;
  } else if (type === "boolean") {
    defaults.defaultOperation = FilterOperation.EQUALS;
  }

  return { name, label, type, ...defaults, ...options };
}

export function createColumnConfig<T>(
  field: string,
  header: string,
  options?: Partial<ColumnConfig<T>>,
): ColumnConfig<T> {
  return { field, header, sortable: true, ...options };
}

export function createQuickFilter(
  id: string,
  label: string,
  filters: FilterRule[],
  options?: Partial<QuickFilterConfig>,
): QuickFilterConfig {
  return { id, label, filters, ...options };
}
