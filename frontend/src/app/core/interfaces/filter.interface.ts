import { FilterOperation } from "../enums/filter-operation.enum";

/**
 * Single filter rule with field, operation, and value
 * Matches backend FilterParam/FilterRule schema
 */
export interface FilterRule {
  field: string;
  operation: FilterOperation | string;
  value: any;
}

/**
 * Filter rule with additional UI metadata
 */
export interface FilterRuleWithMeta extends FilterRule {
  id?: string;
  fieldLabel?: string;
  operationLabel?: string;
}
