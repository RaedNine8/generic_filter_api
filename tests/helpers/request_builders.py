def condition_node(field: str, operation: str, value):
    return {
        "node_type": "condition",
        "field": field,
        "operation": operation,
        "value": value,
    }


def and_tree(*conditions):
    return {
        "node_type": "operator",
        "operator": "AND",
        "children": list(conditions),
    }
