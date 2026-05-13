import { Injectable } from "@angular/core";
import { HttpClient } from "@angular/common/http";

import { GenericQueryService } from "./generic-query.service";

@Injectable()
export class EntityQueryService<T> extends GenericQueryService<T> {
  protected baseUrl = "";

  constructor(http: HttpClient) {
    super(http);
  }

  setBaseUrl(baseUrl: string): void {
    this.baseUrl = baseUrl;
  }
}
