"""
TokenDance Backend - FastAPI Application Entry Point
"""
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import REGISTRY, Counter, Histogram, generate_latest
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


class APILoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log full request and response details for debugging."""

    async def dispatch(self, request: Request, call_next):
        import json
        import time

        request_id = request.headers.get("X-Request-ID", "unknown")
        start_time = time.time()

        # Read and log request body
        request_body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body_bytes = await request.body()
                if body_bytes:
                    try:
                        request_body = json.loads(body_bytes.decode("utf-8"))
                    except json.JSONDecodeError:
                        request_body = body_bytes.decode("utf-8", errors="replace")
            except Exception as e:
                request_body = f"<error reading body: {e}>"

        # Log request
        logger.info(
            "api_request",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            path=request.url.path,
            query_params=dict(request.query_params),
            headers={k: v for k, v in request.headers.items() if k.lower() not in ["authorization", "cookie"]},
            body=request_body,
            client_host=request.client.host if request.client else None,
        )

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Read response body for logging (need to create new response)
        response_body = None
        if response.status_code != 204:  # No content
            try:
                response_body_bytes = b""
                async for chunk in response.body_iterator:
                    response_body_bytes += chunk

                if response_body_bytes:
                    content_type = response.headers.get("content-type", "")
                    if "application/json" in content_type:
                        try:
                            response_body = json.loads(response_body_bytes.decode("utf-8"))
                        except json.JSONDecodeError:
                            response_body = response_body_bytes.decode("utf-8", errors="replace")
                    elif "text/" in content_type:
                        response_body = response_body_bytes.decode("utf-8", errors="replace")[:1000]  # Truncate text
                    else:
                        response_body = f"<binary data, {len(response_body_bytes)} bytes>"

                # Create new response with the same body
                from starlette.responses import Response as StarletteResponse
                response = StarletteResponse(
                    content=response_body_bytes,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )
            except Exception as e:
                logger.warning("response_body_read_error", error=str(e))

        # Log response
        logger.info(
            "api_response",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            response_headers=dict(response.headers.items()),
            body=response_body,
        )

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

    # Import all models to ensure ORM relationships are resolved
    import app.models  # noqa: F401

    # Initialize database connection pool
    from app.core.database import close_db, init_db
    await init_db()
    logger.info("database_connection_pool_initialized")

    # Initialize Redis connection pool
    from app.core.redis import close_redis, init_redis
    await init_redis()
    logger.info("redis_connection_pool_initialized")

    yield

    # Shutdown
    logger.info("application_shutdown")

    # Close Redis connections
    await close_redis()

    # Close database connections
    await close_db()


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

    # Custom middlewares (order matters - first added = outermost)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(APILoggingMiddleware)  # Log all API requests/responses
    app.add_middleware(MetricsMiddleware)

    # Health check endpoints
    @app.get("/health")
    async def health_check():
        """Basic health check."""
        return {"status": "healthy", "version": settings.VERSION}

    @app.get("/readiness")
    async def readiness_check():
        """Readiness check - verifies dependencies."""
        from app.core.database import check_db_health
        from app.core.redis import check_redis_health

        db_ok = await check_db_health()
        redis_ok = await check_redis_health()

        all_ok = db_ok and redis_ok

        return {
            "status": "ready" if all_ok else "degraded",
            "checks": {
                "database": "ok" if db_ok else "failed",
                "redis": "ok" if redis_ok else "failed",
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
