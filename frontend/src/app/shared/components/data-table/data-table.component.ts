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
  @Input() data: T[] = [];

  @Input() columns: TableColumn<T>[] = [];

  @Input() loading = false;

  @Input() pagination: PaginationMeta | null = null;

  @Input() sortField: string | null = null;

  @Input() sortOrder: SortOrder = SortOrder.ASC;

  @Input() pageSizeOptions: number[] = [10, 20, 50, 100];

  @Input() showPagination = true;

  @Input() hoverRows = true;

  @Input() clickableRows = false;

  @Input() striped = false;

  @Input() emptyMessage = "No data available";

  @ContentChild("rowTemplate") rowTemplate?: TemplateRef<any>;

  @ContentChild("cellTemplate") cellTemplate?: TemplateRef<any>;

  @Output() sortChange = new EventEmitter<{
    field: string;
    order: SortOrder;
  }>();

  @Output() pageChange = new EventEmitter<number>();

  @Output() pageSizeChange = new EventEmitter<number>();

  @Output() rowClick = new EventEmitter<T>();


  onSortChange(event: { field: string; order: SortOrder }): void {
    this.sortChange.emit(event);
  }


  onPageChange(page: number): void {
    this.pageChange.emit(page);
  }

  onPageSizeChange(size: number): void {
    this.pageSizeChange.emit(size);
  }


  onRowClick(row: T): void {
    if (this.clickableRows) {
      this.rowClick.emit(row);
    }
  }

  isNumericColumn(column: TableColumn<T>): boolean {
    return column.type === "number" || column.type === "currency";
  }

  isBooleanColumn(column: TableColumn<T>): boolean {
    return column.type === "boolean";
  }

  getBooleanState(value: any): "true" | "false" | "unknown" {
    if (value === true) return "true";
    if (value === false) return "false";
    return "unknown";
  }

  formatBooleanLabel(value: any): string {
    if (value === true) return "Yes";
    if (value === false) return "No";
    return "Unknown";
  }


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


  trackByIndex(index: number): number {
    return index;
  }

  trackByColumn(index: number, column: TableColumn<T>): string {
    return column.field;
  }
}
