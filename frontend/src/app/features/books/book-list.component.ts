import { Component, OnInit, OnDestroy } from "@angular/core";
import { CommonModule } from "@angular/common";
import { Subject } from "rxjs";
import { takeUntil } from "rxjs/operators";

import { BookService, Book } from "./book.service";
import { SavedFilterService } from "../../core/services/saved-filter.service";
import {
  FilterableField,
  TableColumn,
} from "../../core/interfaces/field-config.interface";
import { FilterRule } from "../../core/interfaces/filter.interface";
import {
  SavedFilter,
  SavedFilterCreate,
} from "../../core/interfaces/saved-filter.interface";
import { PaginationMeta } from "../../core/interfaces/pagination.interface";
import { FilterOperation } from "../../core/enums/filter-operation.enum";
import { SortOrder } from "../../core/enums/sort-order.enum";

import {
  AdvancedSearchPanelComponent,
  QuickFilter,
  GroupByOption,
} from "../../shared/components/advanced-search-panel/advanced-search-panel.component";
import { DataTableComponent } from "../../shared/components/data-table/data-table.component";

/**
 * Book List Component
 *
 * Demonstrates how to use the generic filtering system with the Book model.
 * Shows integration of all filtering components with Odoo-style advanced search panel.
 */
@Component({
  selector: "app-book-list",
  standalone: true,
  imports: [CommonModule, AdvancedSearchPanelComponent, DataTableComponent],
  templateUrl: "./book-list.component.html",
  styleUrls: ["./book-list.component.scss"],
})
export class BookListComponent implements OnInit, OnDestroy {
  // Data
  books: Book[] = [];
  pagination: PaginationMeta | null = null;
  loading = false;

  // Current filter state
  filters: FilterRule[] = [];
  search = "";
  sortField: string | null = "id";
  sortOrder: SortOrder = SortOrder.DESC;

  // Saved filters (favorites) from database
  savedFilters: SavedFilter[] = [];

  // Entity name for saved filters (must match model_name in database)
  entityName = "Book";

  // Quick filters - predefined filter presets
  quickFilters: QuickFilter[] = [
    {
      id: "available",
      label: "Available Books",
      icon: "📗",
      filters: [
        {
          field: "is_available",
          operation: FilterOperation.EQUALS,
          value: true,
        },
      ],
    },
    {
      id: "high-rated",
      label: "High Rated (4+)",
      icon: "⭐",
      filters: [
        { field: "rating", operation: FilterOperation.GREATER_EQUAL, value: 4 },
      ],
    },
    {
      id: "affordable",
      label: "Under $20",
      icon: "💰",
      filters: [
        { field: "price", operation: FilterOperation.LESS_THAN, value: 20 },
      ],
    },
    {
      id: "recent",
      label: "Recent (2020+)",
      icon: "📅",
      filters: [
        {
          field: "published_year",
          operation: FilterOperation.GREATER_EQUAL,
          value: 2020,
        },
      ],
    },
    {
      id: "fiction",
      label: "Fiction",
      icon: "📖",
      category: "Genre",
      filters: [
        { field: "genre", operation: FilterOperation.EQUALS, value: "Fiction" },
      ],
    },
    {
      id: "scifi",
      label: "Science Fiction",
      icon: "🚀",
      category: "Genre",
      filters: [
        {
          field: "genre",
          operation: FilterOperation.EQUALS,
          value: "Science Fiction",
        },
      ],
    },
    {
      id: "fantasy",
      label: "Fantasy",
      icon: "🧙",
      category: "Genre",
      filters: [
        { field: "genre", operation: FilterOperation.EQUALS, value: "Fantasy" },
      ],
    },
    {
      id: "active-author",
      label: "By Active Authors",
      icon: "✍️",
      category: "Author",
      filters: [
        {
          field: "author.is_active",
          operation: FilterOperation.EQUALS,
          value: true,
        },
      ],
    },
  ];

  // Group by options
  groupByOptions: GroupByOption[] = [
    { field: "genre", label: "Genre", icon: "📚" },
    { field: "author.name", label: "Author", icon: "✍️" },
    { field: "published_year", label: "Year", icon: "📅" },
    { field: "is_available", label: "Availability", icon: "📗" },
  ];

  // Filterable fields configuration
  filterableFields: FilterableField[] = [
    {
      name: "title",
      label: "Title",
      type: "text",
      sortable: true,
      searchable: true,
      defaultOperation: FilterOperation.ILIKE,
    },
    {
      name: "genre",
      label: "Genre",
      type: "select",
      sortable: true,
      options: [
        { label: "Fiction", value: "Fiction" },
        { label: "Non-Fiction", value: "Non-Fiction" },
        { label: "Science Fiction", value: "Science Fiction" },
        { label: "Fantasy", value: "Fantasy" },
        { label: "Mystery", value: "Mystery" },
        { label: "Romance", value: "Romance" },
        { label: "Thriller", value: "Thriller" },
        { label: "Horror", value: "Horror" },
        { label: "Biography", value: "Biography" },
        { label: "History", value: "History" },
      ],
    },
    {
      name: "price",
      label: "Price",
      type: "number",
      sortable: true,
    },
    {
      name: "pages",
      label: "Pages",
      type: "number",
      sortable: true,
    },
    {
      name: "published_year",
      label: "Published Year",
      type: "number",
      sortable: true,
    },
    {
      name: "rating",
      label: "Rating",
      type: "number",
      sortable: true,
    },
    {
      name: "is_available",
      label: "Available",
      type: "boolean",
      sortable: true,
    },
    {
      name: "created_at",
      label: "Created Date",
      type: "date",
      sortable: true,
    },
    // ============ RELATIONSHIP FILTERS (Author) ============
    {
      name: "author.name",
      label: "Author Name",
      type: "text",
      sortable: false, // Sorting on relationships requires backend support
      defaultOperation: FilterOperation.ILIKE,
    },
    {
      name: "author.country",
      label: "Author Country",
      type: "text",
      sortable: false,
      defaultOperation: FilterOperation.ILIKE,
    },
    {
      name: "author.email",
      label: "Author Email",
      type: "text",
      sortable: false,
    },
    {
      name: "author.is_active",
      label: "Author Active",
      type: "boolean",
      sortable: false,
    },
  ];

  // Table columns configuration
  tableColumns: TableColumn<Book>[] = [
    { field: "id", header: "ID", sortable: true, width: "60px" },
    { field: "title", header: "Title", sortable: true },
    { field: "author.name", header: "Author", sortable: false },
    { field: "genre", header: "Genre", sortable: true, width: "120px" },
    {
      field: "price",
      header: "Price",
      sortable: true,
      type: "currency",
      width: "100px",
    },
    {
      field: "pages",
      header: "Pages",
      sortable: true,
      type: "number",
      width: "80px",
    },
    {
      field: "rating",
      header: "Rating",
      sortable: true,
      type: "number",
      width: "80px",
    },
    {
      field: "is_available",
      header: "Available",
      sortable: true,
      type: "boolean",
      width: "90px",
    },
    {
      field: "created_at",
      header: "Created",
      sortable: true,
      type: "date",
      width: "120px",
    },
  ];

  // Currently selected group by field
  groupBy: string | null = null;

  private destroy$ = new Subject<void>();

  constructor(
    private bookService: BookService,
    private savedFilterService: SavedFilterService,
  ) {}

  ngOnInit(): void {
    this.loadBooks();
    this.loadSavedFilters();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // ===========================================================================
  // DATA LOADING
  // ===========================================================================

  loadBooks(): void {
    this.loading = true;

    // Set up query state
    this.bookService.setFilters(this.filters);
    this.bookService.setSearch(this.search || null);
    this.bookService.setSort({
      sort_by: this.sortField,
      order: this.sortOrder,
    });

    // Execute query
    this.bookService
      .query()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.books = response.data;
          this.pagination = response.meta;
          this.loading = false;
        },
        error: (error) => {
          console.error("Error loading books:", error);
          this.loading = false;
        },
      });
  }

  // ===========================================================================
  // EVENT HANDLERS
  // ===========================================================================

  onFiltersChange(filters: FilterRule[]): void {
    this.filters = filters;
    this.loadBooks();
  }

  onSearchChange(search: string): void {
    this.search = search;
    this.loadBooks();
  }

  onSortChange(event: { field: string | null; order: SortOrder }): void {
    this.sortField = event.field;
    this.sortOrder = event.order;
    this.loadBooks();
  }

  onGroupByChange(field: string | null): void {
    this.groupBy = field;
    // Group by could be implemented via backend or client-side grouping
    console.log("Group by changed:", field);
    // For now, just log - actual grouping logic would go here
  }

  onPageChange(page: number): void {
    this.bookService.setPagination({ page });
    this.loadBooks();
  }

  onPageSizeChange(size: number): void {
    this.bookService.setPagination({ page: 1, size });
    this.loadBooks();
  }

  onRowClick(book: Book): void {
    console.log("Book clicked:", book);
    // Navigate to book detail or open modal
  }

  // ===========================================================================
  // SAVED FILTERS (FAVORITES)
  // ===========================================================================

  loadSavedFilters(): void {
    console.log("Loading saved filters for model:", this.entityName);
    this.savedFilterService
      .getFilters(this.entityName)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (filters: SavedFilter[]) => {
          console.log("Loaded saved filters:", filters);
          this.savedFilters = filters;
        },
        error: (error: Error) => {
          console.error("Error loading saved filters:", error);
        },
      });
  }

  onSaveFilter(filterData: SavedFilterCreate): void {
    console.log("Saving filter:", filterData);
    this.savedFilterService
      .createFilter(filterData)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (savedFilter: SavedFilter) => {
          console.log("Filter saved successfully:", savedFilter);
          this.savedFilters = [...this.savedFilters, savedFilter];
        },
        error: (error: Error) => {
          console.error("Error saving filter:", error);
        },
      });
  }

  onApplySavedFilter(filter: SavedFilter): void {
    // Apply the saved filter's settings
    this.filters = filter.filters || [];
    this.search = filter.search_query || "";
    this.sortField = filter.sort_by || "id";
    this.sortOrder = (filter.sort_order as SortOrder) || SortOrder.DESC;

    if (filter.page_size) {
      this.bookService.setPagination({ page: 1, size: filter.page_size });
    }

    this.loadBooks();
  }

  onDeleteSavedFilter(filterId: number): void {
    this.savedFilterService
      .deleteFilter(filterId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.savedFilters = this.savedFilters.filter(
            (f) => f.id !== filterId,
          );
          console.log("Filter deleted successfully");
        },
        error: (error: Error) => {
          console.error("Error deleting filter:", error);
        },
      });
  }
}
