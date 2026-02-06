import { Injectable } from "@angular/core";
import { HttpClient } from "@angular/common/http";

import { GenericQueryService } from "../../core/services/generic-query.service";

/**
 * Author interface matching backend AuthorResponse
 */
export interface Author {
  id: number;
  name: string;
  email: string;
  country?: string;
  birth_year?: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

/**
 * Author Service
 *
 * Extends GenericQueryService to provide author-specific API access.
 */
@Injectable({
  providedIn: "root",
})
export class AuthorService extends GenericQueryService<Author> {
  protected baseUrl = "/api/authors";

  constructor(http: HttpClient) {
    super(http);
  }
}
