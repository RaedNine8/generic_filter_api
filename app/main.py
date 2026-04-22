import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.books import router as books_router


def _load_allowed_origins() -> list[str]:
    origins_raw = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:4200,http://127.0.0.1:4200")
    origins = [origin.strip() for origin in origins_raw.split(",") if origin.strip()]
    return origins or ["http://localhost:4200", "http://127.0.0.1:4200"]

app = FastAPI(
    title="Filter Test API",
    description="A test API to demonstrate generic filtering, sorting, pagination, and search functionality",
    version="1.0.0"
)

allowed_origins = _load_allowed_origins()
allow_credentials = os.getenv("CORS_ALLOW_CREDENTIALS", "false").lower() == "true"

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(books_router)
# FILTERX:ROUTER_MOUNT
from app.filterx_generated.router import router as filterx_generated_router
app.include_router(filterx_generated_router)


@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "Filter Test API is running"}
