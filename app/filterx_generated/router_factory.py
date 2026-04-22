from __future__ import annotations

from fastapi import APIRouter

from .metadata import build_metadata


def create_router(api_prefix: str = "/api") -> APIRouter:
    prefix = api_prefix.strip() or "/api"
    if not prefix.startswith("/"):
        prefix = f"/{prefix}"
    if prefix != "/":
        prefix = prefix.rstrip("/")
    else:
        prefix = ""

    router = APIRouter(prefix=f"{prefix}/filterx", tags=["filterx"])

    @router.get("/metadata")
    def get_metadata() -> dict[str, object]:
        return build_metadata()

    return router
