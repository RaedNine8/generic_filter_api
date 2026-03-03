import { FilterOperation } from "../enums/filter-operation.enum";

/**
 * Recursive tree node for boolean filter expressions.
 *
 * Mirrors the backend FilterNode schema exactly.
 *
 * Two node types:
 *   - 'operator': internal node with AND/OR and a list of children
 *   - 'condition': leaf node with field + operation + value
 *
 * Example tree: (price > 20 AND rating >= 4) OR (genre = Fantasy)
 * ```
 * {
 *   nodeType: 'operator', operator: 'OR', children: [
 *     { nodeType: 'operator', operator: 'AND', children: [
 *       { nodeType: 'condition', field: 'price', operation: 'gt', value: 20 },
 *       { nodeType: 'condition', field: 'rating', operation: 'gte', value: 4 }
 *     ]},
 *     { nodeType: 'condition', field: 'genre', operation: 'eq', value: 'Fantasy' }
 *   ]
 * }
 * ```
 */
export interface FilterTreeNode {
  /** Unique ID for UI tracking (not sent to backend). */
  id: string;

  /** 'operator' = AND/OR group, 'condition' = filter leaf. */
  nodeType: "operator" | "condition";

  // ── Operator node fields ──────────────────────────
  operator?: "AND" | "OR";
  children?: FilterTreeNode[];

  // ── Condition (leaf) node fields ──────────────────
  field?: string;
  operation?: FilterOperation;
  value?: any;

  // ── UI-only state ─────────────────────────────────
  expanded?: boolean;
}

// ────────────────────────────────────────────────────────────────
// Helpers
// ────────────────────────────────────────────────────────────────

let _nextId = 1;
export function generateNodeId(): string {
  return `node-${_nextId++}`;
}

/** Create a new empty condition leaf. */
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

/** Create a new operator group with default children. */
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

/**
 * Strip UI-only fields (id, expanded) to produce a clean payload
 * matching the backend FilterNode schema.
 */
export function toBackendPayload(node: FilterTreeNode): any {
  if (node.nodeType === "condition") {
    return {
      node_type: "condition",
      field: node.field,
      operation: node.operation,
      value: node.value,
    };
  }
  return {
    node_type: "operator",
    operator: node.operator,
    children: (node.children || []).map(toBackendPayload),
  };
}
