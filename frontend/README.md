# Generic Filtering System - Angular Frontend

A portable, reusable Angular frontend implementing a generic filtering system that integrates with the FastAPI backend.

## Features

- **Generic Query Service**: Base service class for any API endpoint with filtering, pagination, sorting, and search
- **Filter Builder Component**: Dynamic UI for building complex filter rules
- **Data Table Component**: Sortable, paginated table with custom cell templates
- **Pagination Component**: Full-featured pagination with page size selector
- **Search Box Component**: Debounced search input
- **Sort Header Component**: Clickable sortable column headers
- **URL Grammar Support**: Filters are converted to URL parameters (e.g., `title_ilike=test`)

## Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── core/                    # Core functionality
│   │   │   ├── enums/               # TypeScript enums
│   │   │   │   ├── filter-operation.enum.ts
│   │   │   │   └── sort-order.enum.ts
│   │   │   ├── interfaces/          # TypeScript interfaces
│   │   │   │   ├── filter.interface.ts
│   │   │   │   ├── pagination.interface.ts
│   │   │   │   ├── saved-filter.interface.ts
│   │   │   │   └── field-config.interface.ts
│   │   │   └── services/            # Core services
│   │   │       ├── generic-query.service.ts
│   │   │       ├── saved-filter.service.ts
│   │   │       └── filter-state-manager.service.ts
│   │   │
│   │   ├── shared/                  # Shared/reusable components
│   │   │   └── components/
│   │   │       ├── filter-builder/
│   │   │       ├── pagination/
│   │   │       ├── data-table/
│   │   │       ├── search-box/
│   │   │       └── sort-header/
│   │   │
│   │   ├── features/                # Feature modules (examples)
│   │   │   ├── books/
│   │   │   │   ├── book.service.ts
│   │   │   │   └── book-list.component.ts
│   │   │   └── authors/
│   │   │       ├── author.service.ts
│   │   │       └── author-list.component.ts
│   │   │
│   │   ├── app.component.ts
│   │   ├── app.config.ts
│   │   └── app.routes.ts
│   │
│   ├── index.html
│   ├── main.ts
│   └── styles.scss
│
├── angular.json
├── package.json
├── proxy.conf.cjs
└── tsconfig.json
```

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start Development Server

```bash
npm start
```

The app will be available at `http://localhost:4200` and will proxy API requests to the first compatible local backend it finds.
By default it scans `127.0.0.1` on ports `8000, 8001, 8002, 8010, 8080` and verifies the backend exposes `/api/books` and `/api/authors`.

Optional environment variables for proxy discovery:

- `FILTER_API_TARGET` (single target URL or host:port)
- `FILTER_API_TARGETS` (comma-separated target URLs)
- `FILTER_API_PORTS` (comma-separated ports on `127.0.0.1`)
- `BACKEND_PORT` (single backend port)

### 3. Build for Production

```bash
npm run build
```

## How to Use

### Creating a New Model Service

Extend `GenericQueryService` for your model:

```typescript
import { Injectable } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { GenericQueryService } from "@core/services/generic-query.service";

export interface Product {
  id: number;
  name: string;
  price: number;
  category: string;
  // ... other fields
}

@Injectable({ providedIn: "root" })
export class ProductService extends GenericQueryService<Product> {
  protected baseUrl = "/api/products";

  constructor(http: HttpClient) {
    super(http);
  }
}
```

### Creating a List Component

```typescript
import { Component, OnInit } from '@angular/core';
import { ProductService, Product } from './product.service';
import { FilterableField, TableColumn } from '@core/interfaces';
import { FilterRule } from '@core/interfaces/filter.interface';
import { PaginationMeta } from '@core/interfaces/pagination.interface';
import { SortOrder } from '@core/enums';

// Import shared components
import { FilterBuilderComponent } from '@shared/components/filter-builder/filter-builder.component';
import { SearchBoxComponent } from '@shared/components/search-box/search-box.component';
import { DataTableComponent } from '@shared/components/data-table/data-table.component';

@Component({
  selector: 'app-product-list',
  standalone: true,
  imports: [FilterBuilderComponent, SearchBoxComponent, DataTableComponent],
  templateUrl: './product-list.component.html',
})
export class ProductListComponent implements OnInit {
  products: Product[] = [];
  pagination: PaginationMeta | null = null;
  loading = false;

  // Define filterable fields
  filterableFields: FilterableField[] = [
    { name: 'name', label: 'Name', type: 'text', sortable: true },
    { name: 'price', label: 'Price', type: 'number', sortable: true },
    { name: 'category', label: 'Category', type: 'select', options: [...] },
  ];

  // Define table columns
  tableColumns: TableColumn<Product>[] = [
    { field: 'id', header: 'ID', sortable: true },
    { field: 'name', header: 'Name', sortable: true },
    { field: 'price', header: 'Price', sortable: true, type: 'currency' },
    { field: 'category', header: 'Category', sortable: true },
  ];

  constructor(private productService: ProductService) {}

  ngOnInit() {
    this.loadProducts();
  }

  loadProducts() {
    this.loading = true;
    this.productService.query().subscribe({
      next: (response) => {
        this.products = response.data;
        this.pagination = response.meta;
        this.loading = false;
      },
      error: () => this.loading = false,
    });
  }

  // Event handlers...
}
```

### Filter Operations

The system supports all backend filter operations:

| Operation     | URL Grammar              | Description                 |
| ------------- | ------------------------ | --------------------------- |
| `eq`          | `field_eq=value`         | Equals                      |
| `ne`          | `field_ne=value`         | Not Equals                  |
| `gt`          | `field_gt=value`         | Greater Than                |
| `gte`         | `field_gte=value`        | Greater or Equal            |
| `lt`          | `field_lt=value`         | Less Than                   |
| `lte`         | `field_lte=value`        | Less or Equal               |
| `like`        | `field_like=value`       | Contains (case-sensitive)   |
| `ilike`       | `field_ilike=value`      | Contains (case-insensitive) |
| `in`          | `field_in=a,b,c`         | In List                     |
| `not_in`      | `field_not_in=a,b,c`     | Not In List                 |
| `is_null`     | `field_is_null=true`     | Is NULL                     |
| `is_not_null` | `field_is_not_null=true` | Is Not NULL                 |
| `between`     | `field_between=10,20`    | Between Range               |
| `starts_with` | `field_starts_with=val`  | Starts With                 |
| `ends_with`   | `field_ends_with=val`    | Ends With                   |

## Field Types

The filter builder supports different input types based on field configuration:

- **text**: Text input with string operations
- **number**: Number input with numeric operations
- **boolean**: Boolean select (true/false)
- **date**: Date picker
- **datetime**: DateTime picker
- **select**: Dropdown with predefined options
- **enum**: Similar to select, for enum values

## API Integration

### Request Format

The service automatically builds URL query parameters:

```
GET /api/products?page=1&size=20&sort_by=name&order=asc&name_ilike=widget&price_gte=10
```

### Response Format (Expected from Backend)

```json
{
  "data": [...],
  "meta": {
    "page": 1,
    "size": 20,
    "total_items": 150,
    "total_pages": 8,
    "has_next": true,
    "has_previous": false
  }
}
```

## Saved Filters

Use `SavedFilterService` to persist filter configurations:

```typescript
import { SavedFilterService } from "@core/services/saved-filter.service";

// Create a saved filter
this.savedFilterService
  .createFilter({
    name: "Expensive Products",
    model_name: "Product",
    filters: [{ field: "price", operation: "gte", value: 100 }],
    sort_by: "price",
    sort_order: "desc",
    page_size: 20,
  })
  .subscribe();

// Apply a saved filter
this.savedFilterService.applyFilter<Product>(filterId).subscribe((response) => {
  this.products = response.data;
});
```

## Customization

### Custom Cell Templates

```html
<app-data-table [data]="items" [columns]="columns">
  <ng-template #cellTemplate let-value let-row="row" let-column="column">
    <span *ngIf="column.field === 'status'" [class]="'status-' + value">
      {{ value }}
    </span>
  </ng-template>
</app-data-table>
```

### Styling

All components use SCSS and can be customized by:

1. Overriding CSS variables
2. Adding custom CSS classes via component inputs
3. Modifying the component's SCSS files directly

## License

MIT
