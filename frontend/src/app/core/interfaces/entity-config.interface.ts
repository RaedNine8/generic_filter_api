import { FilterRule } from "./filter.interface";
import { FilterOperation } from "../enums/filter-operation.enum";
import { SortOrder } from "../enums/sort-order.enum";

/**
 * Field type definitions for filtering
 */
export type FieldType =
  | "text"
  | "number"
  | "boolean"
  | "date"
  | "datetime"
  | "select";

/**
 * Option for select fields
 */
export interface SelectOption {
  label: string;
  value: string | number | boolean;
}

/**
 * Configuration for a filterable/sortable field
 */
export interface FieldConfig {
  /** Field name (can use dot notation for relations, e.g., 'author.country') */
  name: string;
  /** Human-readable label */
  label: string;
  /** Field type - determines available operations and input type */
  type: FieldType;
  /** Whether this field can be sorted */
  sortable?: boolean;
  /** Whether this field is searchable (included in search query) */
  searchable?: boolean;
  /** Default filter operation for this field */
  defaultOperation?: FilterOperation;
  /** Options for select type fields */
  options?: SelectOption[];
  /** Custom format function for display */
  format?: (value: unknown) => string;
}

/**
 * Configuration for a table column
 */
export interface ColumnConfig<T = unknown> {
  /** Field name (can use dot notation) */
  field: string;
  /** Column header text */
  header: string;
  /** Whether column is sortable */
  sortable?: boolean;
  /** Display type for formatting */
  type?:
    | "text"
    | "number"
    | "currency"
    | "date"
    | "datetime"
    | "boolean"
    | "custom";
  /** Column width (CSS value) */
  width?: string;
  /** Custom cell template identifier */
  template?: string;
  /** Custom format function */
  format?: (value: unknown, row: T) => string;
}

/**
 * Quick filter preset configuration
 */
export interface QuickFilterConfig {
  /** Unique identifier */
  id: string;
  /** Display label */
  label: string;
  /** Optional icon (emoji or icon class) */
  icon?: string;
  /** Category for grouping (e.g., 'Status', 'Date', 'Type') */
  category?: string;
  /** Filter rules to apply */
  filters: FilterRule[];
  /** Whether this is a header/separator */
  isHeader?: boolean;
}

/**
 * Group by option configuration
 */
export interface GroupByConfig {
  /** Field to group by */
  field: string;
  /** Display label */
  label: string;
  /** Optional icon */
  icon?: string;
}

/**
 * Default values for pagination/sorting
 */
export interface DefaultsConfig {
  /** Default page size */
  pageSize?: number;
  /** Default sort field */
  sortField?: string | null;
  /** Default sort order */
  sortOrder?: SortOrder;
  /** Available page size options */
  pageSizeOptions?: number[];
}

/**
 * Complete entity configuration for the filtering system
 * This is what you define per-entity to configure the generic components
 */
export interface EntityConfig<T = unknown> {
  /** Entity name (used for API calls and saved filters) */
  name: string;

  /** Human-readable plural label (e.g., 'Books', 'Users') */
  pluralLabel: string;

  /** Human-readable singular label (e.g., 'Book', 'User') */
  singularLabel: string;

  /** API endpoint base path (e.g., '/api/books') */
  apiEndpoint: string;

  /** Search placeholder text */
  searchPlaceholder?: string;

  /** Empty state message */
  emptyMessage?: string;

  /** Filterable/sortable fields configuration */
  fields: FieldConfig[];

  /** Table columns configuration */
  columns: ColumnConfig<T>[];

  /** Quick filter presets (optional) */
  quickFilters?: QuickFilterConfig[];

  /** Group by options (optional) */
  groupByOptions?: GroupByConfig[];

  /** Default pagination/sorting values */
  defaults?: DefaultsConfig;
}

/**
 * Helper function to create a field config with sensible defaults
 */
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

/**
 * Helper function to create a column config
 */
export function createColumnConfig<T>(
  field: string,
  header: string,
  options?: Partial<ColumnConfig<T>>,
): ColumnConfig<T> {
  return { field, header, sortable: true, ...options };
}

/**
 * Helper function to create a quick filter config
 */
export function createQuickFilter(
  id: string,
  label: string,
  filters: FilterRule[],
  options?: Partial<QuickFilterConfig>,
): QuickFilterConfig {
  return { id, label, filters, ...options };
}
