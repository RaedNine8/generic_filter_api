import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnInit,
  OnDestroy,
  OnChanges,
  SimpleChanges,
  inject,
  ViewChild,
  ElementRef,
} from "@angular/core";
import { CommonModule } from "@angular/common";
import { FormsModule } from "@angular/forms";
import { HttpClient } from "@angular/common/http";
import { Subject } from "rxjs";
import { takeUntil } from "rxjs/operators";

import { FilterRule } from "../../../core/interfaces/filter.interface";
import {
  FilterOperation,
  FILTER_OPERATION_LABELS,
} from "../../../core/enums/filter-operation.enum";
import { SortOrder } from "../../../core/enums/sort-order.enum";
import {
  FilterableField,
  getOperationsForFieldType,
} from "../../../core/interfaces/field-config.interface";
import {
  SavedFilter,
  SavedFilterCreate,
} from "../../../core/interfaces/saved-filter.interface";
import {
  FilterTreeNode,
  createOperatorNode,
  generateNodeId,
  toBackendPayload,
} from "../../../core/interfaces/filter-tree.interface";
import { FilterBuilderComponent } from "../filter-builder/filter-builder.component";

export interface QuickFilter {
  id: string;
  label: string;
  icon?: string;
  filters: FilterRule[];
  category?: string;
  isHeader?: boolean;
  hasSubmenu?: boolean;
}

export interface GroupByOption {
  field: string;
  label: string;
  icon?: string;
  hasSubmenu?: boolean;
}

export interface SearchOption {
  label: string;
  field: string;
  operation: FilterOperation;
  value: any;
  typeHint?: string;
  isDisabled?: boolean;
  isFkHeader?: boolean;
  fkRelationshipName?: string;
  subOptions?: SearchOption[];
  isCustom?: boolean;
}

interface ModelMetadata {
  model: string;
  table: string;
  fields: MetadataField[];
  relationships: MetadataRelationship[];
}

interface MetadataField {
  name: string;
  type: string;
  nullable: boolean;
  ops: string[];
  is_fk: boolean;
  fk_target_table?: string;
  fk_target_column?: string;
}

interface MetadataRelationship {
  name: string;
  related_model: string;
  related_table: string;
  cardinality: string;
  display_field: string;
  related_fields: { name: string; type: string; ops: string[] }[];
}

@Component({
  selector: "app-advanced-search-panel",
  standalone: true,
  imports: [CommonModule, FormsModule, FilterBuilderComponent],
  templateUrl: "./advanced-search-panel.component.html",
  styleUrls: ["./advanced-search-panel.component.scss"],
})
export class AdvancedSearchPanelComponent implements OnInit, OnDestroy, OnChanges {
  @Input() modelName = "";
  @Input() fields: FilterableField[] = [];
  @Input() quickFilters: QuickFilter[] = [];
  @Input() groupByOptions: GroupByOption[] = [];
  @Input() activeGroupBy: string | null = null;
  @Input() activeFilters: FilterRule[] = [];
  @Input() searchQuery = "";
  @Input() savedFilters: SavedFilter[] = [];
  @Input() sortBy: string | null = null;
  @Input() sortOrder: SortOrder = SortOrder.DESC;
  @Input() pageSize = 20;
  @Input() placeholder = "Search...";

  @Input() apiEndpoint = "";

  @Input() activeTree: FilterTreeNode | null = null;

  @Output() filtersChange = new EventEmitter<FilterRule[]>();
  @Output() treeChange = new EventEmitter<FilterTreeNode | null>();
  @Output() globalSearch = new EventEmitter<string>();
  @Output() groupByChange = new EventEmitter<string | null>();
  @Output() applySavedFilter = new EventEmitter<SavedFilter>();
  @Output() saveFilter = new EventEmitter<SavedFilterCreate>();
  @Output() deleteSavedFilter = new EventEmitter<number>();

  private http = inject(HttpClient);

  @ViewChild("searchInput") searchInputRef!: ElementRef<HTMLInputElement>;

  isPanelOpen = false;
  activeQuickFilters: Set<string> = new Set();
  currentGroupBy: string | null = null;
  showSaveDialog = false;
  newFilterName = "";
  newFilterDescription = "";

  showCustomFilterTree = false;
  draftTree: FilterTreeNode | null = null;

  searchOptions: SearchOption[] = [];
  isSearchDropdownOpen = false;
  expandedFkHeaders: Set<string> = new Set();
  inputText = "";

  private metadata: ModelMetadata | null = null;
  private metadataLoading = false;
  private metadataBackedFilterFields: FilterableField[] = [];

  operationLabels = FILTER_OPERATION_LABELS;
  private destroy$ = new Subject<void>();

  ngOnInit(): void {
    this.currentGroupBy = this.activeGroupBy;
    this.fetchMetadata();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes["activeGroupBy"]) {
      this.currentGroupBy = this.activeGroupBy;
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  togglePanel(): void {
    this.isPanelOpen = !this.isPanelOpen;
  }

  closePanel(): void {
    this.isPanelOpen = false;
  }

  private fetchMetadata(): void {
    if (!this.apiEndpoint || this.metadataLoading) return;
    this.metadataLoading = true;

    const url = `${this.apiEndpoint}/metadata`;
    this.http
      .get<ModelMetadata>(url)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (meta) => {
          this.metadata = meta;
          this.rebuildFilterBuilderFields();
          this.metadataLoading = false;
        },
        error: (err) => {
          console.error("[SearchPanel] Metadata fetch error:", err);
          this.metadataLoading = false;
        },
      });
  }

  onSearchInput(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.inputText = value;

    if (value.trim().length > 0) {
      this.generateSearchOptions(value.trim());
    } else {
      this.searchOptions = [];
      this.isSearchDropdownOpen = false;
      this.expandedFkHeaders.clear();
    }
  }

  generateSearchOptions(query: string): void {
    const options: SearchOption[] = [];
    const queryLower = query.toLowerCase();
    const isNumeric = !isNaN(Number(query)) && query.trim() !== "";
    const isBoolTerm = ["true", "false", "yes", "no"].includes(queryLower);
    const dateValue = this.tryParseDateValue(query);

    if (this.metadata) {
      for (const field of this.metadata.fields) {
        if (field.name === "id" || field.is_fk) continue;

        const fieldConfig = this.fields.find((f) => f.name === field.name);
        const label = fieldConfig?.label || this.humanize(field.name);

        if (field.type === "string") {
          options.push({
            label: `Search ${label} for: ${query}`,
            field: field.name,
            operation: FilterOperation.ILIKE,
            value: query,
            typeHint: "Text",
          });
        } else if (field.type === "enum") {
          options.push({
            label: `Search ${label} for: ${query}`,
            field: field.name,
            operation: FilterOperation.ILIKE,
            value: query,
            typeHint: "Enum",
          });
        } else if (field.type === "integer" || field.type === "float") {
          options.push({
            label: isNumeric
              ? `Search ${label} for: ${query}`
              : `Search ${label} for: ${query} (enter a number)`,
            field: field.name,
            operation: FilterOperation.EQUALS,
            value: isNumeric ? Number(query) : null,
            typeHint: "Number",
            isDisabled: !isNumeric,
          });
        } else if (field.type === "boolean") {
          const boolVal = ["true", "yes"].includes(queryLower);
          options.push({
            label: isBoolTerm
              ? `Search ${label} for: ${boolVal}`
              : `Search ${label} for: ${query} (enter true/false)`,
            field: field.name,
            operation: FilterOperation.EQUALS,
            value: isBoolTerm ? boolVal : null,
            typeHint: "Boolean",
            isDisabled: !isBoolTerm,
          });
        } else if (field.type === "date" || field.type === "datetime") {
          options.push({
            label: dateValue
              ? `Search ${label} for: ${query}`
              : `Search ${label} for: ${query} (enter a valid date)`,
            field: field.name,
            operation: FilterOperation.EQUALS,
            value: dateValue,
            typeHint: "Date",
            isDisabled: !dateValue,
          });
        }
      }

      for (const rel of this.metadata.relationships) {
        if (rel.cardinality !== "m2o") continue;

        const relLabel = this.humanize(rel.name);
        const displayFieldType = rel.related_fields.find(
          (field) => field.name === rel.display_field,
        )?.type;
        const dotField = `${rel.name}.${rel.display_field}`;

        if (
          displayFieldType === "string" ||
          displayFieldType === "enum" ||
          !displayFieldType
        ) {
          options.push({
            label: `Search ${relLabel} for: ${query}`,
            field: dotField,
            operation: FilterOperation.ILIKE,
            value: query,
            typeHint: "Relation",
            isFkHeader: true,
            fkRelationshipName: rel.name,
          });
        } else if (
          displayFieldType === "integer" ||
          displayFieldType === "float"
        ) {
          options.push({
            label: isNumeric
              ? `Search ${relLabel} for: ${query}`
              : `Search ${relLabel} for: ${query} (enter a number)`,
            field: dotField,
            operation: FilterOperation.EQUALS,
            value: isNumeric ? Number(query) : null,
            typeHint: "Relation",
            isDisabled: !isNumeric,
            isFkHeader: true,
            fkRelationshipName: rel.name,
          });
        } else if (displayFieldType === "boolean") {
          const boolVal = ["true", "yes"].includes(queryLower);
          options.push({
            label: isBoolTerm
              ? `Search ${relLabel} for: ${boolVal}`
              : `Search ${relLabel} for: ${query} (enter true/false)`,
            field: dotField,
            operation: FilterOperation.EQUALS,
            value: isBoolTerm ? boolVal : null,
            typeHint: "Relation",
            isDisabled: !isBoolTerm,
            isFkHeader: true,
            fkRelationshipName: rel.name,
          });
        } else if (
          displayFieldType === "date" ||
          displayFieldType === "datetime"
        ) {
          options.push({
            label: dateValue
              ? `Search ${relLabel} for: ${query}`
              : `Search ${relLabel} for: ${query} (enter a valid date)`,
            field: dotField,
            operation: FilterOperation.EQUALS,
            value: dateValue,
            typeHint: "Relation",
            isDisabled: !dateValue,
            isFkHeader: true,
            fkRelationshipName: rel.name,
          });
        }
      }
    } else {
      this.generateSearchOptionsFallback(query, options, isNumeric, isBoolTerm);
    }

    options.push({
      label: "Custom Filter...",
      field: "__custom__",
      operation: FilterOperation.EQUALS,
      value: query,
      typeHint: "Advanced",
      isCustom: true,
    });

    this.searchOptions = options;
    this.isSearchDropdownOpen = options.length > 0;
  }

  private generateSearchOptionsFallback(
    query: string,
    options: SearchOption[],
    isNumeric: boolean,
    isBoolTerm: boolean,
  ): void {
    for (const field of this.fields) {
      if (field.name === "id" || field.name.endsWith("_id")) continue;

      const label = field.label || field.name;
      const isRelationship = field.name.includes(".");

      if (field.type === "text" || field.type === "select" || isRelationship) {
        options.push({
          label: `Search ${label} for: ${query}`,
          field: field.name,
          operation: FilterOperation.ILIKE,
          value: query,
          typeHint: isRelationship
            ? "Relation"
            : field.type === "text"
              ? "Text"
              : "Enum",
          isFkHeader: isRelationship,
          fkRelationshipName: isRelationship
            ? field.name.split(".")[0]
            : undefined,
        });
      } else if (field.type === "number" && isNumeric) {
        options.push({
          label: `Search ${label} for: ${query}`,
          field: field.name,
          operation: FilterOperation.EQUALS,
          value: Number(query),
          typeHint: "Number",
        });
      } else if (field.type === "boolean" && isBoolTerm) {
        const boolVal = ["true", "yes"].includes(query.toLowerCase());
        options.push({
          label: `Search ${label} for: ${boolVal}`,
          field: field.name,
          operation: FilterOperation.EQUALS,
          value: boolVal,
          typeHint: "Boolean",
        });
      }
    }
  }

  toggleFkExpansion(relName: string): void {
    if (this.expandedFkHeaders.has(relName)) {
      this.expandedFkHeaders.delete(relName);
    } else {
      this.expandedFkHeaders.add(relName);
    }
    if (this.inputText.trim()) {
      this.generateSearchOptions(this.inputText.trim());
    }
  }

  selectSearchOption(option: SearchOption): void {
    if (option.isDisabled) {
      return;
    }

    if (option.isCustom) {
      this.toggleCustomFilterTree();
      this.inputText = "";
      this.searchOptions = [];
      this.isSearchDropdownOpen = false;
      return;
    }

    const conditionNode: FilterTreeNode = {
      id: generateNodeId(),
      nodeType: "condition",
      field: option.field,
      operation: option.operation,
      value: option.value,
    };

    this.inputText = "";
    this.searchOptions = [];
    this.isSearchDropdownOpen = false;
    this.expandedFkHeaders.clear();
    this.clearSearchInput();
    this.refocusSearchInput();

    let newTree: FilterTreeNode;
    if (
      this.activeTree &&
      this.activeTree.nodeType === "operator" &&
      this.activeTree.operator === "AND"
    ) {
      newTree = {
        ...this.activeTree,
        children: [...(this.activeTree.children || []), conditionNode],
      };
    } else if (this.activeTree) {
      newTree = {
        id: generateNodeId(),
        nodeType: "operator",
        operator: "AND",
        children: [this.activeTree, conditionNode],
        expanded: true,
      };
    } else {
      newTree = {
        id: generateNodeId(),
        nodeType: "operator",
        operator: "AND",
        children: [conditionNode],
        expanded: true,
      };
    }
    this.treeChange.emit(newTree);
  }

  hideSearchDropdown(): void {
    this.isSearchDropdownOpen = false;
  }

  showSearchDropdown(): void {
    if (this.searchOptions.length > 0) {
      this.isSearchDropdownOpen = true;
    }
  }

  onSearchKeydown(event: KeyboardEvent): void {
    if (event.key === "Enter") {
      event.preventDefault();
      event.stopPropagation();
      const query = this.inputText.trim();

      if (!query) {
        return;
      }

      this.globalSearch.emit(query);
      this.inputText = "";
      this.searchOptions = [];
      this.isSearchDropdownOpen = false;
      this.expandedFkHeaders.clear();
      this.clearSearchInput();
      this.refocusSearchInput();
    } else if (event.key === "Escape") {
      this.isSearchDropdownOpen = false;
      this.expandedFkHeaders.clear();
    }
  }

  getOptionLabelParts(
    label: string,
  ): { prefix: string; field: string; suffix: string } | null {
    const match = label.match(/^Search\s+(.+?)\s+for:(.*)$/);
    if (!match) {
      return null;
    }

    return {
      prefix: "Search",
      field: match[1].trim(),
      suffix: `for: ${match[2].trimStart()}`,
    };
  }

  private clearSearchInput(): void {
    if (this.searchInputRef?.nativeElement) {
      this.searchInputRef.nativeElement.value = "";
    }
  }

  private refocusSearchInput(): void {
    queueMicrotask(() => {
      this.searchInputRef?.nativeElement?.focus();
    });
  }

  private humanize(str: string): string {
    return str.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  }

  private tryParseDateValue(raw: string): string | null {
    const value = raw.trim();
    if (!value) return null;
    const parsed = Date.parse(value);
    if (isNaN(parsed)) return null;
    return value;
  }

  toggleQuickFilter(filter: QuickFilter): void {
    if (filter.isHeader) return;

    if (this.activeQuickFilters.has(filter.id)) {
      this.activeQuickFilters.delete(filter.id);
      const newFilters = this.activeFilters.filter(
        (af) =>
          !filter.filters.some(
            (qf) => qf.field === af.field && qf.operation === af.operation,
          ),
      );
      this.filtersChange.emit(newFilters);
    } else {
      this.activeQuickFilters.add(filter.id);
      const newFilters = [...this.activeFilters, ...filter.filters];
      this.filtersChange.emit(newFilters);
    }
  }

  isQuickFilterActive(filterId: string): boolean {
    return this.activeQuickFilters.has(filterId);
  }

  setGroupBy(field: string | null): void {
    this.currentGroupBy = field;
    this.groupByChange.emit(field);
  }

  getTreeConditions(): { id: string; label: string }[] {
    if (!this.activeTree) return [];
    const conditions: { id: string; label: string }[] = [];
    this.collectConditions(this.activeTree, conditions);
    return conditions;
  }

  private collectConditions(
    node: FilterTreeNode,
    out: { id: string; label: string }[],
  ): void {
    if (node.nodeType === "condition") {
      const fieldName = node.field || "";
      const fieldConfig = this.fields.find((f) => f.name === fieldName);
      let label =
        fieldConfig?.label || this.humanize(fieldName.replace(".", " → "));

      const op = node.operation?.toLowerCase();
      if (op === "is_null") {
        label = `${label} is empty`;
      } else if (op === "is_not_null") {
        label = `${label} is set`;
      } else {
        const val = Array.isArray(node.value)
          ? node.value.join(", ")
          : node.value;
        label = `${label}: ${val}`;
      }
      out.push({ id: node.id, label });
    } else if (node.children) {
      for (const child of node.children) {
        this.collectConditions(child, out);
      }
    }
  }

  removeTreeCondition(conditionId: string): void {
    if (!this.activeTree) return;

    const pruned = this.removeNodeById(this.activeTree, conditionId);
    if (!pruned) {
      this.treeChange.emit(null);
    } else {
      this.treeChange.emit(pruned);
    }
  }

  private removeNodeById(
    node: FilterTreeNode,
    targetId: string,
  ): FilterTreeNode | null {
    if (node.id === targetId) return null;
    if (node.nodeType === "operator" && node.children) {
      const remaining = node.children
        .map((c) => this.removeNodeById(c, targetId))
        .filter((c): c is FilterTreeNode => c !== null);
      if (remaining.length === 0) return null;
      if (remaining.length === 1) return remaining[0];
      return { ...node, children: remaining };
    }
    return node;
  }

  removeFilterTag(index: number): void {
    const newFilters = [...this.activeFilters];
    newFilters.splice(index, 1);
    this.filtersChange.emit(newFilters);
  }

  clearAllFilters(): void {
    this.activeQuickFilters.clear();
    this.inputText = "";
    this.searchOptions = [];
    this.isSearchDropdownOpen = false;
    this.showCustomFilterTree = false;
    this.draftTree = null;
    this.currentGroupBy = null;
    this.clearSearchInput();
    this.globalSearch.emit("");
    this.groupByChange.emit(null);
    this.filtersChange.emit([]);
    this.treeChange.emit(null);
  }

  removeSearchTag(): void {
    this.globalSearch.emit("");
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
      filter_tree: this.activeTree
        ? toBackendPayload(this.activeTree)
        : undefined,
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

  toggleCustomFilterTree(): void {
    if (!this.showCustomFilterTree) {
      this.draftTree = this.activeTree
        ? this.cloneTree(this.activeTree)
        : createOperatorNode("AND");
    }
    this.showCustomFilterTree = !this.showCustomFilterTree;

    if (!this.showCustomFilterTree) {
      this.draftTree = null;
    }
  }

  onTreeChange(tree: FilterTreeNode): void {
    this.draftTree = tree;
  }

  onApplyTree(tree: FilterTreeNode): void {
    const committedTree = this.normalizeTreeValues(tree);
    this.treeChange.emit(committedTree);
    this.showCustomFilterTree = false;
    this.draftTree = null;
  }

  onClearTree(): void {
    this.treeChange.emit(null);
    this.showCustomFilterTree = false;
    this.draftTree = null;
  }

  get hasActiveFilters(): boolean {
    return (
      this.activeFilters.length > 0 || !!this.searchQuery || !!this.activeTree
    );
  }

  get activeFilterCount(): number {
    return (
      this.activeFilters.length +
      (this.searchQuery ? 1 : 0) +
      (this.activeTree ? 1 : 0)
    );
  }

  private cloneTree(node: FilterTreeNode): FilterTreeNode {
    return {
      ...node,
      children: node.children?.map((child) => this.cloneTree(child)),
    };
  }

  get filterBuilderFields(): FilterableField[] {
    if (this.metadataBackedFilterFields.length > 0) {
      return this.metadataBackedFilterFields;
    }
    return this.fields;
  }

  private rebuildFilterBuilderFields(): void {
    if (!this.metadata) {
      this.metadataBackedFilterFields = [];
      return;
    }

    const byName = new Map<string, FilterableField>();
    const configByName = new Map(
      this.fields.map((field) => [field.name, field]),
    );

    for (const field of this.metadata.fields) {
      if (field.is_fk) {
        continue;
      }

      const configField = configByName.get(field.name);
      const mappedType = this.mapMetadataTypeToFilterType(field.type);
      const allowedOperations = this.mapAllowedOperations(
        field.ops,
        mappedType,
      );

      byName.set(field.name, {
        name: field.name,
        label: configField?.label || this.humanize(field.name),
        type: mappedType,
        options: configField?.options,
        sortable: configField?.sortable ?? true,
        searchable: configField?.searchable ?? true,
        allowedOperations,
      });
    }

    for (const rel of this.metadata.relationships) {
      if (rel.cardinality !== "m2o") {
        continue;
      }

      const relLabel = this.humanize(rel.name);
      for (const relField of rel.related_fields) {
        const dotName = `${rel.name}.${relField.name}`;
        const configField = configByName.get(dotName);
        const mappedType = this.mapMetadataTypeToFilterType(relField.type);
        const allowedOperations = this.mapAllowedOperations(
          relField.ops,
          mappedType,
        );

        byName.set(dotName, {
          name: dotName,
          label:
            configField?.label ||
            `${relLabel} -> ${this.humanize(relField.name)}`,
          type: mappedType,
          options: configField?.options,
          sortable: configField?.sortable ?? false,
          searchable: configField?.searchable ?? true,
          allowedOperations,
        });
      }
    }

    this.metadataBackedFilterFields = Array.from(byName.values());
  }

  private mapMetadataTypeToFilterType(type: string): FilterableField["type"] {
    switch (type) {
      case "integer":
      case "float":
        return "number";
      case "boolean":
        return "boolean";
      case "date":
        return "date";
      case "datetime":
        return "datetime";
      case "enum":
        return "enum";
      default:
        return "text";
    }
  }

  private mapAllowedOperations(
    ops: string[],
    type: FilterableField["type"],
  ): FilterOperation[] {
    const allowed = ops
      .map((op) => op as FilterOperation)
      .filter((op) => Object.values(FilterOperation).includes(op));
    return allowed.length > 0 ? allowed : getOperationsForFieldType(type);
  }

  private normalizeTreeValues(node: FilterTreeNode): FilterTreeNode {
    if (node.nodeType === "operator") {
      return {
        ...node,
        children: (node.children || []).map((child) =>
          this.normalizeTreeValues(child),
        ),
      };
    }

    const normalizedValue = this.normalizeConditionValue(node);
    return {
      ...node,
      value: normalizedValue,
    };
  }

  private normalizeConditionValue(node: FilterTreeNode): any {
    const operation = node.operation;
    const rawValue = node.value;
    const fieldType = this.filterBuilderFields.find(
      (f) => f.name === node.field,
    )?.type;

    if (!operation) {
      return rawValue;
    }

    if (
      operation === FilterOperation.IS_NULL ||
      operation === FilterOperation.IS_NOT_NULL
    ) {
      return true;
    }

    if (
      operation === FilterOperation.IN ||
      operation === FilterOperation.NOT_IN
    ) {
      if (Array.isArray(rawValue)) {
        return rawValue.filter(
          (v) => v !== null && v !== undefined && `${v}`.trim() !== "",
        );
      }
      if (typeof rawValue === "string") {
        return rawValue
          .split(",")
          .map((v) => v.trim())
          .filter((v) => v.length > 0)
          .map((v) => this.normalizeScalarByFieldType(v, fieldType));
      }
      if (rawValue === null || rawValue === undefined || rawValue === "") {
        return [];
      }
      return [this.normalizeScalarByFieldType(rawValue, fieldType)];
    }

    if (operation === FilterOperation.BETWEEN) {
      let range: any[] = [];
      if (Array.isArray(rawValue)) {
        range = rawValue.slice(0, 2);
      } else if (typeof rawValue === "string") {
        range = rawValue
          .split(",")
          .map((v) => v.trim())
          .slice(0, 2);
      }
      while (range.length < 2) {
        range.push(null);
      }
      return range.map((v) => this.normalizeScalarByFieldType(v, fieldType));
    }

    return this.normalizeScalarByFieldType(rawValue, fieldType);
  }

  private normalizeScalarByFieldType(
    value: any,
    fieldType: FilterableField["type"] | undefined,
  ): any {
    if (value === null || value === undefined || value === "") {
      return value;
    }

    if (fieldType === "number") {
      const parsed = Number(value);
      return Number.isNaN(parsed) ? value : parsed;
    }

    if (fieldType === "boolean") {
      if (typeof value === "boolean") {
        return value;
      }
      const lowered = `${value}`.trim().toLowerCase();
      if (["true", "yes", "1"].includes(lowered)) return true;
      if (["false", "no", "0"].includes(lowered)) return false;
    }

    if (
      (fieldType === "date" || fieldType === "datetime") &&
      value instanceof Date
    ) {
      return value.toISOString();
    }

    return value;
  }
}
