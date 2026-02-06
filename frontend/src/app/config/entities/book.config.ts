import { FilterOperation } from "../../core/enums/filter-operation.enum";
import { SortOrder } from "../../core/enums/sort-order.enum";
import {
  EntityConfig,
  createFieldConfig,
  createColumnConfig,
  createQuickFilter,
} from "../../core/interfaces/entity-config.interface";

/**
 * Book entity interface
 */
export interface Book {
  id: number;
  title: string;
  genre: string;
  price: number;
  pages: number;
  published_year: number;
  rating: number;
  is_available: boolean;
  created_at: string;
  author?: {
    id: number;
    name: string;
    country: string;
    email: string;
    is_active: boolean;
  };
}

/**
 * Book Entity Configuration
 *
 * This file contains ALL the configuration for the Book entity's filtering UI.
 * When porting to a new project, create a similar config file for your entities.
 */
export const BOOK_CONFIG: EntityConfig<Book> = {
  // ===== ENTITY METADATA =====
  name: "Book",
  pluralLabel: "Books",
  singularLabel: "Book",
  apiEndpoint: "/api/books",
  searchPlaceholder: "Search books by title, author, genre...",
  emptyMessage: "No books found matching your criteria",

  // ===== DEFAULT VALUES =====
  defaults: {
    pageSize: 20,
    sortField: "id",
    sortOrder: SortOrder.DESC,
    pageSizeOptions: [10, 20, 50, 100],
  },

  // ===== FILTERABLE FIELDS =====
  fields: [
    createFieldConfig("title", "Title", "text", { searchable: true }),
    createFieldConfig("genre", "Genre", "select", {
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
    }),
    createFieldConfig("price", "Price", "number"),
    createFieldConfig("pages", "Pages", "number"),
    createFieldConfig("published_year", "Published Year", "number"),
    createFieldConfig("rating", "Rating", "number"),
    createFieldConfig("is_available", "Available", "boolean"),
    createFieldConfig("created_at", "Created Date", "date"),
    // Relationship fields (author)
    createFieldConfig("author.name", "Author Name", "text", {
      sortable: false,
    }),
    createFieldConfig("author.country", "Author Country", "text", {
      sortable: false,
    }),
    createFieldConfig("author.email", "Author Email", "text", {
      sortable: false,
    }),
    createFieldConfig("author.is_active", "Author Active", "boolean", {
      sortable: false,
    }),
  ],

  // ===== TABLE COLUMNS =====
  columns: [
    createColumnConfig<Book>("id", "ID", { width: "60px" }),
    createColumnConfig<Book>("title", "Title"),
    createColumnConfig<Book>("author.name", "Author", { sortable: false }),
    createColumnConfig<Book>("genre", "Genre", { width: "120px" }),
    createColumnConfig<Book>("price", "Price", {
      type: "currency",
      width: "100px",
    }),
    createColumnConfig<Book>("pages", "Pages", {
      type: "number",
      width: "80px",
    }),
    createColumnConfig<Book>("rating", "Rating", {
      type: "number",
      width: "80px",
    }),
    createColumnConfig<Book>("is_available", "Available", {
      type: "boolean",
      width: "90px",
    }),
    createColumnConfig<Book>("created_at", "Created", {
      type: "date",
      width: "120px",
    }),
  ],

  // ===== QUICK FILTERS (Predefined filter presets) =====
  quickFilters: [
    createQuickFilter(
      "available",
      "Available Books",
      [
        {
          field: "is_available",
          operation: FilterOperation.EQUALS,
          value: true,
        },
      ],
      { icon: "📗" },
    ),

    createQuickFilter(
      "high-rated",
      "High Rated (4+)",
      [{ field: "rating", operation: FilterOperation.GREATER_EQUAL, value: 4 }],
      { icon: "⭐" },
    ),

    createQuickFilter(
      "affordable",
      "Under $20",
      [{ field: "price", operation: FilterOperation.LESS_THAN, value: 20 }],
      { icon: "💰" },
    ),

    createQuickFilter(
      "recent",
      "Recent (2020+)",
      [
        {
          field: "published_year",
          operation: FilterOperation.GREATER_EQUAL,
          value: 2020,
        },
      ],
      { icon: "📅" },
    ),

    // Genre category
    createQuickFilter(
      "fiction",
      "Fiction",
      [{ field: "genre", operation: FilterOperation.EQUALS, value: "Fiction" }],
      { icon: "📖", category: "Genre" },
    ),

    createQuickFilter(
      "scifi",
      "Science Fiction",
      [
        {
          field: "genre",
          operation: FilterOperation.EQUALS,
          value: "Science Fiction",
        },
      ],
      { icon: "🚀", category: "Genre" },
    ),

    createQuickFilter(
      "fantasy",
      "Fantasy",
      [{ field: "genre", operation: FilterOperation.EQUALS, value: "Fantasy" }],
      { icon: "🧙", category: "Genre" },
    ),

    // Author category
    createQuickFilter(
      "active-author",
      "By Active Authors",
      [
        {
          field: "author.is_active",
          operation: FilterOperation.EQUALS,
          value: true,
        },
      ],
      { icon: "✍️", category: "Author" },
    ),
  ],

  // ===== GROUP BY OPTIONS =====
  groupByOptions: [
    { field: "genre", label: "Genre", icon: "📚" },
    { field: "author.name", label: "Author", icon: "✍️" },
    { field: "published_year", label: "Year", icon: "📅" },
    { field: "is_available", label: "Availability", icon: "📗" },
  ],
};
