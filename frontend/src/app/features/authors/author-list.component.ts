import { Component, OnInit, OnDestroy } from "@angular/core";
import { CommonModule } from "@angular/common";
import { Subject } from "rxjs";
import { takeUntil } from "rxjs/operators";

import { AuthorService, Author } from "./author.service";
import {
  FilterableField,
  TableColumn,
} from "../../core/interfaces/field-config.interface";
import { FilterRule } from "../../core/interfaces/filter.interface";
import { PaginationMeta } from "../../core/interfaces/pagination.interface";
import { FilterOperation } from "../../core/enums/filter-operation.enum";
import { SortOrder } from "../../core/enums/sort-order.enum";

import { FilterBuilderComponent } from "../../shared/components/filter-builder/filter-builder.component";
import { SearchBoxComponent } from "../../shared/components/search-box/search-box.component";
import { DataTableComponent } from "../../shared/components/data-table/data-table.component";

/**
 * Author List Component
 *
 * Demonstrates how to use the generic filtering system with the Author model.
 */
@Component({
  selector: "app-author-list",
  standalone: true,
  imports: [
    CommonModule,
    FilterBuilderComponent,
    SearchBoxComponent,
    DataTableComponent,
  ],
  templateUrl: "./author-list.component.html",
  styleUrls: ["./author-list.component.scss"],
})
export class AuthorListComponent implements OnInit, OnDestroy {
  // Data
  authors: Author[] = [];
  pagination: PaginationMeta | null = null;
  loading = false;

  // Current filter state
  filters: FilterRule[] = [];
  search = "";
  sortField: string | null = "id";
  sortOrder: SortOrder = SortOrder.DESC;

  // Filterable fields configuration
  filterableFields: FilterableField[] = [
    {
      name: "name",
      label: "Name",
      type: "text",
      sortable: true,
      searchable: true,
      defaultOperation: FilterOperation.ILIKE,
    },
    {
      name: "email",
      label: "Email",
      type: "text",
      sortable: true,
      searchable: true,
    },
    {
      name: "country",
      label: "Country",
      type: "text",
      sortable: true,
      searchable: true,
    },
    {
      name: "birth_year",
      label: "Birth Year",
      type: "number",
      sortable: true,
    },
    {
      name: "is_active",
      label: "Active",
      type: "boolean",
      sortable: true,
    },
    {
      name: "created_at",
      label: "Created Date",
      type: "date",
      sortable: true,
    },
  ];

  // Table columns configuration
  tableColumns: TableColumn<Author>[] = [
    { field: "id", header: "ID", sortable: true, width: "60px" },
    { field: "name", header: "Name", sortable: true },
    { field: "email", header: "Email", sortable: true },
    { field: "country", header: "Country", sortable: true, width: "120px" },
    {
      field: "birth_year",
      header: "Birth Year",
      sortable: true,
      type: "number",
      width: "100px",
    },
    {
      field: "is_active",
      header: "Active",
      sortable: true,
      type: "boolean",
      width: "80px",
    },
    {
      field: "created_at",
      header: "Created",
      sortable: true,
      type: "date",
      width: "120px",
    },
  ];

  private destroy$ = new Subject<void>();

  constructor(private authorService: AuthorService) {}

  ngOnInit(): void {
    this.loadAuthors();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadAuthors(): void {
    this.loading = true;

    this.authorService.setFilters(this.filters);
    this.authorService.setSearch(this.search || null);
    this.authorService.setSort({
      sort_by: this.sortField,
      order: this.sortOrder,
    });

    this.authorService
      .query()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.authors = response.data;
          this.pagination = response.meta;
          this.loading = false;
        },
        error: (error) => {
          console.error("Error loading authors:", error);
          this.loading = false;
        },
      });
  }

  onFiltersApply(filters: FilterRule[]): void {
    this.filters = filters;
    this.loadAuthors();
  }

  onFiltersClear(): void {
    this.filters = [];
    this.loadAuthors();
  }

  onSearchChange(search: string): void {
    this.search = search;
    this.loadAuthors();
  }

  onSortChange(event: { field: string; order: SortOrder }): void {
    this.sortField = event.field;
    this.sortOrder = event.order;
    this.loadAuthors();
  }

  onPageChange(page: number): void {
    this.authorService.setPagination({ page });
    this.loadAuthors();
  }

  onPageSizeChange(size: number): void {
    this.authorService.setPagination({ page: 1, size });
    this.loadAuthors();
  }

  onRowClick(author: Author): void {
    console.log("Author clicked:", author);
  }
}
