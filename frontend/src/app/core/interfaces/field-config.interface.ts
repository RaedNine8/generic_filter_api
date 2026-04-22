import { FilterOperation } from "../enums/filter-operation.enum";

export type FilterFieldType =
  | "text"
  | "number"
  | "boolean"
  | "date"
  | "datetime"
  | "select"
  | "enum";

export interface FilterableField {
  name: string;
  label: string;
  type: FilterFieldType;
  options?: Array<{ label: string; value: any }>;
  sortable?: boolean;
  searchable?: boolean;
  defaultOperation?: FilterOperation;
  allowedOperations?: FilterOperation[];
}

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

export interface TableColumn<T = any> {
  field: string;
  header: string;
  sortable?: boolean;
  width?: string;
  type?:
    | "text"
    | "date"
    | "datetime"
    | "number"
    | "boolean"
    | "currency"
    | "custom";
  formatter?: (value: any, row: T) => string;
  cssClass?: string;
}
