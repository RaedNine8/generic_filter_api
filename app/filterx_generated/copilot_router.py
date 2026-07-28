from __future__ import annotations

import importlib
from pathlib import Path

from app.filterx_generated.entities import ENTITIES
from app.generics.query_executor import GenericQueryExecutor
from app.schema.filter_node import FilterNode
from app.schema.pagination import GenericPaginationParams
from filterx.agent import create_copilot_router

API_PREFIX = "/api"
SCAN_FILE = Path(".filterx/scan.json")
SESSION_DEPENDENCY_IMPORT = "app.database:get_db"
AGENT_CONFIG = {'enabled': False,
 'generated_file': 'app/filterx_generated/copilot_router.py',
 'mount_anchor': '# FILTERX:COPILOT_MOUNT',
 'mount_file': 'app/main.py',
 'providers': [{'api_key_env': 'GROQ_API_KEY',
                'model': 'llama-3.3-70b-versatile',
                'name': 'groq',
                'roles': ['compile', 'retry', 'summarize']},
               {'api_key_env': 'GEMINI_API_KEY',
                'model': 'gemini-2.5-flash',
                'name': 'gemini',
                'roles': ['fallback']}],
 'safety': {'circuit_breaker_failure_threshold': 5,
            'circuit_breaker_reset_seconds': 60,
            'max_provider_retries': 3,
            'max_validation_retries': 3,
            'require_human_preview': True},
 'vector_store': {'backend': 'chroma',
                  'embedding_model': 'all-MiniLM-L6-v2',
                  'enabled': False,
                  'path': '.filterx/vector_store'}}

def _import_object(import_path: str) -> object:
    module_name, obj_name = import_path.split(":", 1)
    module = importlib.import_module(module_name)
    return getattr(module, obj_name)

router = create_copilot_router(
    api_prefix=API_PREFIX,
    entities=ENTITIES,
    scan_file=SCAN_FILE,
    agent_config=AGENT_CONFIG,
    session_dependency=_import_object(SESSION_DEPENDENCY_IMPORT),
    query_executor_cls=GenericQueryExecutor,
    pagination_cls=GenericPaginationParams,
    filter_node_cls=FilterNode,
)
