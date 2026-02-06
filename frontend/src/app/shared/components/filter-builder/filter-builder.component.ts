import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnInit,
  OnDestroy,
} from "@angular/core";
import { CommonModule } from "@angular/common";
import {
  FormsModule,
  ReactiveFormsModule,
  FormGroup,
  FormBuilder,
  FormArray,
  Validators,
} from "@angular/forms";
import { Subject } from "rxjs";
import { takeUntil, debounceTime } from "rxjs/operators";

import { FilterRule } from "../../../core/interfaces/filter.interface";
import {
  FilterableField,
  getOperationsForFieldType,
} from "../../../core/interfaces/field-config.interface";
import {
  FilterOperation,
  FILTER_OPERATION_LABELS,
  operationNeedsValue,
  operationNeedsMultipleValues,
  operationNeedsRange,
} from "../../../core/enums/filter-operation.enum";

/**
 * Filter Builder Component
 *
 * A reusable component for building filter rules dynamically.
 * Supports multiple field types, operations, and value inputs.
 *
 * Features:
 * - Dynamic field selection based on configuration
 * - Operation selection based on field type
 * - Appropriate value input based on operation
 * - Add/remove filter rules
 * - Clear all filters
 * - Emits filter changes
 *
 * Usage:
 * ```html
 * <app-filter-builder
 *   [fields]="filterableFields"
 *   [filters]="currentFilters"
 *   (filtersChange)="onFiltersChange($event)"
 *   (apply)="onApplyFilters($event)">
 * </app-filter-builder>
 * ```
 */
@Component({
  selector: "app-filter-builder",
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  templateUrl: "./filter-builder.component.html",
  styleUrls: ["./filter-builder.component.scss"],
})
export class FilterBuilderComponent implements OnInit, OnDestroy {
  /** Available fields for filtering */
  @Input() fields: FilterableField[] = [];

  /** Current filter rules */
  @Input() filters: FilterRule[] = [];

  /** Label for the apply button */
  @Input() applyButtonLabel = "Apply Filters";

  /** Show apply button */
  @Input() showApplyButton = true;

  /** Auto-emit on change (if false, only emit on apply) */
  @Input() autoApply = false;

  /** Debounce time for auto-apply (ms) */
  @Input() debounceMs = 300;

  /** Emitted when filters change */
  @Output() filtersChange = new EventEmitter<FilterRule[]>();

  /** Emitted when apply button is clicked */
  @Output() apply = new EventEmitter<FilterRule[]>();

  /** Emitted when clear button is clicked */
  @Output() clear = new EventEmitter<void>();

  form!: FormGroup;
  operationLabels = FILTER_OPERATION_LABELS;

  private destroy$ = new Subject<void>();

  constructor(private fb: FormBuilder) {}

  ngOnInit(): void {
    this.initForm();
    this.loadFilters();

    if (this.autoApply) {
      this.form.valueChanges
        .pipe(takeUntil(this.destroy$), debounceTime(this.debounceMs))
        .subscribe(() => this.emitFilters());
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // ===========================================================================
  // FORM MANAGEMENT
  // ===========================================================================

  private initForm(): void {
    this.form = this.fb.group({
      rules: this.fb.array([]),
    });
  }

  get rules(): FormArray {
    return this.form.get("rules") as FormArray;
  }

  private createRuleGroup(rule?: Partial<FilterRule>): FormGroup {
    const field =
      rule?.field || (this.fields.length > 0 ? this.fields[0].name : "");
    const fieldConfig = this.getFieldConfig(field);
    const defaultOp = fieldConfig?.defaultOperation || FilterOperation.EQUALS;

    return this.fb.group({
      field: [field, Validators.required],
      operation: [rule?.operation || defaultOp, Validators.required],
      value: [rule?.value ?? ""],
      valueEnd: [""], // For BETWEEN operation
    });
  }

  private loadFilters(): void {
    this.rules.clear();
    for (const filter of this.filters) {
      const group = this.createRuleGroup(filter);
      // Handle BETWEEN value
      if (
        filter.operation === FilterOperation.BETWEEN &&
        Array.isArray(filter.value)
      ) {
        group.patchValue({
          value: filter.value[0],
          valueEnd: filter.value[1],
        });
      }
      this.rules.push(group);
    }

    // Add empty rule if none exist
    if (this.rules.length === 0) {
      this.addRule();
    }
  }

  // ===========================================================================
  // RULE MANAGEMENT
  // ===========================================================================

  addRule(): void {
    this.rules.push(this.createRuleGroup());
  }

  removeRule(index: number): void {
    this.rules.removeAt(index);
    if (this.rules.length === 0) {
      this.addRule();
    }
    if (this.autoApply) {
      this.emitFilters();
    }
  }

  clearAllRules(): void {
    this.rules.clear();
    this.addRule();
    this.clear.emit();
    this.filtersChange.emit([]);
  }

  // ===========================================================================
  // FIELD/OPERATION HELPERS
  // ===========================================================================

  getFieldConfig(fieldName: string): FilterableField | undefined {
    return this.fields.find((f) => f.name === fieldName);
  }

  getAvailableOperations(fieldName: string): FilterOperation[] {
    const field = this.getFieldConfig(fieldName);
    if (!field) {
      return Object.values(FilterOperation);
    }

    if (field.allowedOperations && field.allowedOperations.length > 0) {
      return field.allowedOperations;
    }

    return getOperationsForFieldType(field.type);
  }

  onFieldChange(index: number): void {
    const ruleGroup = this.rules.at(index) as FormGroup;
    const fieldName = ruleGroup.get("field")?.value;
    const operations = this.getAvailableOperations(fieldName);

    // Reset operation to first available if current is not valid
    const currentOp = ruleGroup.get("operation")?.value;
    if (!operations.includes(currentOp)) {
      ruleGroup.patchValue({
        operation: operations[0],
        value: "",
        valueEnd: "",
      });
    }
  }

  onOperationChange(index: number): void {
    const ruleGroup = this.rules.at(index) as FormGroup;
    // Reset value when operation changes
    ruleGroup.patchValue({ value: "", valueEnd: "" });
  }

  needsValue(operation: string): boolean {
    return operationNeedsValue(operation as FilterOperation);
  }

  needsMultipleValues(operation: string): boolean {
    return operationNeedsMultipleValues(operation as FilterOperation);
  }

  needsRange(operation: string): boolean {
    return operationNeedsRange(operation as FilterOperation);
  }

  getInputType(fieldName: string): string {
    const field = this.getFieldConfig(fieldName);
    switch (field?.type) {
      case "number":
        return "number";
      case "date":
        return "date";
      case "datetime":
        return "datetime-local";
      default:
        return "text";
    }
  }

  // ===========================================================================
  // OUTPUT
  // ===========================================================================

  applyFilters(): void {
    const filters = this.buildFilters();
    this.apply.emit(filters);
    this.filtersChange.emit(filters);
  }

  private emitFilters(): void {
    const filters = this.buildFilters();
    this.filtersChange.emit(filters);
  }

  private buildFilters(): FilterRule[] {
    const filters: FilterRule[] = [];

    for (const control of this.rules.controls) {
      const group = control as FormGroup;
      const field = group.get("field")?.value;
      const operation = group.get("operation")?.value;
      let value = group.get("value")?.value;
      const valueEnd = group.get("valueEnd")?.value;

      // Skip empty rules
      if (!field || !operation) continue;

      // Skip if value is required but empty
      if (
        this.needsValue(operation) &&
        (value === "" || value === null || value === undefined)
      ) {
        continue;
      }

      // Handle special operations
      if (operation === FilterOperation.BETWEEN) {
        if (value !== "" && valueEnd !== "") {
          value = [value, valueEnd];
        } else {
          continue; // Skip incomplete BETWEEN
        }
      } else if (this.needsMultipleValues(operation)) {
        // Parse comma-separated values
        if (typeof value === "string") {
          value = value
            .split(",")
            .map((v: string) => v.trim())
            .filter((v: string) => v !== "");
          if (value.length === 0) continue;
        }
      }

      filters.push({ field, operation, value });
    }

    return filters;
  }
}
