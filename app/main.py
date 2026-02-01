"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from app.config import settings
from app.database import init_db, close_db
from app.core.exceptions import TaskAssistantException
from app.core.docs import custom_openapi, tags_metadata
from app.api.v1 import api_v1_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting up Task Assistant API")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down Task Assistant API")
    await close_db()


# Create FastAPI app
app = FastAPI(
    title="Task Assistant AI SaaS API",
    description="Production-grade, multi-tenant AI SaaS platform with advanced orchestration",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware
allowed_origins = settings.get_allowed_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Exception handlers
@app.exception_handler(TaskAssistantException)
async def task_assistant_exception_handler(request, exc: TaskAssistantException):
    """Handle custom task assistant exceptions."""
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors(),
            },
        },
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Task Assistant AI",
    }


# Include API v1 router
app.include_router(api_v1_router, prefix="/api/v1")

# Custom OpenAPI schema
app.openapi = lambda: custom_openapi(app)

# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# Root endpoint - Serve UI
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - Serve the UI."""
    static_dir = Path(__file__).parent / "static"
    html_file = static_dir / "index.html"
    
    if html_file.exists():
        return FileResponse(str(html_file), media_type="text/html")
    
    return {
        "service": "Task Assistant AI SaaS API",
        "version": "1.0.0",
        "documentation": "/docs",
        "api_version": "v1",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.getenv("PORT", settings.port))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.debug,
    )
