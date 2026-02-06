import { Component } from "@angular/core";
import { Router } from "@angular/router";
import { EntityListComponent } from "../../shared/components/entity-list/entity-list.component";
import { BOOK_CONFIG, Book } from "../../config/entities/book.config";

/**
 * Book List Component
 *
 * This component uses the generic EntityListComponent with the BOOK_CONFIG.
 * All the filtering logic is inherited - you only need to provide the config.
 *
 * For custom behavior, override methods from EntityListComponent.
 */
@Component({
  selector: "app-book-list",
  standalone: true,
  imports: [EntityListComponent],
  template: `
    <app-entity-list
      [config]="config"
      [showHeader]="true"
      [description]="
        'Browse and filter the book collection using the advanced search panel.'
      "
      [clickableRows]="true"
      [onRowClicked]="handleRowClick"
    ></app-entity-list>
  `,
})
export class BookListComponent {
  config = BOOK_CONFIG;

  constructor(private router: Router) {}

  // Custom row click handler - navigate to book detail
  handleRowClick = (book: Book): void => {
    console.log("Book clicked:", book);
    // Example: this.router.navigate(['/books', book.id]);
  };
}
