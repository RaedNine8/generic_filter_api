import { FilterTreeNode } from "./filter-tree.interface";

export interface CopilotQueryRequest {
  entity: string;
  prompt: string;
}

export interface CopilotPreviewResponse {
  filter_tree: Record<string, unknown>;
  explanation: string;
  confirmation_token: string;
}

export interface CopilotExecuteResponse<T = Record<string, unknown>> {
  data: T[];
  meta: {
    page: number;
    size: number;
    total_items: number;
  };
  summary: string;
  explanation: string;
}

export interface CopilotPreview {
  filterTree: FilterTreeNode;
  explanation: string;
  confirmationToken: string;
}
