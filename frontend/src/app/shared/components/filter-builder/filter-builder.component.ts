import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnInit,
} from "@angular/core";
import { CommonModule } from "@angular/common";
import { FormsModule } from "@angular/forms";

import {
  FilterTreeNode,
  createConditionNode,
  createOperatorNode,
} from "../../../core/interfaces/filter-tree.interface";
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

// PrimeNG 18 Imports
import { TreeModule } from "primeng/tree";
import { TreeNode } from "primeng/api";
import { ButtonModule } from "primeng/button";
import { SelectModule } from "primeng/select";
import { InputTextModule } from "primeng/inputtext";
import { InputNumberModule } from "primeng/inputnumber";
import { DatePickerModule } from "primeng/datepicker";
import { TooltipModule } from "primeng/tooltip";

/**
 * Tree-based Filter Builder Component
 *
 * Renders a recursive tree of AND/OR groups and filter conditions.
 * Each operator node can contain conditions and nested operator groups.
 *
 * Usage:
 * ```html
 * <app-filter-builder
 *   [fields]="filterableFields"
 *   [tree]="filterTree"
 *   (treeChange)="onTreeChange($event)"
 *   (apply)="onApply($event)">
 * </app-filter-builder>
 * ```
 */
@Component({
  selector: "app-filter-builder",
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TreeModule,
    ButtonModule,
    SelectModule,
    InputTextModule,
    InputNumberModule,
    DatePickerModule,
    TooltipModule,
  ],
  templateUrl: "./filter-builder.component.html",
  styleUrls: ["./filter-builder.component.scss"],
})
export class FilterBuilderComponent implements OnInit {
  @Input() fields: FilterableField[] = [];
  @Input() set tree(value: FilterTreeNode | null) {
    this._tree = value;
    this.refreshPrimeNodes();
  }
  get tree(): FilterTreeNode | null {
    return this._tree;
  }

  @Input() applyButtonLabel = "Apply Filters";
  @Input() showApplyButton = true;

  @Output() treeChange = new EventEmitter<FilterTreeNode>();
  @Output() apply = new EventEmitter<FilterTreeNode>();
  @Output() clear = new EventEmitter<void>();

  private _tree: FilterTreeNode | null = null;
  primeNodes: TreeNode[] = [];
  operationLabels = FILTER_OPERATION_LABELS;

  ngOnInit(): void {
    if (!this.tree) {
      this.tree = createOperatorNode("AND");
    }
    this.refreshPrimeNodes();
  }

  // ===========================================================================
  // TREE MAPPING
  // ===========================================================================

  refreshPrimeNodes(): void {
    if (!this.tree) {
      this.primeNodes = [];
      return;
    }
    this.primeNodes = [this.mapToTreeNode(this.tree)];
  }

  private mapToTreeNode(node: FilterTreeNode, parent: FilterTreeNode | null = null): TreeNode {
    const treeNode: TreeNode = {
      key: node.id,
      type: node.nodeType,
      data: { node, parent },
      expanded: node.expanded !== false,
      children: [],
    };

    if (node.nodeType === "operator" && node.children) {
      treeNode.children = node.children.map((child) =>
        this.mapToTreeNode(child, node)
      );
    }

    return treeNode;
  }

  // ===========================================================================
  // NODE MANAGEMENT
  // ===========================================================================

  addCondition(node: FilterTreeNode): void {
    if (node.children) {
      const defaultField = this.fields.length > 0 ? this.fields[0].name : "";
      node.children.push(createConditionNode(defaultField));
      this.refreshPrimeNodes();
      this.emitChange();
    }
  }

  addGroup(node: FilterTreeNode): void {
    if (node.children) {
      const defaultField = this.fields.length > 0 ? this.fields[0].name : "";
      node.children.push(
        createOperatorNode("AND", [
          createConditionNode(defaultField),
          createConditionNode(defaultField),
        ])
      );
      this.refreshPrimeNodes();
      this.emitChange();
    }
  }

  removeNode(parent: FilterTreeNode, node: FilterTreeNode): void {
    if (parent.children) {
      const index = parent.children.findIndex((c) => c.id === node.id);
      if (index !== -1) {
        parent.children.splice(index, 1);
        this.refreshPrimeNodes();
        this.emitChange();
      }
    }
  }

  toggleOperator(node: FilterTreeNode): void {
    node.operator = node.operator === "AND" ? "OR" : "AND";
    this.refreshPrimeNodes();
    this.emitChange();
  }

  toggleExpanded(node: FilterTreeNode): void {
    node.expanded = !node.expanded;
    this.refreshPrimeNodes();
  }

  clearAll(): void {
    this.tree = createOperatorNode("AND");
    this.clear.emit();
    this.refreshPrimeNodes();
    this.emitChange();
  }

  applyFilters(): void {
    if (this.tree) {
      this.apply.emit(this.tree);
      this.emitChange();
    }
  }

  // ===========================================================================
  // FIELD / OPERATION HELPERS
  // ===========================================================================

  getFieldConfig(fieldName: string): FilterableField | undefined {
    return this.fields.find((f) => f.name === fieldName);
  }

  getAvailableOperations(fieldName: string): FilterOperation[] {
    const field = this.getFieldConfig(fieldName);
    if (!field) return Object.values(FilterOperation);
    if (field.allowedOperations && field.allowedOperations.length > 0) {
      return field.allowedOperations;
    }
    return getOperationsForFieldType(field.type);
  }

  onFieldChange(node: FilterTreeNode): void {
    const ops = this.getAvailableOperations(node.field || "");
    if (node.operation && !ops.includes(node.operation)) {
      node.operation = ops[0];
      node.value = "";
    }
    this.emitChange();
  }

  onOperationChange(node: FilterTreeNode): void {
    node.value = "";
    this.emitChange();
  }

  onValueChange(): void {
    this.emitChange();
  }

  getOpLabel(op: any): string {
    if (!op) return "";
    return this.operationLabels[op as FilterOperation] || op;
  }

  needsValue(operation: FilterOperation | undefined): boolean {
    return operation ? operationNeedsValue(operation) : false;
  }

  needsMultipleValues(operation: FilterOperation | undefined): boolean {
    return operation ? operationNeedsMultipleValues(operation) : false;
  }

  needsRange(operation: FilterOperation | undefined): boolean {
    return operation ? operationNeedsRange(operation) : false;
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

  canRemoveChild(parent: FilterTreeNode): boolean {
    return (parent.children?.length || 0) > 2;
  }

  // ===========================================================================
  // PRIVATE
  // ===========================================================================

  private emitChange(): void {
    if (this.tree) {
      this.treeChange.emit(this.tree);
    }
  }
}
