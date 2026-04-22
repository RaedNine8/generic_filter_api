import { Routes } from "@angular/router";

export const routes: Routes = [
  {
    path: "",
    redirectTo: "books",
    pathMatch: "full",
  },
  // FILTERX:ROUTES
  {
    path: "books",
    loadComponent: () =>
      import("./features/books/book-list-new.component").then(
        (m) => m.BookListComponent,
      ),
    title: "Books - Generic Filter System",
  },
  {
    path: "authors",
    loadComponent: () =>
      import("./features/authors/author-list-new.component").then(
        (m) => m.AuthorListComponent,
      ),
    title: "Authors - Generic Filter System",
  },
  {
    path: "**",
    redirectTo: "books",
  },
];
