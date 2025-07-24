"""
FastAPI application with strongly typed endpoints.

This is the main application entry point providing a comprehensive,
type-safe API for crypto portfolio analysis with C#-like architecture.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.v1.api import api_router
from .core.config import get_settings
from .core.exceptions import APIException
from .models.common import ErrorResponse, HealthCheckResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Application startup time for health checks
startup_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events similar to C# hosted services.
    """
    # Startup
    logger.info("🚀 Starting Crypto Portfolio API...")
    settings = get_settings()
    logger.info(f"📊 API Version: {settings.api_version}")
    logger.info(f"🔧 Debug Mode: {settings.debug}")
    logger.info(f"🌐 CORS Origins: {settings.cors_origins}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Crypto Portfolio API...")


# Create FastAPI application with strong typing
def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    settings = get_settings()
    
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    
    # Add request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # Include API routes
    app.include_router(api_router, prefix="/api/v1")
    
    return app


# Create application instance
app = create_application()


# Global exception handler for API exceptions
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """
    Handle custom API exceptions with proper error responses.
    
    Args:
        request: FastAPI request
        exc: API exception
        
    Returns:
        JSONResponse: Structured error response
    """
    error_response = ErrorResponse(
        error_code=exc.error_code,
        error_message=exc.message,
        details=exc.details
    )
    
    logger.error(f"API Exception: {exc.error_code} - {exc.message}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )


# Global exception handler for unhandled exceptions
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions with generic error response.
    
    Args:
        request: FastAPI request
        exc: Unhandled exception
        
    Returns:
        JSONResponse: Generic error response
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    error_response = ErrorResponse(
        error_code="INTERNAL_SERVER_ERROR",
        error_message="An unexpected error occurred",
        details={"exception_type": type(exc).__name__}
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.dict()
    )


# Health check endpoint
@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check() -> HealthCheckResponse:
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        HealthCheckResponse: Service health status
    """
    settings = get_settings()
    uptime = time.time() - startup_time
    
    # Check dependencies (simplified for now)
    dependencies = {
        "bitvavo_api": "healthy" if settings.bitvavo_api_key else "unhealthy",
        "openai_api": "healthy" if settings.openai_api_key else "not_configured",
        "anthropic_api": "healthy" if settings.anthropic_api_key else "not_configured",
    }
    
    return HealthCheckResponse(
        status="healthy",
        version=settings.api_version,
        uptime_seconds=uptime,
        dependencies=dependencies
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> Dict[str, str]:
    """
    Root endpoint with API information.
    
    Returns:
        Dict[str, str]: Basic API information
    """
    settings = get_settings()
    return {
        "message": "Crypto Portfolio API",
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )
