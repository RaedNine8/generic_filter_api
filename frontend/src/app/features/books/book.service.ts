import { Injectable } from "@angular/core";
import { HttpClient } from "@angular/common/http";

import { GenericQueryService } from "../../core/services/generic-query.service";

/**
 * Book interface matching backend BookResponse
 */
export interface Book {
  id: number;
  title: string;
  isbn: string;
  genre?: string;
  description?: string;
  price: number;
  pages?: number;
  published_year?: number;
  is_available: boolean;
  rating?: number;
  author_id: number;
  created_at: string;
  updated_at?: string;
  author?: {
    id: number;
    name: string;
    email: string;
    country?: string;
    is_active: boolean;
  };
}

/**
 * Book Service
 *
 * Extends GenericQueryService to provide book-specific API access.
 * Demonstrates how to create model-specific services using the generic base.
 */
@Injectable({
  providedIn: "root",
})
export class BookService extends GenericQueryService<Book> {
  protected baseUrl = "/api/books";

  constructor(http: HttpClient) {
    super(http);
  }
}
