"""
Main Application Module
FastAPI application entry point with route configuration.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

from app.core.config import settings
from app.db.database import DatabaseManager
from app.api.routes import organization_router, admin_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting up application...")
    await DatabaseManager.connect()
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await DatabaseManager.disconnect()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
## Organization Management Service API

A multi-tenant backend service for managing organizations with dynamic MongoDB collections.

### Features:
- **Organization Management**: Create, read, update, and delete organizations
- **Dynamic Collections**: Each organization gets its own MongoDB collection
- **JWT Authentication**: Secure admin authentication with JWT tokens
- **Multi-tenant Architecture**: Master database for metadata, separate collections for each org

### Authentication:
Most endpoints require JWT authentication. To authenticate:
1. Create an organization using `POST /org/create`
2. Login using `POST /admin/login` to receive a JWT token
3. Include the token in the `Authorization` header: `Bearer <token>`
    """,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors with detailed messages.
    """
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation Error",
            "message": "Request validation failed",
            "details": {"errors": errors}
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "details": {"error": str(exc)} if settings.debug else None
        }
    )


# Include routers
app.include_router(organization_router)
app.include_router(admin_router)


# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    """
    Root endpoint - health check.
    """
    return {
        "success": True,
        "message": "Organization Management Service is running",
        "version": settings.app_version,
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
    }
