import { FilterOperation } from "../../core/enums/filter-operation.enum";
import { SortOrder } from "../../core/enums/sort-order.enum";
import {
  EntityConfig,
  createFieldConfig,
  createColumnConfig,
  createQuickFilter,
} from "../../core/interfaces/entity-config.interface";

/**
 * Author entity interface
 */
export interface Author {
  id: number;
  name: string;
  email: string;
  country: string;
  birth_date: string;
  is_active: boolean;
  created_at: string;
}

/**
 * Author Entity Configuration
 */
export const AUTHOR_CONFIG: EntityConfig<Author> = {
  name: "Author",
  pluralLabel: "Authors",
  singularLabel: "Author",
  apiEndpoint: "/api/authors",
  searchPlaceholder: "Search authors by name, email, country...",
  emptyMessage: "No authors found matching your criteria",

  defaults: {
    pageSize: 20,
    sortField: "id",
    sortOrder: SortOrder.DESC,
    pageSizeOptions: [10, 20, 50, 100],
  },

  fields: [
    createFieldConfig("name", "Name", "text", { searchable: true }),
    createFieldConfig("email", "Email", "text", { searchable: true }),
    createFieldConfig("country", "Country", "text"),
    createFieldConfig("birth_date", "Birth Date", "date"),
    createFieldConfig("is_active", "Active", "boolean"),
    createFieldConfig("created_at", "Created Date", "date"),
  ],

  columns: [
    createColumnConfig<Author>("id", "ID", { width: "60px" }),
    createColumnConfig<Author>("name", "Name"),
    createColumnConfig<Author>("email", "Email"),
    createColumnConfig<Author>("country", "Country", { width: "120px" }),
    createColumnConfig<Author>("birth_date", "Birth Date", {
      type: "date",
      width: "120px",
    }),
    createColumnConfig<Author>("is_active", "Active", {
      type: "boolean",
      width: "80px",
    }),
    createColumnConfig<Author>("created_at", "Created", {
      type: "date",
      width: "120px",
    }),
  ],

  quickFilters: [
    createQuickFilter(
      "active",
      "Active Authors",
      [{ field: "is_active", operation: FilterOperation.EQUALS, value: true }],
      { icon: "✅" },
    ),

    createQuickFilter(
      "inactive",
      "Inactive Authors",
      [{ field: "is_active", operation: FilterOperation.EQUALS, value: false }],
      { icon: "❌" },
    ),

    createQuickFilter(
      "usa",
      "From USA",
      [{ field: "country", operation: FilterOperation.EQUALS, value: "USA" }],
      { icon: "🇺🇸", category: "Country" },
    ),

    createQuickFilter(
      "uk",
      "From UK",
      [{ field: "country", operation: FilterOperation.EQUALS, value: "UK" }],
      { icon: "🇬🇧", category: "Country" },
    ),
  ],

  groupByOptions: [
    { field: "country", label: "Country", icon: "🌍" },
    { field: "is_active", label: "Status", icon: "📊" },
  ],
};
