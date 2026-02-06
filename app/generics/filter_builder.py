from typing import Dict, Any, List, Type
from sqlalchemy.orm import Query
from app.enums.filter_operation import FilterOperation
from app.schema.filtering import FilterParam


class QueryFilterBuilder:
    FILTER_OPERATIONS = {
        FilterOperation.EQUALS: lambda col, val: col == val,
        FilterOperation.NOT_EQUALS: lambda col, val: col != val,
        FilterOperation.GREATER_THAN: lambda col, val: col > val,
        FilterOperation.GREATER_EQUAL: lambda col, val: col >= val,
        FilterOperation.LESS_THAN: lambda col, val: col < val,
        FilterOperation.LESS_EQUAL: lambda col, val: col <= val,
        FilterOperation.LIKE: lambda col, val: col.like(f"%{val}%"),
        FilterOperation.ILIKE: lambda col, val: col.ilike(f"%{val}%"),
        FilterOperation.IN: lambda col, val: col.in_(val),
        FilterOperation.NOT_IN: lambda col, val: ~col.in_(val),
        FilterOperation.IS_NULL: lambda col, val: col.is_(None) if val else col.isnot(None),
        FilterOperation.IS_NOT_NULL: lambda col, val: col.isnot(None) if val else col.is_(None),
        FilterOperation.BETWEEN: lambda col, val: col.between(val[0], val[1]),
        FilterOperation.STARTS_WITH: lambda col, val: col.like(f"{val}%"),
        FilterOperation.ENDS_WITH: lambda col, val: col.like(f"%{val}"),
    }
    
    def __init__(self, query: Query, model: Type[Any]):
        self.query = query
        self.model = model
    
    def apply_filter(
        self,
        field: str,
        operation: FilterOperation,
        value: Any
    ) -> 'QueryFilterBuilder':
        if '.' in field:
            parts = field.split('.', 1)
            relationship_name = parts[0]
            related_field = parts[1]
            
            if not hasattr(self.model, relationship_name):
                raise ValueError(
                    f"Model '{self.model.__name__}' has no relationship '{relationship_name}'."
                )

            relationship_attr = getattr(self.model, relationship_name)
            
            if not hasattr(relationship_attr, 'property'):
                raise ValueError(
                    f"Attribute '{relationship_name}' on model '{self.model.__name__}' is not a relationship"
                )
            
            related_model = relationship_attr.property.mapper.class_
            
            if not hasattr(related_model, related_field):
                raise ValueError(
                    f"Related model '{related_model.__name__}' has no field '{related_field}'."
                )
            
            column = getattr(related_model, related_field)
            self.query = self.query.join(relationship_attr)
        else:
            if not hasattr(self.model, field):
                raise ValueError(
                    f"Model '{self.model.__name__}' has no field '{field}'."
                )
            column = getattr(self.model, field)
        
        filter_func = self.FILTER_OPERATIONS.get(operation)
        
        if filter_func is None:
            raise ValueError(f"Unsupported filter operation: {operation}")
        
        try:
            filter_condition = filter_func(column, value)
            self.query = self.query.filter(filter_condition)
        except Exception as e:
            raise ValueError(
                f"Failed to apply filter on field '{field}' with operation '{operation}': {str(e)}"
            )
        
        return self
    
    def apply_filters_from_dict(self, filters: Dict[str, Any]) -> 'QueryFilterBuilder':
        for field, filter_value in filters.items():
            if isinstance(filter_value, dict) and "operation" in filter_value:
                operation = FilterOperation(filter_value["operation"])
                value = filter_value["value"]
                self.apply_filter(field, operation, value)
            else:
                self.apply_filter(field, FilterOperation.EQUALS, filter_value)
        return self
    
    def apply_filters_from_list(self, filter_list: List[Dict[str, Any]]) -> 'QueryFilterBuilder':
        for filter_dict in filter_list:
            field = filter_dict.get("field")
            operation_str = filter_dict.get("operation")
            value = filter_dict.get("value")
            
            if not field or not operation_str:
                raise ValueError(
                    f"Invalid filter dict: {filter_dict}. Must have 'field' and 'operation'."
                )
            
            operation = FilterOperation(operation_str)
            self.apply_filter(field, operation, value)
        return self
    
    def apply_filters_from_params(self, filter_params: List[FilterParam]) -> 'QueryFilterBuilder':
        for param in filter_params:
            self.apply_filter(param.field, param.operation, param.value)
        return self
    
    def get_query(self) -> Query:
        return self.query
