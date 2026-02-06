import { Injectable } from "@angular/core";
import {
  HttpClient,
  HttpParams,
  HttpErrorResponse,
} from "@angular/common/http";
import { Observable, throwError } from "rxjs";
import { catchError, map } from "rxjs/operators";

import {
  SavedFilter,
  SavedFilterCreate,
  SavedFilterUpdate,
  SavedFilterApplyResponse,
} from "../interfaces/saved-filter.interface";
import { FilterRule } from "../interfaces/filter.interface";
import { PaginatedResponse } from "../interfaces/pagination.interface";

/**
 * Saved Filter Service
 *
 * Service for managing saved filters - CRUD operations and applying filters.
 * Works with the /api/saved-filters backend endpoints.
 *
 * Features:
 * - Create, read, update, delete saved filters
 * - Apply saved filters to get filtered results
 * - List filters by model name
 */
@Injectable({
  providedIn: "root",
})
export class SavedFilterService {
  private readonly baseUrl = "/api/saved-filters";

  constructor(private http: HttpClient) {}

  // ===========================================================================
  // CRUD OPERATIONS
  // ===========================================================================

  /**
   * Create a new saved filter
   * POST /api/saved-filters
   */
  createFilter(filter: SavedFilterCreate): Observable<SavedFilter> {
    return this.http
      .post<SavedFilter>(this.baseUrl, filter)
      .pipe(catchError(this.handleError));
  }

  /**
   * Get all saved filters, optionally filtered by model name
   * GET /api/saved-filters?model_name=X
   */
  getFilters(modelName?: string): Observable<SavedFilter[]> {
    let params = new HttpParams();
    if (modelName) {
      params = params.set("model_name", modelName);
    }

    return this.http
      .get<SavedFilter[]>(this.baseUrl, { params })
      .pipe(catchError(this.handleError));
  }

  /**
   * Get a specific saved filter by ID
   * GET /api/saved-filters/{filter_id}
   */
  getFilterById(filterId: number): Observable<SavedFilter> {
    return this.http
      .get<SavedFilter>(`${this.baseUrl}/${filterId}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Update an existing saved filter
   * PUT /api/saved-filters/{filter_id}
   */
  updateFilter(
    filterId: number,
    update: SavedFilterUpdate,
  ): Observable<SavedFilter> {
    return this.http
      .put<SavedFilter>(`${this.baseUrl}/${filterId}`, update)
      .pipe(catchError(this.handleError));
  }

  /**
   * Delete a saved filter
   * DELETE /api/saved-filters/{filter_id}
   */
  deleteFilter(filterId: number): Observable<void> {
    return this.http
      .delete<void>(`${this.baseUrl}/${filterId}`)
      .pipe(catchError(this.handleError));
  }

  // ===========================================================================
  // FILTER APPLICATION
  // ===========================================================================

  /**
   * Apply a saved filter and get results
   * GET /api/saved-filters/{filter_id}/apply?page=1
   */
  applyFilter<T = any>(
    filterId: number,
    page = 1,
  ): Observable<PaginatedResponse<T>> {
    const params = new HttpParams().set("page", String(page));

    return this.http
      .get<
        PaginatedResponse<T>
      >(`${this.baseUrl}/${filterId}/apply`, { params })
      .pipe(catchError(this.handleError));
  }

  // ===========================================================================
  // ERROR HANDLING
  // ===========================================================================

  private handleError = (error: HttpErrorResponse): Observable<never> => {
    let errorMessage: string;

    if (error.error instanceof ErrorEvent) {
      errorMessage = `Client Error: ${error.error.message}`;
    } else {
      errorMessage =
        error.error?.detail ||
        error.error?.message ||
        `Server Error: ${error.message}`;
    }

    console.error("SavedFilter Service Error:", {
      status: error.status,
      message: errorMessage,
    });

    return throwError(() => new Error(errorMessage));
  };
}
