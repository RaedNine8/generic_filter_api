import {
  Component,
  Input,
  Output,
  EventEmitter,
  HostListener,
} from "@angular/core";
import { CommonModule } from "@angular/common";

import { SortOrder } from "../../../core/enums/sort-order.enum";

/**
 * Sort Header Component
 *
 * A reusable sortable column header component.
 *
 * Features:
 * - Visual sort indicator
 * - Click to toggle sort
 * - Active state styling
 *
 * Usage:
 * ```html
 * <th>
 *   <app-sort-header
 *     [field]="'title'"
 *     [label]="'Title'"
 *     [currentSortField]="sortBy"
 *     [currentSortOrder]="sortOrder"
 *     (sortChange)="onSort($event)">
 *   </app-sort-header>
 * </th>
 * ```
 */
@Component({
  selector: "app-sort-header",
  standalone: true,
  imports: [CommonModule],
  template: `
    <button
      type="button"
      class="sort-header"
      [class.active]="isActive"
      [class.asc]="isActive && currentSortOrder === sortOrders.ASC"
      [class.desc]="isActive && currentSortOrder === sortOrders.DESC"
      (click)="toggleSort()"
    >
      <span class="sort-label">{{ label }}</span>
      <span class="sort-indicator" *ngIf="isActive">
        {{ currentSortOrder === sortOrders.ASC ? "↑" : "↓" }}
      </span>
      <span class="sort-indicator sort-inactive" *ngIf="!isActive">↕</span>
    </button>
  `,
  styles: [
    `
      .sort-header {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 0;
        font-size: inherit;
        font-weight: 600;
        color: #333;
        background: none;
        border: none;
        cursor: pointer;
        transition: color 0.15s ease-in-out;
      }

      .sort-header:hover {
        color: #007bff;
      }

      .sort-header.active {
        color: #007bff;
      }

      .sort-label {
        white-space: nowrap;
      }

      .sort-indicator {
        font-size: 12px;
        line-height: 1;
      }

      .sort-indicator.sort-inactive {
        opacity: 0.3;
      }

      .sort-header:hover .sort-inactive {
        opacity: 0.6;
      }
    `,
  ],
})
export class SortHeaderComponent {
  /** Field name for sorting */
  @Input() field = "";

  /** Display label */
  @Input() label = "";

  /** Current sort field */
  @Input() currentSortField: string | null = null;

  /** Current sort order */
  @Input() currentSortOrder: SortOrder = SortOrder.ASC;

  /** Emitted when sort changes */
  @Output() sortChange = new EventEmitter<{
    field: string;
    order: SortOrder;
  }>();

  sortOrders = SortOrder;

  get isActive(): boolean {
    return this.currentSortField === this.field;
  }

  toggleSort(): void {
    let newOrder: SortOrder;

    if (this.isActive) {
      // Toggle between ASC and DESC
      newOrder =
        this.currentSortOrder === SortOrder.ASC
          ? SortOrder.DESC
          : SortOrder.ASC;
    } else {
      // Default to ASC when first selecting
      newOrder = SortOrder.ASC;
    }

    this.sortChange.emit({ field: this.field, order: newOrder });
  }
}
