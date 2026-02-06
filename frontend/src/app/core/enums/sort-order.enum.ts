/**
 * Sort Order Enum
 * Matches the backend SortOrder enum values
 */
export enum SortOrder {
  ASC = "asc",
  DESC = "desc",
}

/**
 * Human-readable labels for sort orders
 */
export const SORT_ORDER_LABELS: Record<SortOrder, string> = {
  [SortOrder.ASC]: "Ascending",
  [SortOrder.DESC]: "Descending",
};
