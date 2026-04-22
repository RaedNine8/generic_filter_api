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

@Component({
  selector: "app-search-box",
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: "./search-box.component.html",
  styleUrls: ["./search-box.component.scss"],
})
export class SearchBoxComponent implements OnInit, OnDestroy {
  @Input() placeholder = "Search...";

  @Input() debounceMs = 300;

  @Input() value = "";

  @Input() minLength = 0;

  @Input() loading = false;

  @Input() showClear = true;

  @Output() searchChange = new EventEmitter<string>();

  @Output() searchSubmit = new EventEmitter<string>();

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
