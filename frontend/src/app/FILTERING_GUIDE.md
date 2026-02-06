# Generic Filtering System - Frontend

A fully portable, configuration-driven filtering system for Angular applications.
Works with any FastAPI backend using the URL grammar filtering pattern.

## Quick Start

### 1. Add a New Entity

Create a config file for your entity in `src/app/config/entities/`:

```typescript
// src/app/config/entities/product.config.ts
import { FilterOperation } from "../../core/enums/filter-operation.enum";
import { SortOrder } from "../../core/enums/sort-order.enum";
import {
  EntityConfig,
  createFieldConfig,
  createColumnConfig,
  createQuickFilter,
} from "../../core/interfaces/entity-config.interface";

// Define your entity type
export interface Product {
  id: number;
  name: string;
  price: number;
  category: string;
  in_stock: boolean;
  created_at: string;
}

// Create the configuration
export const PRODUCT_CONFIG: EntityConfig<Product> = {
  name: "Product",
  pluralLabel: "Products",
  singularLabel: "Product",
  apiEndpoint: "/api/products",
  searchPlaceholder: "Search products...",
  emptyMessage: "No products found",

  defaults: {
    pageSize: 20,
    sortField: "id",
    sortOrder: SortOrder.DESC,
    pageSizeOptions: [10, 20, 50, 100],
  },

  // Define filterable/sortable fields
  fields: [
    createFieldConfig("name", "Name", "text", { searchable: true }),
    createFieldConfig("price", "Price", "number"),
    createFieldConfig("category", "Category", "select", {
      options: [
        { label: "Electronics", value: "electronics" },
        { label: "Clothing", value: "clothing" },
        { label: "Food", value: "food" },
      ],
    }),
    createFieldConfig("in_stock", "In Stock", "boolean"),
    createFieldConfig("created_at", "Created", "date"),
    // Relationship fields use dot notation
    createFieldConfig("supplier.name", "Supplier", "text", { sortable: false }),
  ],

  // Define table columns
  columns: [
    createColumnConfig<Product>("id", "ID", { width: "60px" }),
    createColumnConfig<Product>("name", "Name"),
    createColumnConfig<Product>("price", "Price", {
      type: "currency",
      width: "100px",
    }),
    createColumnConfig<Product>("category", "Category", { width: "120px" }),
    createColumnConfig<Product>("in_stock", "In Stock", {
      type: "boolean",
      width: "90px",
    }),
    createColumnConfig<Product>("created_at", "Created", {
      type: "date",
      width: "120px",
    }),
  ],

  // Optional: Quick filter presets
  quickFilters: [
    createQuickFilter(
      "in-stock",
      "In Stock",
      [{ field: "in_stock", operation: FilterOperation.EQUALS, value: true }],
      { icon: "✅" },
    ),

    createQuickFilter(
      "expensive",
      "Over $100",
      [{ field: "price", operation: FilterOperation.GREATER_THAN, value: 100 }],
      { icon: "💰" },
    ),
  ],

  // Optional: Group by options
  groupByOptions: [
    { field: "category", label: "Category", icon: "📁" },
    { field: "in_stock", label: "Stock Status", icon: "📦" },
  ],
};
```

### 2. Create the List Component

```typescript
// src/app/features/products/product-list.component.ts
import { Component } from "@angular/core";
import { EntityListComponent } from "../../shared/components/entity-list/entity-list.component";
import { PRODUCT_CONFIG, Product } from "../../config/entities/product.config";

@Component({
  selector: "app-product-list",
  standalone: true,
  imports: [EntityListComponent],
  template: `
    <app-entity-list
      [config]="config"
      [showHeader]="true"
      [description]="'Manage your product catalog'"
      [onRowClicked]="handleRowClick"
    ></app-entity-list>
  `,
})
export class ProductListComponent {
  config = PRODUCT_CONFIG;

  handleRowClick = (product: Product): void => {
    console.log("Product clicked:", product);
    // Navigate to detail page, open modal, etc.
  };
}
```

### 3. Add the Route

```typescript
// src/app/app.routes.ts
export const routes: Routes = [
  {
    path: "products",
    loadComponent: () =>
      import("./features/products/product-list.component").then(
        (m) => m.ProductListComponent,
      ),
  },
];
```

That's it! You now have a fully functional list page with:

- Advanced search panel (Odoo-style)
- Quick filters
- Custom filters
- Sorting
- Pagination
- Saved filters (favorites)

## Configuration Reference

### EntityConfig

| Property            | Type                  | Required | Description                          |
| ------------------- | --------------------- | -------- | ------------------------------------ |
| `name`              | `string`              | Yes      | Entity name (used for saved filters) |
| `pluralLabel`       | `string`              | Yes      | Display name (plural)                |
| `singularLabel`     | `string`              | Yes      | Display name (singular)              |
| `apiEndpoint`       | `string`              | Yes      | API endpoint path                    |
| `searchPlaceholder` | `string`              | No       | Search input placeholder             |
| `emptyMessage`      | `string`              | No       | Message when no results              |
| `fields`            | `FieldConfig[]`       | Yes      | Filterable fields                    |
| `columns`           | `ColumnConfig[]`      | Yes      | Table columns                        |
| `quickFilters`      | `QuickFilterConfig[]` | No       | Predefined filter presets            |
| `groupByOptions`    | `GroupByConfig[]`     | No       | Group by options                     |
| `defaults`          | `DefaultsConfig`      | No       | Default values                       |

### FieldConfig

| Property           | Type                                                                  | Description                                      |
| ------------------ | --------------------------------------------------------------------- | ------------------------------------------------ |
| `name`             | `string`                                                              | Field name (supports dot notation for relations) |
| `label`            | `string`                                                              | Display label                                    |
| `type`             | `'text' \| 'number' \| 'boolean' \| 'date' \| 'datetime' \| 'select'` | Field type                                       |
| `sortable`         | `boolean`                                                             | Can be sorted (default: true)                    |
| `searchable`       | `boolean`                                                             | Included in search (default: false)              |
| `defaultOperation` | `FilterOperation`                                                     | Default filter operation                         |
| `options`          | `SelectOption[]`                                                      | Options for select type                          |

### ColumnConfig

| Property   | Type                                                                                | Description                        |
| ---------- | ----------------------------------------------------------------------------------- | ---------------------------------- |
| `field`    | `string`                                                                            | Field name (supports dot notation) |
| `header`   | `string`                                                                            | Column header text                 |
| `sortable` | `boolean`                                                                           | Column is sortable                 |
| `type`     | `'text' \| 'number' \| 'currency' \| 'date' \| 'datetime' \| 'boolean' \| 'custom'` | Display type                       |
| `width`    | `string`                                                                            | Column width (CSS value)           |
| `template` | `string`                                                                            | Custom template identifier         |
| `format`   | `(value, row) => string`                                                            | Custom format function             |

### Filter Operations

Available filter operations (match your backend):

- `EQUALS` / `eq` - Exact match
- `NOT_EQUALS` / `ne` - Not equal
- `GREATER_THAN` / `gt` - Greater than
- `GREATER_EQUAL` / `gte` - Greater than or equal
- `LESS_THAN` / `lt` - Less than
- `LESS_EQUAL` / `lte` - Less than or equal
- `LIKE` / `like` - Contains (case-sensitive)
- `ILIKE` / `ilike` - Contains (case-insensitive)
- `STARTS_WITH` / `starts_with` - Starts with
- `ENDS_WITH` / `ends_with` - Ends with
- `IN` / `in` - In list
- `NOT_IN` / `not_in` - Not in list
- `IS_NULL` / `is_null` - Is empty
- `IS_NOT_NULL` / `is_not_null` - Is not empty
- `BETWEEN` / `between` - Between two values

## Backend Requirements

Your backend API should support:

1. **URL Grammar Filtering**: `GET /api/products?name_ilike=phone&price_gte=100`
2. **Pagination**: `?page=1&size=20`
3. **Sorting**: `?sort_by=price&order=asc`
4. **Search**: `?search=keyword`
5. **Saved Filters API** (optional):
   - `GET /api/saved-filters?model_name=Product`
   - `POST /api/saved-filters`
   - `DELETE /api/saved-filters/{id}`

Response format:

```json
{
  "data": [...],
  "meta": {
    "page": 1,
    "size": 20,
    "total_items": 100,
    "total_pages": 5
  }
}
```

## Customization

### Custom Row Click Handler

```typescript
handleRowClick = (product: Product): void => {
  this.router.navigate(["/products", product.id]);
};
```

### Extending EntityListComponent

For advanced customization, extend the base component:

```typescript
@Component({
  selector: "app-product-list",
  standalone: true,
  imports: [CommonModule, AdvancedSearchPanelComponent, DataTableComponent],
  templateUrl: "./product-list.component.html", // Custom template
})
export class ProductListComponent extends EntityListComponent<Product> {
  constructor() {
    super();
    this.config = PRODUCT_CONFIG;
  }

  // Override any method for custom behavior
  override loadData(): void {
    // Custom data loading logic
    super.loadData();
  }
}
```

### Using Individual Components

If you need more control, use the components directly:

```html
<app-advanced-search-panel
  [modelName]="'Product'"
  [fields]="fields"
  [quickFilters]="quickFilters"
  [activeFilters]="filters"
  (filtersChange)="onFiltersChange($event)"
  (searchChange)="onSearchChange($event)"
></app-advanced-search-panel>

<app-data-table
  [data]="products"
  [columns]="columns"
  [pagination]="pagination"
  (sortChange)="onSortChange($event)"
  (pageChange)="onPageChange($event)"
></app-data-table>
```

## File Structure

```
src/app/
├── config/
│   └── entities/           # Entity configurations
│       ├── index.ts
│       ├── book.config.ts
│       ├── author.config.ts
│       └── [your-entity].config.ts
├── core/
│   ├── enums/
│   │   ├── filter-operation.enum.ts
│   │   └── sort-order.enum.ts
│   ├── interfaces/
│   │   ├── entity-config.interface.ts  # Main config interface
│   │   ├── filter.interface.ts
│   │   ├── pagination.interface.ts
│   │   └── saved-filter.interface.ts
│   └── services/
│       ├── saved-filter.service.ts
│       └── filter-state-manager.service.ts
├── shared/
│   └── components/
│       ├── entity-list/                # Generic list component
│       ├── advanced-search-panel/      # Odoo-style search panel
│       ├── data-table/                 # Generic data table
│       ├── filter-builder/             # Filter rule builder
│       └── pagination/                 # Pagination controls
└── features/
    └── [your-feature]/
        └── [your-entity]-list.component.ts
```

## Porting to a New Project

1. Copy the `core/` folder (enums, interfaces, services)
2. Copy the `shared/components/` folder
3. Create your entity configs in `config/entities/`
4. Create feature components that use `EntityListComponent`
5. Ensure your backend supports the URL grammar filtering pattern
