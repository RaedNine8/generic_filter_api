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
import { FilterTreeNode, generateNodeId } from "../../core/interfaces/filter-tree.interface";
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

  // Current filter state — tree-only (no flat filters)
  filterTree: FilterTreeNode | null = null;
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

  // Filterable fields will be populated dynamically from backend metadata
  filterableFields: FilterableField[] = [];

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
    this.loadMetadata();
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

  loadMetadata(): void {
    this.bookService.getMetadata()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (metadata) => {
          const dynamicFields: FilterableField[] = metadata.fields.map((f: any) => {
            let fieldType: 'text' | 'number' | 'boolean' | 'date' | 'datetime' | 'select' = 'text';
            if (f.type === 'integer' || f.type === 'float' || f.type === 'decimal') fieldType = 'number';
            else if (f.type === 'boolean') fieldType = 'boolean';
            else if (f.type === 'date') fieldType = 'date';
            else if (f.type === 'datetime') fieldType = 'datetime';
            else if (f.type === 'enum') fieldType = 'select';

            // Convert 'first_name' -> 'First Name'
            const label = f.name.split('_').map((word: string) => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');

            return {
              name: f.name,
              label: label,
              type: fieldType,
              sortable: true,
              searchable: true,
              defaultOperation: fieldType === 'text' ? FilterOperation.ILIKE : FilterOperation.EQUALS,
              options: f.type === 'enum' ? [] : undefined // Backend would need to provide options
            };
          });

          // Add basic relationship fields
          metadata.relationships.forEach((rel: any) => {
            const relLabel = rel.name.charAt(0).toUpperCase() + rel.name.slice(1);
            dynamicFields.push({
              name: `${rel.name}.name`,
              label: `${relLabel} Name`,
              type: 'text',
              sortable: false,
              searchable: true,
              defaultOperation: FilterOperation.ILIKE
            });
          });

          this.filterableFields = dynamicFields;
        },
        error: (error) => {
          console.error("Error loading metadata:", error);
        }
      });
  }

  loadBooks(): void {
    this.loading = true;

    // Set up query state — tree-only
    this.bookService.setFilterTree(this.filterTree);
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
    // Legacy flat filters are now converted into tree conditions
    // This is kept for backward compatibility with QuickFilters
    if (filters.length > 0) {
      const conditions: FilterTreeNode[] = filters.map(f => ({
        id: generateNodeId(),
        nodeType: 'condition' as const,
        field: f.field,
        operation: f.operation as FilterOperation,
        value: f.value
      }));
      const andRoot: FilterTreeNode = {
        id: generateNodeId(),
        nodeType: 'operator',
        operator: 'AND',
        children: conditions,
        expanded: true
      };
      this.filterTree = andRoot;
    } else {
      this.filterTree = null;
    }
    this.loadBooks();
  }

  onTreeChange(tree: FilterTreeNode | null): void {
    this.filterTree = tree;
    this.loadBooks();
  }

  onSearchChange(search: string): void {
    this.search = search;
    // Don't reload on every keystroke — the Odoo-style dropdown
    // will handle adding structured filters. Only reload when
    // the search is cleared (user removed the text).
    if (!search) {
      this.loadBooks();
    }
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
    // Apply the saved filter's settings — tree-only
    this.filterTree = filter.filter_tree || null;
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
