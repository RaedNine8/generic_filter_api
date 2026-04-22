export enum FilterOperation {
  EQUALS = "eq",
  NOT_EQUALS = "ne",
  GREATER_THAN = "gt",
  GREATER_EQUAL = "gte",
  LESS_THAN = "lt",
  LESS_EQUAL = "lte",
  LIKE = "like",
  ILIKE = "ilike",
  STARTS_WITH = "starts_with",
  ENDS_WITH = "ends_with",
  IN = "in",
  NOT_IN = "not_in",
  IS_NULL = "is_null",
  IS_NOT_NULL = "is_not_null",
  BETWEEN = "between",
}

export const FILTER_OPERATION_LABELS: Record<FilterOperation, string> = {
  [FilterOperation.EQUALS]: "Equals",
  [FilterOperation.NOT_EQUALS]: "Not Equals",
  [FilterOperation.GREATER_THAN]: "Greater Than",
  [FilterOperation.GREATER_EQUAL]: "Greater or Equal",
  [FilterOperation.LESS_THAN]: "Less Than",
  [FilterOperation.LESS_EQUAL]: "Less or Equal",
  [FilterOperation.LIKE]: "Contains (case-sensitive)",
  [FilterOperation.ILIKE]: "Contains",
  [FilterOperation.STARTS_WITH]: "Starts With",
  [FilterOperation.ENDS_WITH]: "Ends With",
  [FilterOperation.IN]: "In List",
  [FilterOperation.NOT_IN]: "Not In List",
  [FilterOperation.IS_NULL]: "Is Empty",
  [FilterOperation.IS_NOT_NULL]: "Is Not Empty",
  [FilterOperation.BETWEEN]: "Between",
};

export function operationNeedsValue(operation: FilterOperation): boolean {
  return ![FilterOperation.IS_NULL, FilterOperation.IS_NOT_NULL].includes(
    operation,
  );
}

export function operationNeedsMultipleValues(
  operation: FilterOperation,
): boolean {
  return [FilterOperation.IN, FilterOperation.NOT_IN].includes(operation);
}

export function operationNeedsRange(operation: FilterOperation): boolean {
  return operation === FilterOperation.BETWEEN;
}
