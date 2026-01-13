"""
TokenDance Backend - FastAPI Application Entry Point
"""
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CollectorRegistry, REGISTRY
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import get_logger, set_request_id

logger = get_logger(__name__)

# Prometheus metrics - use try/except to handle reload mode
try:
    REQUEST_COUNT = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status"],
    )
    REQUEST_DURATION = Histogram(
        "http_request_duration_seconds",
        "HTTP request duration in seconds",
        ["method", "endpoint"],
    )
except ValueError:
    # Metrics already registered (reload mode)
    REQUEST_COUNT = REGISTRY._names_to_collectors.get("http_requests_total")
    REQUEST_DURATION = REGISTRY._names_to_collectors.get("http_request_duration_seconds")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to all requests."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        set_request_id(request_id)
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics."""

    async def dispatch(self, request: Request, call_next):
        if not settings.ENABLE_METRICS:
            return await call_next(request)
        
        # Start timer
        with REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path,
        ).time():
            response = await call_next(request)
        
        # Record request count
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
        ).inc()
        
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    logger.info(
        "application_startup",
        environment=settings.ENVIRONMENT,
        version=settings.VERSION,
    )
    
    # TODO: Initialize database connection pool
    # TODO: Initialize Redis connection pool
    
    yield
    
    # Shutdown
    logger.info("application_shutdown")
    # TODO: Close database connections
    # TODO: Close Redis connections


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        redoc_url=f"{settings.API_V1_PREFIX}/redoc",
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Custom middlewares
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(MetricsMiddleware)
    
    # Health check endpoints
    @app.get("/health")
    async def health_check():
        """Basic health check."""
        return {"status": "healthy", "version": settings.VERSION}
    
    @app.get("/readiness")
    async def readiness_check():
        """Readiness check - verifies dependencies."""
        # TODO: Check database connection
        # TODO: Check Redis connection
        return {
            "status": "ready",
            "checks": {
                "database": "ok",  # placeholder
                "redis": "ok",     # placeholder
            },
        }
    
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint."""
        if not settings.ENABLE_METRICS:
            return Response(status_code=404)
        return Response(content=generate_latest(), media_type="text/plain")
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception(
            "unhandled_exception",
            path=request.url.path,
            method=request.method,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred",
                "request_id": request.headers.get("X-Request-ID"),
            },
        )
    
    # Include API routers
    from app.api.v1.api import api_router
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    
    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_config=None,  # Use structlog instead
    )
