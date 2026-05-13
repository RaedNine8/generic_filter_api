import {
  Component,
  Input,
  Output,
  EventEmitter,
  HostListener,
} from "@angular/core";
import { CommonModule } from "@angular/common";

import { SortOrder } from "../../../core/enums/sort-order.enum";

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
        gap: 6px;
        padding: 0;
        font-size: inherit;
        font-weight: 700;
        color: var(--color-text-muted);
        background: none;
        border: none;
        cursor: pointer;
        transition: color 0.15s ease-in-out;
      }

      .sort-header:hover {
        color: var(--color-primary);
      }

      .sort-header.active {
        color: var(--color-primary);
      }

      .sort-label {
        white-space: nowrap;
      }

      .sort-indicator {
        font-size: 12px;
        line-height: 1;
        font-weight: 800;
      }

      .sort-indicator.sort-inactive {
        opacity: 0.45;
      }

      .sort-header:hover .sort-inactive {
        opacity: 0.75;
      }
    `,
  ],
})
export class SortHeaderComponent {
  @Input() field = "";

  @Input() label = "";

  @Input() currentSortField: string | null = null;

  @Input() currentSortOrder: SortOrder = SortOrder.ASC;

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
      newOrder =
        this.currentSortOrder === SortOrder.ASC
          ? SortOrder.DESC
          : SortOrder.ASC;
    } else {
      newOrder = SortOrder.ASC;
    }

    this.sortChange.emit({ field: this.field, order: newOrder });
  }
}
