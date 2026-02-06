import { Component } from "@angular/core";
import { Router } from "@angular/router";
import { EntityListComponent } from "../../shared/components/entity-list/entity-list.component";
import { AUTHOR_CONFIG, Author } from "../../config/entities/author.config";

/**
 * Author List Component
 *
 * Uses the generic EntityListComponent with AUTHOR_CONFIG.
 */
@Component({
  selector: "app-author-list",
  standalone: true,
  imports: [EntityListComponent],
  template: `
    <app-entity-list
      [config]="config"
      [showHeader]="true"
      [description]="'Manage authors in the system.'"
      [clickableRows]="true"
      [onRowClicked]="handleRowClick"
    ></app-entity-list>
  `,
})
export class AuthorListComponent {
  config = AUTHOR_CONFIG;

  constructor(private router: Router) {}

  handleRowClick = (author: Author): void => {
    console.log("Author clicked:", author);
    // Example: this.router.navigate(['/authors', author.id]);
  };
}
