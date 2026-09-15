import { inject, Injectable } from "@angular/core";
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
import { FILTERX_CONFIG, joinFilterxUrl } from "../config/filterx-config";

@Injectable({
  providedIn: "root",
})
export class SavedFilterService {
  private readonly config = inject(FILTERX_CONFIG);
  private get baseUrl(): string {
    return joinFilterxUrl(
      this.config.apiBaseUrl,
      `${this.config.apiPrefix}/saved-filters`,
    );
  }

  constructor(private http: HttpClient) {}

  createFilter(filter: SavedFilterCreate): Observable<SavedFilter> {
    this.requireFeature();
    return this.http
      .post<SavedFilter>(this.baseUrl, filter)
      .pipe(catchError(this.handleError));
  }

  getFilters(modelName?: string): Observable<SavedFilter[]> {
    this.requireFeature();
    let params = new HttpParams();
    if (modelName) {
      params = params.set("model_name", modelName);
    }

    return this.http
      .get<SavedFilter[]>(this.baseUrl, { params })
      .pipe(catchError(this.handleError));
  }

  getFilterById(filterId: number): Observable<SavedFilter> {
    this.requireFeature();
    return this.http
      .get<SavedFilter>(`${this.baseUrl}/${filterId}`)
      .pipe(catchError(this.handleError));
  }

  updateFilter(
    filterId: number,
    update: SavedFilterUpdate,
  ): Observable<SavedFilter> {
    this.requireFeature();
    return this.http
      .put<SavedFilter>(`${this.baseUrl}/${filterId}`, update)
      .pipe(catchError(this.handleError));
  }

  deleteFilter(filterId: number): Observable<void> {
    this.requireFeature();
    return this.http
      .delete<void>(`${this.baseUrl}/${filterId}`)
      .pipe(catchError(this.handleError));
  }

  applyFilter<T = any>(
    filterId: number,
    page = 1,
  ): Observable<PaginatedResponse<T>> {
    this.requireFeature();
    const params = new HttpParams().set("page", String(page));

    return this.http
      .get<
        PaginatedResponse<T>
      >(`${this.baseUrl}/${filterId}/apply`, { params })
      .pipe(catchError(this.handleError));
  }

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

  private requireFeature(): void {
    if (!this.config.savedFiltersEnabled) {
      throw new Error(
        "Saved filters are disabled in the FilterX frontend configuration.",
      );
    }
  }
}
