export enum SortOrder {
  ASC = "asc",
  DESC = "desc",
}

export const SORT_ORDER_LABELS: Record<SortOrder, string> = {
  [SortOrder.ASC]: "Ascending",
  [SortOrder.DESC]: "Descending",
};
