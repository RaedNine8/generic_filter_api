from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routers.books import router as books_router

app = FastAPI(
    title="Filter Test API",
    description="A test API to demonstrate generic filtering, sorting, pagination, and search functionality",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(books_router)


@app.get("/")
def read_root():
    return FileResponse("static/index.html")


@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "Filter Test API is running"}
