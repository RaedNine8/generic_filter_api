from __future__ import annotations

import json

_ENTITIES_JSON = '''[
  {
    "model": "Author",
    "table": "authors",
    "primary_keys": [
      "id"
    ],
    "fields": [
      {
        "name": "id",
        "type": "integer",
        "ops": [
          "eq",
          "ne",
          "gt",
          "gte",
          "lt",
          "lte",
          "in",
          "not_in",
          "between",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "name",
        "type": "string",
        "ops": [
          "eq",
          "ne",
          "like",
          "ilike",
          "starts_with",
          "ends_with",
          "in",
          "not_in",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "email",
        "type": "string",
        "ops": [
          "eq",
          "ne",
          "like",
          "ilike",
          "starts_with",
          "ends_with",
          "in",
          "not_in",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "country",
        "type": "string",
        "ops": [
          "eq",
          "ne",
          "like",
          "ilike",
          "starts_with",
          "ends_with",
          "in",
          "not_in",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "is_active",
        "type": "boolean",
        "ops": [
          "eq",
          "ne",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "birth_year",
        "type": "integer",
        "ops": [
          "eq",
          "ne",
          "gt",
          "gte",
          "lt",
          "lte",
          "in",
          "not_in",
          "between",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "created_at",
        "type": "datetime",
        "ops": [
          "eq",
          "ne",
          "gt",
          "gte",
          "lt",
          "lte",
          "between",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "updated_at",
        "type": "datetime",
        "ops": [
          "eq",
          "ne",
          "gt",
          "gte",
          "lt",
          "lte",
          "between",
          "is_null",
          "is_not_null"
        ]
      }
    ],
    "relationships": [
      {
        "name": "books",
        "related_model": "Book",
        "cardinality": "o2m"
      }
    ]
  },
  {
    "model": "Book",
    "table": "books",
    "primary_keys": [
      "id"
    ],
    "fields": [
      {
        "name": "id",
        "type": "integer",
        "ops": [
          "eq",
          "ne",
          "gt",
          "gte",
          "lt",
          "lte",
          "in",
          "not_in",
          "between",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "title",
        "type": "string",
        "ops": [
          "eq",
          "ne",
          "like",
          "ilike",
          "starts_with",
          "ends_with",
          "in",
          "not_in",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "isbn",
        "type": "string",
        "ops": [
          "eq",
          "ne",
          "like",
          "ilike",
          "starts_with",
          "ends_with",
          "in",
          "not_in",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "genre",
        "type": "string",
        "ops": [
          "eq",
          "ne",
          "like",
          "ilike",
          "starts_with",
          "ends_with",
          "in",
          "not_in",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "description",
        "type": "text",
        "ops": [
          "eq",
          "ne",
          "like",
          "ilike",
          "starts_with",
          "ends_with",
          "in",
          "not_in",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "price",
        "type": "float",
        "ops": [
          "eq",
          "ne",
          "gt",
          "gte",
          "lt",
          "lte",
          "in",
          "not_in",
          "between",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "pages",
        "type": "integer",
        "ops": [
          "eq",
          "ne",
          "gt",
          "gte",
          "lt",
          "lte",
          "in",
          "not_in",
          "between",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "published_year",
        "type": "integer",
        "ops": [
          "eq",
          "ne",
          "gt",
          "gte",
          "lt",
          "lte",
          "in",
          "not_in",
          "between",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "is_available",
        "type": "boolean",
        "ops": [
          "eq",
          "ne",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "rating",
        "type": "float",
        "ops": [
          "eq",
          "ne",
          "gt",
          "gte",
          "lt",
          "lte",
          "in",
          "not_in",
          "between",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "created_at",
        "type": "datetime",
        "ops": [
          "eq",
          "ne",
          "gt",
          "gte",
          "lt",
          "lte",
          "between",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "updated_at",
        "type": "datetime",
        "ops": [
          "eq",
          "ne",
          "gt",
          "gte",
          "lt",
          "lte",
          "between",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "author_id",
        "type": "integer",
        "ops": [
          "eq",
          "ne",
          "gt",
          "gte",
          "lt",
          "lte",
          "in",
          "not_in",
          "between",
          "is_null",
          "is_not_null"
        ]
      }
    ],
    "relationships": [
      {
        "name": "author",
        "related_model": "Author",
        "cardinality": "m2o"
      }
    ]
  },
  {
    "model": "SavedFilter",
    "table": "saved_filters",
    "primary_keys": [
      "id"
    ],
    "fields": [
      {
        "name": "id",
        "type": "integer",
        "ops": [
          "eq",
          "ne",
          "gt",
          "gte",
          "lt",
          "lte",
          "in",
          "not_in",
          "between",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "name",
        "type": "string",
        "ops": [
          "eq",
          "ne",
          "like",
          "ilike",
          "starts_with",
          "ends_with",
          "in",
          "not_in",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "description",
        "type": "text",
        "ops": [
          "eq",
          "ne",
          "like",
          "ilike",
          "starts_with",
          "ends_with",
          "in",
          "not_in",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "model_name",
        "type": "string",
        "ops": [
          "eq",
          "ne",
          "like",
          "ilike",
          "starts_with",
          "ends_with",
          "in",
          "not_in",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "filters",
        "type": "json",
        "ops": [
          "is_null",
          "is_not_null",
          "eq",
          "ne"
        ]
      },
      {
        "name": "filter_tree",
        "type": "json",
        "ops": [
          "is_null",
          "is_not_null",
          "eq",
          "ne"
        ]
      },
      {
        "name": "sort_by",
        "type": "string",
        "ops": [
          "eq",
          "ne",
          "like",
          "ilike",
          "starts_with",
          "ends_with",
          "in",
          "not_in",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "sort_order",
        "type": "string",
        "ops": [
          "eq",
          "ne",
          "like",
          "ilike",
          "starts_with",
          "ends_with",
          "in",
          "not_in",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "page_size",
        "type": "integer",
        "ops": [
          "eq",
          "ne",
          "gt",
          "gte",
          "lt",
          "lte",
          "in",
          "not_in",
          "between",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "search_query",
        "type": "string",
        "ops": [
          "eq",
          "ne",
          "like",
          "ilike",
          "starts_with",
          "ends_with",
          "in",
          "not_in",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "created_at",
        "type": "datetime",
        "ops": [
          "eq",
          "ne",
          "gt",
          "gte",
          "lt",
          "lte",
          "between",
          "is_null",
          "is_not_null"
        ]
      },
      {
        "name": "updated_at",
        "type": "datetime",
        "ops": [
          "eq",
          "ne",
          "gt",
          "gte",
          "lt",
          "lte",
          "between",
          "is_null",
          "is_not_null"
        ]
      }
    ],
    "relationships": []
  }
]'''
ENTITIES = json.loads(_ENTITIES_JSON)
