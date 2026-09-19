export type FilterOperator =
  | "eq"
  | "ne"
  | "gt"
  | "gte"
  | "lt"
  | "lte"
  | "like"
  | "ilike"
  | "starts_with"
  | "ends_with"
  | "in"
  | "not_in"
  | "between"
  | "is_null"
  | "is_not_null";
export type FilterNode = FilterCondition | FilterGroup;
export interface FilterCondition {
  node_type: "condition";
  field: string;
  operation: FilterOperator;
  value?: unknown;
}
export interface FilterGroup {
  node_type: "group";
  operator: "AND" | "OR";
  children: FilterNode[];
}
export interface QueryMeta {
  page: number;
  size: number;
  total_items: number;
  total_pages: number;
}
export interface QueryResponse<T> {
  data: T[];
  meta: QueryMeta;
}
export interface GroupBucket {
  key: unknown;
  count: number;
}
export interface FieldConfig {
  name: string;
  type: string;
  nullable: boolean;
  operations: FilterOperator[];
  enumValues: string[];
}
export interface EntityConfig {
  name: string;
  table: string;
  route: string;
  fields: FieldConfig[];
  relationships: { name: string; target: string; collection: boolean }[];
}
export interface QueryState {
  page: number;
  size: number;
  search: string;
  sortBy: string;
  order: "asc" | "desc";
  filterTree?: FilterNode;
}
export type EntityPresentation = {
  label?: string;
  columns?: string[];
  labels?: Record<string, string>;
};
export type PresentationConfig = Record<string, EntityPresentation>;
export type FilterxRow = Record<string, unknown>;
export interface FilterxContext {
  entity: EntityConfig;
  rows: FilterxRow[];
  state: QueryState;
  meta: QueryMeta;
  groups: GroupBucket[];
  loading: boolean;
  error: string;
  refresh: () => void;
}
export interface FilterxCellContext extends FilterxContext {
  row: FilterxRow;
  rowIndex: number;
  field: FieldConfig;
  value: unknown;
}
