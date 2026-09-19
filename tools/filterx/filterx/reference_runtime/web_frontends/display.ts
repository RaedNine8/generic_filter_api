import type {
  EntityConfig,
  FieldConfig,
  FilterxRow,
  PresentationConfig,
  QueryResponse,
  QueryState,
  FilterGroup,
} from "./contracts";
import { FILTERX_PRESENTATION } from "./presentation";

const presentation: PresentationConfig = FILTERX_PRESENTATION;
export const entityLabel = (entity: EntityConfig): string =>
  presentation[entity.name]?.label ?? entity.name;
export const fieldLabel = (entity: EntityConfig, field: FieldConfig): string =>
  presentation[entity.name]?.labels?.[field.name] ?? field.name;

// Display-only intersection: never rewrite schema metadata or query field names.
// Fields absent from all returned rows remain hidden (including backend-redacted fields).
export function visibleFields(
  entity: EntityConfig,
  rows: FilterxRow[],
): FieldConfig[] {
  const columns = presentation[entity.name]?.columns;
  const fields =
    columns === undefined
      ? entity.fields
      : [...new Set(columns)].flatMap((name) =>
          entity.fields.filter((field) => field.name === name),
        );
  return fields.filter((field) =>
    rows.some((row) => Object.prototype.hasOwnProperty.call(row, field.name)),
  );
}
export const cellText = (value: unknown): string =>
  typeof value === "object"
    ? (JSON.stringify(value) ?? "")
    : String(value ?? "");
export const initialState = (entity?: EntityConfig): QueryState => ({
  page: 1,
  size: 20,
  search: "",
  sortBy: entity?.fields[0]?.name ?? "",
  order: "asc",
});
export const emptyGroup = (): FilterGroup => ({
  node_type: "group",
  operator: "AND",
  children: [],
});
export const emptyResult = (): QueryResponse<FilterxRow> => ({
  data: [],
  meta: { page: 1, size: 20, total_items: 0, total_pages: 0 },
});
