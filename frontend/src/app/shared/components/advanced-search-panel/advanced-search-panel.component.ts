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

import { FilterRule } from "../../../core/interfaces/filter.interface";
import { FilterOperation, FILTER_OPERATION_LABELS } from "../../../core/enums/filter-operation.enum";
import { SortOrder } from "../../../core/enums/sort-order.enum";
import { FilterableField } from "../../../core/interfaces/field-config.interface";
import { SavedFilter, SavedFilterCreate } from "../../../core/interfaces/saved-filter.interface";
import { FilterTreeNode, createOperatorNode, generateNodeId, toBackendPayload } from "../../../core/interfaces/filter-tree.interface";
import { FilterBuilderComponent } from "../filter-builder/filter-builder.component";

/**
 * Predefined quick filter configuration
 */
export interface QuickFilter {
  id: string;
  label: string;
  icon?: string;
  filters: FilterRule[];
  category?: string;
  isHeader?: boolean;
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
 * Smart search option (Odoo style)
 */
export interface SearchOption {
  label: string;
  field: string;
  operation: FilterOperation;
  value: any;
}

@Component({
  selector: "app-advanced-search-panel",
  standalone: true,
  imports: [CommonModule, FormsModule, FilterBuilderComponent],
  templateUrl: "./advanced-search-panel.component.html",
  styleUrls: ["./advanced-search-panel.component.scss"],
})
export class AdvancedSearchPanelComponent implements OnInit, OnDestroy {
  // ============ INPUTS ============

  @Input() modelName = "";
  @Input() fields: FilterableField[] = [];
  @Input() quickFilters: QuickFilter[] = [];
  @Input() groupByOptions: GroupByOption[] = [];
  @Input() activeFilters: FilterRule[] = [];
  @Input() searchQuery = "";
  @Input() savedFilters: SavedFilter[] = [];
  @Input() sortBy: string | null = null;
  @Input() sortOrder: SortOrder = SortOrder.DESC;
  @Input() pageSize = 20;
  @Input() placeholder = "Search...";

  /** Current active tree filter */
  @Input() activeTree: FilterTreeNode | null = null;

  // ============ OUTPUTS ============

  @Output() filtersChange = new EventEmitter<FilterRule[]>();
  @Output() treeChange = new EventEmitter<FilterTreeNode | null>();
  @Output() searchChange = new EventEmitter<string>();
  @Output() groupByChange = new EventEmitter<string | null>();
  @Output() applySavedFilter = new EventEmitter<SavedFilter>();
  @Output() saveFilter = new EventEmitter<SavedFilterCreate>();
  @Output() deleteSavedFilter = new EventEmitter<number>();
  @Output() apply = new EventEmitter<void>();

  // ============ STATE ============

  isPanelOpen = false;
  activeQuickFilters: Set<string> = new Set();
  currentGroupBy: string | null = null;
  showSaveDialog = false;
  newFilterName = "";
  newFilterDescription = "";
  
  /** Show custom tree filter builder modal */
  showCustomFilterTree = false;

  // Smart Search State
  searchOptions: SearchOption[] = [];
  isSearchDropdownOpen = false;

  operationLabels = FILTER_OPERATION_LABELS;
  private destroy$ = new Subject<void>();

  ngOnInit(): void {}

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
    this.searchQuery = value;
    this.searchChange.emit(value);
    
    if (value.trim().length > 0) {
      this.generateSearchOptions(value.trim());
    } else {
      this.searchOptions = [];
      this.isSearchDropdownOpen = false;
    }
  }

  generateSearchOptions(query: string): void {
    const options: SearchOption[] = [];
    
    this.fields.forEach(field => {
      // Skip non-searchable fields: IDs, FK IDs, booleans
      if (field.name === 'id' || field.name.endsWith('_id') || field.type === 'boolean') {
        return;
      }
      
      // Infer operator based on field type (Odoo rules)
      let operation = FilterOperation.EQUALS;
      let isRelationship = field.name.includes('.');
      
      if (field.type === 'text' || field.type === 'select') {
        operation = FilterOperation.ILIKE;
      } else if (field.type === 'number') {
        operation = FilterOperation.EQUALS;
      } else if (isRelationship) {
        operation = FilterOperation.ILIKE;
      }
      
      // Build Odoo-style label: "Search Title for: dede"
      const label = field.label || field.name;
      
      options.push({
        label: `Search ${label} for: ${query}`,
        field: field.name,
        operation: operation,
        value: query
      });
    });

    // Add a "Custom Filter..." option at the end
    options.push({
      label: 'Custom Filter...',
      field: '__custom__',
      operation: FilterOperation.EQUALS,
      value: query
    });

    this.searchOptions = options;
    this.isSearchDropdownOpen = options.length > 0;
  }

  selectSearchOption(option: SearchOption): void {
    // Handle "Custom Filter..." option
    if (option.field === '__custom__') {
      this.toggleCustomFilterTree();
      this.searchQuery = "";
      this.searchOptions = [];
      this.isSearchDropdownOpen = false;
      return;
    }
    
    // Create a new condition node for the tree
    const conditionNode: FilterTreeNode = {
      id: generateNodeId(),
      nodeType: 'condition',
      field: option.field,
      operation: option.operation,
      value: option.value
    };
    
    // Merge into the existing tree: wrap in AND if tree exists, or create new AND root
    if (this.activeTree && this.activeTree.nodeType === 'operator' && this.activeTree.operator === 'AND') {
      // Append to existing AND root
      const updatedTree: FilterTreeNode = {
        ...this.activeTree,
        children: [...(this.activeTree.children || []), conditionNode]
      };
      this.activeTree = updatedTree;
      this.treeChange.emit(updatedTree);
    } else if (this.activeTree) {
      // Wrap existing tree + new condition in AND
      const andRoot: FilterTreeNode = {
        id: generateNodeId(),
        nodeType: 'operator',
        operator: 'AND',
        children: [this.activeTree, conditionNode],
        expanded: true
      };
      this.activeTree = andRoot;
      this.treeChange.emit(andRoot);
    } else {
      // No tree yet — create AND root with single condition
      const andRoot: FilterTreeNode = {
        id: generateNodeId(),
        nodeType: 'operator',
        operator: 'AND',
        children: [conditionNode],
        expanded: true
      };
      this.activeTree = andRoot;
      this.treeChange.emit(andRoot);
    }
    
    // Clear search bar
    this.searchQuery = "";
    this.searchChange.emit("");
    this.searchOptions = [];
    this.isSearchDropdownOpen = false;
    
    // Apply immediately
    this.apply.emit();
  }
  
  hideSearchDropdown(): void {
    // Slight delay to allow clicks on the dropdown items to register
    setTimeout(() => {
      this.isSearchDropdownOpen = false;
    }, 150);
  }

  showSearchDropdown(): void {
    if (this.searchOptions.length > 0) {
      this.isSearchDropdownOpen = true;
    }
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
      const newFilters = this.activeFilters.filter(
        (af) => !filter.filters.some((qf) => qf.field === af.field && qf.operation === af.operation),
      );
      this.filtersChange.emit(newFilters);
    } else {
      this.activeQuickFilters.add(filter.id);
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
    this.treeChange.emit(null);
    this.searchChange.emit("");
    this.apply.emit();
  }

  getFilterTagLabel(filter: FilterRule): string {
    const field = this.fields.find((f) => f.name === filter.field);
    const fieldLabel = field?.label || filter.field;
    const opLabel = this.operationLabels[filter.operation as FilterOperation] || filter.operation;

    if (filter.operation === FilterOperation.IS_NULL || filter.operation === FilterOperation.IS_NOT_NULL) {
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
      filter_tree: this.activeTree ? toBackendPayload(this.activeTree) : undefined,
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

  // ============ CUSTOM FILTER TREE ============

  toggleCustomFilterTree(): void {
    if (!this.activeTree) {
      this.activeTree = createOperatorNode("AND");
    }
    this.showCustomFilterTree = !this.showCustomFilterTree;
  }

  onTreeChange(tree: FilterTreeNode): void {
    this.activeTree = tree;
    this.treeChange.emit(tree);
  }

  onApplyTree(tree: FilterTreeNode): void {
    this.activeTree = tree;
    this.treeChange.emit(tree);
    this.showCustomFilterTree = false;
    this.apply.emit();
  }

  onClearTree(): void {
    this.activeTree = null;
    this.treeChange.emit(null);
    this.showCustomFilterTree = false;
    this.apply.emit();
  }

  // ============ LEGACY CUSTOM FILTER (maintained for UI compatibility) ============

  showCustomFilterBuilder = false;
  customFilter = { field: "", operation: FilterOperation.EQUALS, value: "" };

  toggleCustomFilterBuilder(): void {
    // Redirect to the new Tree Builder
    this.toggleCustomFilterTree();
  }

  // ============ HELPERS ============

  get hasActiveFilters(): boolean {
    return this.activeFilters.length > 0 || !!this.searchQuery || !!this.activeTree;
  }

  get activeFilterCount(): number {
    return this.activeFilters.length + (this.searchQuery ? 1 : 0) + (this.activeTree ? 1 : 0);
  }
}
