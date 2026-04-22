import { FilterOperation } from "../enums/filter-operation.enum";

export interface FilterTreeNode {
  id: string;

  nodeType: "operator" | "condition";

  operator?: "AND" | "OR";
  children?: FilterTreeNode[];

  field?: string;
  operation?: FilterOperation;
  value?: any;

  expanded?: boolean;
}


let _nextId = 1;
export function generateNodeId(): string {
  return `node-${_nextId++}`;
}

export function createConditionNode(
  field: string = "",
  operation: FilterOperation = FilterOperation.EQUALS,
  value: any = "",
): FilterTreeNode {
  return {
    id: generateNodeId(),
    nodeType: "condition",
    field,
    operation,
    value,
  };
}

export function createOperatorNode(
  operator: "AND" | "OR" = "AND",
  children: FilterTreeNode[] = [],
): FilterTreeNode {
  if (children.length === 0) {
    children = [createConditionNode(), createConditionNode()];
  }
  return {
    id: generateNodeId(),
    nodeType: "operator",
    operator,
    children,
    expanded: true,
  };
}

export function toBackendPayload(node: FilterTreeNode): any | null {
  if (node.nodeType === "condition") {
    const op = node.operation?.toLowerCase();
    const isNullOp = op === "is_null" || op === "is_not_null";

    if (!isNullOp) {
      if (node.value === null || node.value === undefined || node.value === "") {
        return null;
      }
      if (Array.isArray(node.value) && node.value.length === 0) {
        return null;
      }
    }

    return {
      node_type: "condition",
      field: node.field,
      operation: node.operation,
      value: node.value,
    };
  }

  const children = (node.children || [])
    .map(toBackendPayload)
    .filter((c: any) => c !== null);

  if (children.length === 0) {
    return null;
  }

  return {
    node_type: "operator",
    operator: node.operator,
    children,
  };
}
