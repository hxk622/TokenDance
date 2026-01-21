"""
TokenDance Backend - FastAPI Application Entry Point
"""
import os
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC

# Fix SSL certificate issue on macOS
try:
    import certifi
    cert_path = certifi.where()
    os.environ.setdefault("SSL_CERT_FILE", cert_path)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", cert_path)
    # For httpx/httpcore
    os.environ.setdefault("CURL_CA_BUNDLE", cert_path)
except ImportError:
    pass

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

    def _log_json(self, data: dict, level: str = "info") -> None:
        """Print formatted JSON log to stdout."""
        import json
        import sys
        from datetime import datetime

        # Add timestamp and level
        log_entry = {
            "request_id": data.pop("request_id", None),
            "timestamp": datetime.now(UTC).isoformat(),
            "level": level,
            **data,
        }
        # Ensure body is always last by removing and re-adding
        body = log_entry.pop("body", None)
        if body is not None:
            log_entry["body"] = body

        print(json.dumps(log_entry, ensure_ascii=False, indent=2), file=sys.stdout, flush=True)

    async def dispatch(self, request: Request, call_next):
        import json
        import time

        from app.core.logging import get_request_id

        # Get request_id from context (set by RequestIDMiddleware) or fallback
        request_id = get_request_id() or request.headers.get("X-Request-ID", "unknown")
        start_time = time.time()

        # Read request body
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
                request_body = f"<error: {e}>"

        # Log request
        self._log_json({
            "request_id": request_id,
            "type": "REQUEST",
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params) or None,
            "client": request.client.host if request.client else None,
            "body": request_body,
        })

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
                        response_body = response_body_bytes.decode("utf-8", errors="replace")[:1000]
                    else:
                        response_body = f"<binary {len(response_body_bytes)} bytes>"

                # Create new response with the same body
                from starlette.responses import Response as StarletteResponse
                response = StarletteResponse(
                    content=response_body_bytes,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )
            except Exception as e:
                logger.warning(f"response_body_read_error: {e}")

        # Choose log level based on status code
        level = "info"
        if response.status_code >= 500:
            level = "error"
        elif response.status_code >= 400:
            level = "warning"

        # Log response
        self._log_json({
            "request_id": request_id,
            "type": "RESPONSE",
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "body": response_body,
        }, level=level)

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


async def check_unmigrated_sessions() -> None:
    """Check for Sessions that haven't been migrated to Project-First architecture.

    This is a warning-only check - it won't block startup or auto-migrate.
    Operators should manually run the migration script when ready.
    """
    from sqlalchemy import func, select
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.database import async_session_maker
    from app.models.conversation import Conversation
    from app.models.session import Session

    try:
        async with async_session_maker() as session:
            session: AsyncSession

            # Count total Sessions
            total_sessions_result = await session.execute(
                select(func.count(Session.id))
            )
            total_sessions = total_sessions_result.scalar() or 0

            if total_sessions == 0:
                return  # No Sessions, nothing to migrate

            # Count Conversations that were migrated from Sessions
            # (they have migrated_from_session_id in extra_data)
            migrated_result = await session.execute(
                select(func.count(Conversation.id)).where(
                    Conversation.extra_data["migrated_from_session_id"].isnot(None)
                )
            )
            migrated_count = migrated_result.scalar() or 0

            unmigrated_count = total_sessions - migrated_count

            if unmigrated_count > 0:
                logger.warning(
                    "unmigrated_sessions_detected",
                    total_sessions=total_sessions,
                    migrated_sessions=migrated_count,
                    unmigrated_sessions=unmigrated_count,
                    action_required="Run migration script: python scripts/migrate_session_to_project.py",
                    docs="See docs/migration/session-to-project.md for details",
                )
            else:
                logger.info(
                    "session_migration_complete",
                    total_sessions=total_sessions,
                    all_migrated=True,
                )
    except Exception as e:
        # Don't fail startup if check fails - just log and continue
        logger.warning(
            "migration_check_failed",
            error=str(e),
            message="Could not check for unmigrated Sessions. This is non-blocking.",
        )


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
    from app.core.database import check_tables_exist, close_db, init_db, run_migrations
    await init_db()
    logger.info("database_connection_pool_initialized")

    # Check if critical tables exist
    tables_exist, missing_tables = await check_tables_exist()

    if not tables_exist:
        logger.warning(
            "missing_database_tables",
            missing_tables=missing_tables,
            environment=settings.ENVIRONMENT
        )

        if settings.ENVIRONMENT == "development":
            # Auto-run migrations in development
            logger.info("auto_running_migrations_in_development")
            migration_success = await run_migrations()

            if migration_success:
                # Re-check tables after migration
                tables_exist, missing_tables = await check_tables_exist()
                if not tables_exist:
                    logger.error(
                        "tables_still_missing_after_migration",
                        missing_tables=missing_tables
                    )
                    raise RuntimeError(
                        f"数据库迁移后仍缺少关键表: {missing_tables}. "
                        f"请检查 migration 文件是否完整。"
                    )
            else:
                raise RuntimeError(
                    f"数据库迁移失败. 缺少表: {missing_tables}. "
                    f"请手动运行: cd backend && alembic upgrade head"
                )
        else:
            # In production, fail fast with clear error
            raise RuntimeError(
                f"数据库缺少关键表: {missing_tables}. "
                f"请在部署前执行数据库迁移: alembic upgrade head"
            )

    # Initialize Redis connection pool
    from app.core.redis import close_redis, init_redis
    await init_redis()
    logger.info("redis_connection_pool_initialized")

    # Check for unmigrated Sessions (Project-First migration)
    await check_unmigrated_sessions()

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
