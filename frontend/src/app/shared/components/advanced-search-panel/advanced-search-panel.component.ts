import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnInit,
  OnDestroy,
} from "@angular/core";
import { CommonModule } from "@angular/common";
import { FormsModule } from "@angular/forms";
import { Subject } from "rxjs";
import { takeUntil } from "rxjs/operators";

import { FilterRule } from "../../../core/interfaces/filter.interface";
import {
  SavedFilter,
  SavedFilterCreate,
} from "../../../core/interfaces/saved-filter.interface";
import { FilterableField } from "../../../core/interfaces/field-config.interface";
import {
  FilterOperation,
  FILTER_OPERATION_LABELS,
} from "../../../core/enums/filter-operation.enum";
import { SortOrder } from "../../../core/enums/sort-order.enum";

/**
 * Predefined quick filter configuration
 */
export interface QuickFilter {
  id: string;
  label: string;
  icon?: string;
  filters: FilterRule[];
  /** Category to group filters (e.g., 'Genre', 'Author') */
  category?: string;
  /** If true, this is a separator/header in the list */
  isHeader?: boolean;
  /** If true, shows a dropdown arrow for date filters etc */
  hasSubmenu?: boolean;
}

/**
 * Group by option
 */
export interface GroupByOption {
  field: string;
  label: string;
  icon?: string;
  hasSubmenu?: boolean;
}

/**
 * Advanced Search Panel Component
 *
 * A comprehensive search/filter panel similar to Odoo's search view.
 * Features:
 * - Search bar with active filter tags
 * - Quick filters sidebar (predefined filters)
 * - Group by options
 * - Favorites (saved filters)
 * - Custom filter builder
 */
@Component({
  selector: "app-advanced-search-panel",
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: "./advanced-search-panel.component.html",
  styleUrls: ["./advanced-search-panel.component.scss"],
})
export class AdvancedSearchPanelComponent implements OnInit, OnDestroy {
  // ============ INPUTS ============

  /** Model name for saved filters */
  @Input() modelName = "";

  /** Available fields for filtering */
  @Input() fields: FilterableField[] = [];

  /** Predefined quick filters */
  @Input() quickFilters: QuickFilter[] = [];

  /** Group by options */
  @Input() groupByOptions: GroupByOption[] = [];

  /** Current active filters */
  @Input() activeFilters: FilterRule[] = [];

  /** Current search query */
  @Input() searchQuery = "";

  /** Saved filters from database */
  @Input() savedFilters: SavedFilter[] = [];

  /** Current sort field */
  @Input() sortBy: string | null = null;

  /** Current sort order */
  @Input() sortOrder: SortOrder = SortOrder.DESC;

  /** Current page size */
  @Input() pageSize = 20;

  /** Placeholder text for search input */
  @Input() placeholder = "Search...";

  // ============ OUTPUTS ============

  /** Emitted when filters change */
  @Output() filtersChange = new EventEmitter<FilterRule[]>();

  /** Emitted when search query changes */
  @Output() searchChange = new EventEmitter<string>();

  /** Emitted when group by changes */
  @Output() groupByChange = new EventEmitter<string | null>();

  /** Emitted when a saved filter should be applied */
  @Output() applySavedFilter = new EventEmitter<SavedFilter>();

  /** Emitted when user wants to save current filter */
  @Output() saveFilter = new EventEmitter<SavedFilterCreate>();

  /** Emitted when user wants to delete a saved filter */
  @Output() deleteSavedFilter = new EventEmitter<number>();

  /** Emitted when apply is clicked */
  @Output() apply = new EventEmitter<void>();

  // ============ STATE ============

  /** Is the dropdown panel open */
  isPanelOpen = false;

  /** Currently active quick filter IDs */
  activeQuickFilters: Set<string> = new Set();

  /** Current group by field */
  currentGroupBy: string | null = null;

  /** Show save filter dialog */
  showSaveDialog = false;

  /** New filter name for save dialog */
  newFilterName = "";

  /** New filter description */
  newFilterDescription = "";

  /** Show custom filter builder */
  showCustomFilterBuilder = false;

  /** Custom filter being built */
  customFilter: { field: string; operation: FilterOperation; value: any } = {
    field: "",
    operation: FilterOperation.EQUALS,
    value: "",
  };

  operationLabels = FILTER_OPERATION_LABELS;

  private destroy$ = new Subject<void>();

  ngOnInit(): void {
    if (this.fields.length > 0) {
      this.customFilter.field = this.fields[0].name;
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // ============ PANEL TOGGLE ============

  togglePanel(): void {
    this.isPanelOpen = !this.isPanelOpen;
  }

  closePanel(): void {
    this.isPanelOpen = false;
  }

  // ============ SEARCH ============

  onSearchInput(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.searchChange.emit(value);
  }

  onSearchKeydown(event: KeyboardEvent): void {
    if (event.key === "Enter") {
      this.apply.emit();
    }
  }

  // ============ QUICK FILTERS ============

  toggleQuickFilter(filter: QuickFilter): void {
    if (filter.isHeader) return;

    if (this.activeQuickFilters.has(filter.id)) {
      this.activeQuickFilters.delete(filter.id);
      // Remove the filters associated with this quick filter
      const newFilters = this.activeFilters.filter(
        (af) =>
          !filter.filters.some(
            (qf) => qf.field === af.field && qf.operation === af.operation,
          ),
      );
      this.filtersChange.emit(newFilters);
    } else {
      this.activeQuickFilters.add(filter.id);
      // Add the filters
      const newFilters = [...this.activeFilters, ...filter.filters];
      this.filtersChange.emit(newFilters);
    }

    this.apply.emit();
  }

  isQuickFilterActive(filterId: string): boolean {
    return this.activeQuickFilters.has(filterId);
  }

  // ============ GROUP BY ============

  setGroupBy(field: string | null): void {
    this.currentGroupBy = field;
    this.groupByChange.emit(field);
  }

  // ============ FILTER TAGS ============

  removeFilterTag(index: number): void {
    const newFilters = [...this.activeFilters];
    newFilters.splice(index, 1);
    this.filtersChange.emit(newFilters);
    this.apply.emit();
  }

  clearAllFilters(): void {
    this.activeQuickFilters.clear();
    this.filtersChange.emit([]);
    this.searchChange.emit("");
    this.apply.emit();
  }

  getFilterTagLabel(filter: FilterRule): string {
    const field = this.fields.find((f) => f.name === filter.field);
    const fieldLabel = field?.label || filter.field;
    const opLabel =
      this.operationLabels[filter.operation as FilterOperation] ||
      filter.operation;

    if (
      filter.operation === FilterOperation.IS_NULL ||
      filter.operation === FilterOperation.IS_NOT_NULL
    ) {
      return `${fieldLabel} ${opLabel}`;
    }

    let valueStr = filter.value;
    if (Array.isArray(filter.value)) {
      valueStr = filter.value.join(", ");
    }

    return `${fieldLabel}: ${valueStr}`;
  }

  // ============ SAVED FILTERS (FAVORITES) ============

  openSaveDialog(): void {
    this.showSaveDialog = true;
    this.newFilterName = "";
    this.newFilterDescription = "";
  }

  closeSaveDialog(): void {
    this.showSaveDialog = false;
  }

  saveCurrentFilter(): void {
    if (!this.newFilterName.trim()) return;

    const filterToSave: SavedFilterCreate = {
      name: this.newFilterName.trim(),
      description: this.newFilterDescription.trim() || undefined,
      model_name: this.modelName,
      filters: this.activeFilters,
      sort_by: this.sortBy || undefined,
      sort_order: this.sortOrder,
      page_size: this.pageSize,
      search_query: this.searchQuery || undefined,
    };

    this.saveFilter.emit(filterToSave);
    this.closeSaveDialog();
  }

  onApplySavedFilter(filter: SavedFilter): void {
    this.applySavedFilter.emit(filter);
    this.closePanel();
  }

  onDeleteSavedFilter(event: Event, filterId: number): void {
    event.stopPropagation();
    if (confirm("Are you sure you want to delete this saved filter?")) {
      this.deleteSavedFilter.emit(filterId);
    }
  }

  // ============ CUSTOM FILTER ============

  toggleCustomFilterBuilder(): void {
    this.showCustomFilterBuilder = !this.showCustomFilterBuilder;
  }

  getAvailableOperations(): FilterOperation[] {
    const field = this.fields.find((f) => f.name === this.customFilter.field);
    if (!field) return Object.values(FilterOperation);

    // Return operations based on field type
    switch (field.type) {
      case "text":
        return [
          FilterOperation.EQUALS,
          FilterOperation.NOT_EQUALS,
          FilterOperation.ILIKE,
          FilterOperation.LIKE,
          FilterOperation.STARTS_WITH,
          FilterOperation.ENDS_WITH,
          FilterOperation.IN,
          FilterOperation.NOT_IN,
          FilterOperation.IS_NULL,
          FilterOperation.IS_NOT_NULL,
        ];
      case "number":
        return [
          FilterOperation.EQUALS,
          FilterOperation.NOT_EQUALS,
          FilterOperation.GREATER_THAN,
          FilterOperation.GREATER_EQUAL,
          FilterOperation.LESS_THAN,
          FilterOperation.LESS_EQUAL,
          FilterOperation.BETWEEN,
          FilterOperation.IN,
          FilterOperation.NOT_IN,
          FilterOperation.IS_NULL,
          FilterOperation.IS_NOT_NULL,
        ];
      case "boolean":
        return [
          FilterOperation.EQUALS,
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
          FilterOperation.BETWEEN,
          FilterOperation.IS_NULL,
          FilterOperation.IS_NOT_NULL,
        ];
      default:
        return Object.values(FilterOperation);
    }
  }

  addCustomFilter(): void {
    if (!this.customFilter.field) return;

    const needsValue = ![
      FilterOperation.IS_NULL,
      FilterOperation.IS_NOT_NULL,
    ].includes(this.customFilter.operation);
    if (needsValue && !this.customFilter.value && this.customFilter.value !== 0)
      return;

    const newFilter: FilterRule = {
      field: this.customFilter.field,
      operation: this.customFilter.operation,
      value: this.customFilter.value,
    };

    this.filtersChange.emit([...this.activeFilters, newFilter]);

    // Reset
    this.customFilter.value = "";
    this.showCustomFilterBuilder = false;
    this.apply.emit();
  }

  // ============ HELPERS ============

  get hasActiveFilters(): boolean {
    return this.activeFilters.length > 0 || !!this.searchQuery;
  }

  get activeFilterCount(): number {
    return this.activeFilters.length + (this.searchQuery ? 1 : 0);
  }
}
