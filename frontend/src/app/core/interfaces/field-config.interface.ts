import { FilterOperation } from "../enums/filter-operation.enum";

/**
 * Field types for dynamic input rendering
 */
export type FilterFieldType =
  | "text"
  | "number"
  | "boolean"
  | "date"
  | "datetime"
  | "select"
  | "enum";

/**
 * Configuration for a filterable field
 * Used by components to dynamically render filter UI
 */
export interface FilterableField {
  /** Internal field name (used in API queries) */
  name: string;
  /** Display label for UI */
  label: string;
  /** Data type of the field */
  type: FilterFieldType;
  /** Available options for select/enum types */
  options?: Array<{ label: string; value: any }>;
  /** Whether the field is sortable */
  sortable?: boolean;
  /** Whether the field is searchable */
  searchable?: boolean;
  /** Default filter operation for this field */
  defaultOperation?: FilterOperation;
  /** Allowed operations for this field (if not all operations apply) */
  allowedOperations?: FilterOperation[];
}

/**
 * Get available operations for a field type
 */
export function getOperationsForFieldType(
  fieldType: FilterFieldType,
): FilterOperation[] {
  switch (fieldType) {
    case "text":
      return [
        FilterOperation.EQUALS,
        FilterOperation.NOT_EQUALS,
        FilterOperation.LIKE,
        FilterOperation.ILIKE,
        FilterOperation.IN,
        FilterOperation.NOT_IN,
        FilterOperation.IS_NULL,
        FilterOperation.IS_NOT_NULL,
        FilterOperation.STARTS_WITH,
        FilterOperation.ENDS_WITH,
      ];
    case "number":
      return [
        FilterOperation.EQUALS,
        FilterOperation.NOT_EQUALS,
        FilterOperation.GREATER_THAN,
        FilterOperation.GREATER_EQUAL,
        FilterOperation.LESS_THAN,
        FilterOperation.LESS_EQUAL,
        FilterOperation.IN,
        FilterOperation.NOT_IN,
        FilterOperation.IS_NULL,
        FilterOperation.IS_NOT_NULL,
        FilterOperation.BETWEEN,
      ];
    case "boolean":
      return [
        FilterOperation.EQUALS,
        FilterOperation.NOT_EQUALS,
        FilterOperation.IS_NULL,
        FilterOperation.IS_NOT_NULL,
      ];
    case "date":
    case "datetime":
      return [
        FilterOperation.EQUALS,
        FilterOperation.NOT_EQUALS,
        FilterOperation.GREATER_THAN,
        FilterOperation.GREATER_EQUAL,
        FilterOperation.LESS_THAN,
        FilterOperation.LESS_EQUAL,
        FilterOperation.IS_NULL,
        FilterOperation.IS_NOT_NULL,
        FilterOperation.BETWEEN,
      ];
    case "select":
    case "enum":
      return [
        FilterOperation.EQUALS,
        FilterOperation.NOT_EQUALS,
        FilterOperation.IN,
        FilterOperation.NOT_IN,
        FilterOperation.IS_NULL,
        FilterOperation.IS_NOT_NULL,
      ];
    default:
      return [
        FilterOperation.EQUALS,
        FilterOperation.NOT_EQUALS,
        FilterOperation.IS_NULL,
        FilterOperation.IS_NOT_NULL,
      ];
  }
}

/**
 * Table column configuration
 */
export interface TableColumn<T = any> {
  /** Field name in the data object */
  field: string;
  /** Display header label */
  header: string;
  /** Whether the column is sortable */
  sortable?: boolean;
  /** Column width (CSS value) */
  width?: string;
  /** Custom cell template type */
  type?:
    | "text"
    | "date"
    | "datetime"
    | "number"
    | "boolean"
    | "currency"
    | "custom";
  /** Custom formatter function */
  formatter?: (value: any, row: T) => string;
  /** CSS class for the column */
  cssClass?: string;
}
