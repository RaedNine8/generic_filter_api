import { Injectable, inject } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { Observable, map } from "rxjs";

import {
  CopilotExecuteResponse,
  CopilotPreview,
  CopilotPreviewResponse,
  CopilotQueryRequest,
} from "../interfaces/copilot.interface";
import {
  FilterTreeNode,
  generateNodeId,
} from "../interfaces/filter-tree.interface";
import { FilterOperation } from "../enums/filter-operation.enum";
import { FILTERX_CONFIG, joinFilterxUrl } from "../config/filterx-config";

@Injectable({ providedIn: "root" })
export class CopilotService {
  private readonly config = inject(FILTERX_CONFIG);

  private get baseUrl(): string {
    return joinFilterxUrl(
      this.config.apiBaseUrl,
      `${this.config.apiPrefix}/filterx/copilot`,
    );
  }

  constructor(private http: HttpClient) {}

  preview(request: CopilotQueryRequest): Observable<CopilotPreview> {
    return this.http
      .post<CopilotPreviewResponse>(`${this.baseUrl}/query`, request)
      .pipe(
        map((response) => ({
          filterTree: this.fromBackendTree(response.filter_tree),
          explanation: response.explanation,
          confirmationToken: response.confirmation_token,
        })),
      );
  }

  execute(
    confirmationToken: string,
  ): Observable<CopilotExecuteResponse> {
    return this.http.post<CopilotExecuteResponse>(
      `${this.baseUrl}/execute`,
      {
        confirmation_token: confirmationToken,
      },
    );
  }

  fromBackendTree(node: Record<string, unknown>): FilterTreeNode {
    const nodeType =
      node["node_type"] === "operator" ? "operator" : "condition";
    if (nodeType === "operator") {
      return {
        id: generateNodeId(),
        nodeType,
        operator: node["operator"] === "OR" ? "OR" : "AND",
        children: Array.isArray(node["children"])
          ? node["children"].map((child) =>
              this.fromBackendTree(child as Record<string, unknown>),
            )
          : [],
        expanded: true,
      };
    }

    return {
      id: generateNodeId(),
      nodeType,
      field: String(node["field"] || ""),
      operation: String(
        node["operation"] || FilterOperation.EQUALS,
      ) as FilterOperation,
      value: node["value"],
    };
  }
}
