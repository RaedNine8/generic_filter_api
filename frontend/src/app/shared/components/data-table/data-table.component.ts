import {
  Component,
  Input,
  Output,
  EventEmitter,
  ContentChild,
  TemplateRef,
} from "@angular/core";
import {
  CommonModule,
  DatePipe,
  CurrencyPipe,
  DecimalPipe,
} from "@angular/common";

import { TableColumn } from "../../../core/interfaces/field-config.interface";
import { PaginationMeta } from "../../../core/interfaces/pagination.interface";
import { SortOrder } from "../../../core/enums/sort-order.enum";
import { PaginationComponent } from "../pagination/pagination.component";
import { SortHeaderComponent } from "../sort-header/sort-header.component";

/**
 * Data Table Component
 *
 * A generic, reusable data table with sorting, pagination, and custom cell templates.
 *
 * Features:
 * - Dynamic column configuration
 * - Sortable columns
 * - Integrated pagination
 * - Custom cell templates
 * - Loading state
 * - Empty state
 * - Row selection (optional)
 *
 * Usage:
 * ```html
 * <app-data-table
 *   [data]="items"
 *   [columns]="columnConfig"
 *   [loading]="isLoading"
 *   [pagination]="paginationMeta"
 *   [sortField]="currentSort.field"
 *   [sortOrder]="currentSort.order"
 *   (sortChange)="onSort($event)"
 *   (pageChange)="onPageChange($event)"
 *   (rowClick)="onRowClick($event)">
 * </app-data-table>
 * ```
 */
@Component({
  selector: "app-data-table",
  standalone: true,
  imports: [
    CommonModule,
    PaginationComponent,
    SortHeaderComponent,
    DatePipe,
    CurrencyPipe,
    DecimalPipe,
  ],
  templateUrl: "./data-table.component.html",
  styleUrls: ["./data-table.component.scss"],
})
export class DataTableComponent<T = any> {
  /** Data to display */
  @Input() data: T[] = [];

  /** Column configuration */
  @Input() columns: TableColumn<T>[] = [];

  /** Loading state */
  @Input() loading = false;

  /** Pagination metadata */
  @Input() pagination: PaginationMeta | null = null;

  /** Current sort field */
  @Input() sortField: string | null = null;

  /** Current sort order */
  @Input() sortOrder: SortOrder = SortOrder.ASC;

  /** Page size options for pagination */
  @Input() pageSizeOptions: number[] = [10, 20, 50, 100];

  /** Show pagination */
  @Input() showPagination = true;

  /** Enable row hover effect */
  @Input() hoverRows = true;

  /** Enable row click */
  @Input() clickableRows = false;

  /** Striped rows */
  @Input() striped = false;

  /** Empty state message */
  @Input() emptyMessage = "No data available";

  /** Custom row template */
  @ContentChild("rowTemplate") rowTemplate?: TemplateRef<any>;

  /** Custom cell templates */
  @ContentChild("cellTemplate") cellTemplate?: TemplateRef<any>;

  /** Emitted when sort changes */
  @Output() sortChange = new EventEmitter<{
    field: string;
    order: SortOrder;
  }>();

  /** Emitted when page changes */
  @Output() pageChange = new EventEmitter<number>();

  /** Emitted when page size changes */
  @Output() pageSizeChange = new EventEmitter<number>();

  /** Emitted when a row is clicked */
  @Output() rowClick = new EventEmitter<T>();

  // ===========================================================================
  // SORTING
  // ===========================================================================

  onSortChange(event: { field: string; order: SortOrder }): void {
    this.sortChange.emit(event);
  }

  // ===========================================================================
  // PAGINATION
  // ===========================================================================

  onPageChange(page: number): void {
    this.pageChange.emit(page);
  }

  onPageSizeChange(size: number): void {
    this.pageSizeChange.emit(size);
  }

  // ===========================================================================
  // ROW INTERACTION
  // ===========================================================================

  onRowClick(row: T): void {
    if (this.clickableRows) {
      this.rowClick.emit(row);
    }
  }

  // ===========================================================================
  // CELL RENDERING
  // ===========================================================================

  getCellValue(row: T, column: TableColumn<T>): any {
    const value = this.getNestedValue(row, column.field);

    if (column.formatter) {
      return column.formatter(value, row);
    }

    return value;
  }

  formatCellValue(value: any, column: TableColumn<T>): string {
    if (value === null || value === undefined) {
      return "—";
    }

    switch (column.type) {
      case "date":
        return this.formatDate(value);
      case "datetime":
        return this.formatDateTime(value);
      case "boolean":
        return value ? "✓" : "✗";
      case "currency":
        return this.formatCurrency(value);
      case "number":
        return this.formatNumber(value);
      default:
        return String(value);
    }
  }

  private getNestedValue(obj: any, path: string): any {
    return path.split(".").reduce((o, key) => (o ? o[key] : undefined), obj);
  }

  private formatDate(value: any): string {
    if (!value) return "—";
    const date = new Date(value);
    return date.toLocaleDateString();
  }

  private formatDateTime(value: any): string {
    if (!value) return "—";
    const date = new Date(value);
    return `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
  }

  private formatCurrency(value: any): string {
    if (typeof value !== "number") return "—";
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(value);
  }

  private formatNumber(value: any): string {
    if (typeof value !== "number") return "—";
    return new Intl.NumberFormat("en-US").format(value);
  }

  // ===========================================================================
  // TRACKING
  // ===========================================================================

  trackByIndex(index: number): number {
    return index;
  }

  trackByColumn(index: number, column: TableColumn<T>): string {
    return column.field;
  }
}
