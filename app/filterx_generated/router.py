from __future__ import annotations

from .router_factory import create_router

API_PREFIX = "/api"
router = create_router(api_prefix=API_PREFIX)
