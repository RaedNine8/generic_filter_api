import { FilterOperation } from "../enums/filter-operation.enum";

export interface FilterRule {
  field: string;
  operation: FilterOperation | string;
  value: any;
}

export interface FilterRuleWithMeta extends FilterRule {
  id?: string;
  fieldLabel?: string;
  operationLabel?: string;
}
