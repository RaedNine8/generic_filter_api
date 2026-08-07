import { Injectable } from "@angular/core";
import { TestBed } from "@angular/core/testing";
import {
  HttpTestingController,
  provideHttpClientTesting,
} from "@angular/common/http/testing";
import { provideHttpClient } from "@angular/common/http";

import { FilterOperation } from "../enums/filter-operation.enum";
import { SortOrder } from "../enums/sort-order.enum";
import { QueryState } from "../interfaces/query-state.interface";
import { GenericQueryService } from "./generic-query.service";

@Injectable()
class TestQueryService extends GenericQueryService<Record<string, unknown>> {
  protected baseUrl = "/api/books";
}

describe("GenericQueryService exports", () => {
  let service: TestQueryService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        TestQueryService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(TestQueryService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it("exports the active tree, search, and sort without pagination", () => {
    const state: QueryState = {
      filterTree: {
        id: "price-filter",
        nodeType: "condition",
        field: "price",
        operation: FilterOperation.GREATER_EQUAL,
        value: 10,
      },
      filters: [],
      pagination: { page: 3, size: 20 },
      sort: { sort_by: "title", order: SortOrder.DESC },
      search: "filtering",
    };

    service.exportWithState(state, "xlsx").subscribe();

    const request = http.expectOne(
      (candidate) => candidate.url === "/api/books/export",
    );
    expect(request.request.method).toBe("POST");
    expect(request.request.responseType).toBe("blob");
    expect(request.request.params.get("format")).toBe("xlsx");
    expect(request.request.params.get("sort_by")).toBe("title");
    expect(request.request.params.get("order")).toBe("desc");
    expect(request.request.params.get("search")).toBe("filtering");
    expect(request.request.params.has("page")).toBeFalse();
    expect(request.request.params.has("size")).toBeFalse();
    expect(request.request.body).toEqual({
      filter_tree: {
        node_type: "condition",
        field: "price",
        operation: "gte",
        value: 10,
      },
    });
    request.flush(new Blob(["xlsx"]));
  });
});
