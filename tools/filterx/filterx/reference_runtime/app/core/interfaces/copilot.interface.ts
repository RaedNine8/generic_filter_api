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

export interface CopilotExecuteResponse {
  entity: string;
  filter_tree: Record<string, unknown>;
  summary: string;
  explanation: string;
}

export interface CopilotPreview {
  filterTree: FilterTreeNode;
  explanation: string;
  confirmationToken: string;
}
