import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnChanges,
  SimpleChanges,
} from "@angular/core";
import { CommonModule } from "@angular/common";
import { FormsModule } from "@angular/forms";

import { PaginationMeta } from "../../../core/interfaces/pagination.interface";

@Component({
  selector: "app-pagination",
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: "./pagination.component.html",
  styleUrls: ["./pagination.component.scss"],
})
export class PaginationComponent implements OnChanges {
  @Input() meta: PaginationMeta | null = null;

  @Input() pageSizeOptions: number[] = [10, 20, 50, 100];

  @Input() maxPageButtons = 5;

  @Input() showPageSizeSelector = true;

  @Input() showItemsInfo = true;

  @Output() pageChange = new EventEmitter<number>();

  @Output() pageSizeChange = new EventEmitter<number>();

  currentPageSize = 20;
  jumpPage: number | null = null;

  pageNumbers: number[] = [];

  ngOnChanges(changes: SimpleChanges): void {
    if (changes["meta"] && this.meta) {
      this.currentPageSize = this.meta.size;
      this.jumpPage = this.meta.page;
      this.calculatePageNumbers();
    }
  }

  private calculatePageNumbers(): void {
    if (!this.meta) {
      this.pageNumbers = [];
      return;
    }

    const totalPages = this.meta.total_pages;
    const currentPage = this.meta.page;
    const maxButtons = this.maxPageButtons;

    if (totalPages <= maxButtons) {
      this.pageNumbers = Array.from({ length: totalPages }, (_, i) => i + 1);
    } else {
      let start = Math.max(1, currentPage - Math.floor(maxButtons / 2));
      let end = start + maxButtons - 1;

      if (end > totalPages) {
        end = totalPages;
        start = Math.max(1, end - maxButtons + 1);
      }

      this.pageNumbers = Array.from(
        { length: end - start + 1 },
        (_, i) => start + i,
      );
    }
  }


  goToPage(page: number): void {
    if (!this.meta) return;
    if (page < 1 || page > this.meta.total_pages) return;
    if (page === this.meta.page) return;

    this.pageChange.emit(page);
  }

  goToFirstPage(): void {
    this.goToPage(1);
  }

  goToLastPage(): void {
    if (this.meta) {
      this.goToPage(this.meta.total_pages);
    }
  }

  goToPreviousPage(): void {
    if (this.meta && this.meta.page > 1) {
      this.goToPage(this.meta.page - 1);
    }
  }

  goToNextPage(): void {
    if (this.meta && this.meta.page < this.meta.total_pages) {
      this.goToPage(this.meta.page + 1);
    }
  }

  onPageSizeChanged(): void {
    this.pageSizeChange.emit(this.currentPageSize);
  }

  onJumpSubmit(): void {
    if (this.jumpPage === null || this.jumpPage === undefined) {
      return;
    }
    this.goToPage(Number(this.jumpPage));
  }


  get itemsInfo(): string {
    if (!this.meta || this.meta.total_items === 0) {
      return "No items";
    }

    const start = (this.meta.page - 1) * this.meta.size + 1;
    const end = Math.min(
      this.meta.page * this.meta.size,
      this.meta.total_items,
    );

    return `${start}-${end} of ${this.meta.total_items}`;
  }

  get isFirstPage(): boolean {
    return !this.meta || this.meta.page <= 1;
  }

  get isLastPage(): boolean {
    return !this.meta || this.meta.page >= this.meta.total_pages;
  }

  get showEllipsisBefore(): boolean {
    return this.pageNumbers.length > 0 && this.pageNumbers[0] > 1;
  }

  get showEllipsisAfter(): boolean {
    if (!this.meta || this.pageNumbers.length === 0) return false;
    return (
      this.pageNumbers[this.pageNumbers.length - 1] < this.meta.total_pages
    );
  }
}
