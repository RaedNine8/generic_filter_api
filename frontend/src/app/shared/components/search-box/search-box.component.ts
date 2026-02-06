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
import { debounceTime, distinctUntilChanged, takeUntil } from "rxjs/operators";

/**
 * Search Box Component
 *
 * A reusable search input with debounce support.
 *
 * Features:
 * - Debounced search input
 * - Clear button
 * - Loading indicator support
 * - Customizable placeholder
 *
 * Usage:
 * ```html
 * <app-search-box
 *   [placeholder]="'Search books...'"
 *   [debounceMs]="300"
 *   (searchChange)="onSearch($event)">
 * </app-search-box>
 * ```
 */
@Component({
  selector: "app-search-box",
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: "./search-box.component.html",
  styleUrls: ["./search-box.component.scss"],
})
export class SearchBoxComponent implements OnInit, OnDestroy {
  /** Placeholder text */
  @Input() placeholder = "Search...";

  /** Debounce time in milliseconds */
  @Input() debounceMs = 300;

  /** Initial search value */
  @Input() value = "";

  /** Minimum characters before search triggers */
  @Input() minLength = 0;

  /** Show loading indicator */
  @Input() loading = false;

  /** Show clear button */
  @Input() showClear = true;

  /** Emitted when search value changes (debounced) */
  @Output() searchChange = new EventEmitter<string>();

  /** Emitted when user presses Enter */
  @Output() searchSubmit = new EventEmitter<string>();

  /** Emitted when clear button is clicked */
  @Output() searchClear = new EventEmitter<void>();

  searchValue = "";
  private searchSubject = new Subject<string>();
  private destroy$ = new Subject<void>();

  ngOnInit(): void {
    this.searchValue = this.value;

    this.searchSubject
      .pipe(
        debounceTime(this.debounceMs),
        distinctUntilChanged(),
        takeUntil(this.destroy$),
      )
      .subscribe((value) => {
        if (value.length === 0 || value.length >= this.minLength) {
          this.searchChange.emit(value);
        }
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onInput(): void {
    this.searchSubject.next(this.searchValue);
  }

  onKeydown(event: KeyboardEvent): void {
    if (event.key === "Enter") {
      this.searchSubmit.emit(this.searchValue);
    }
  }

  clearSearch(): void {
    this.searchValue = "";
    this.searchSubject.next("");
    this.searchClear.emit();
  }

  get showClearButton(): boolean {
    return this.showClear && this.searchValue.length > 0;
  }
}
