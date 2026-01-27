"""
Redis configuration and connection management.
"""
from collections.abc import AsyncGenerator, Awaitable
from typing import cast

import redis.asyncio as aioredis
from redis.asyncio import Redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Global Redis client
redis_client: Redis | None = None


async def init_redis() -> None:
    """Initialize Redis connection pool."""
    global redis_client

    try:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
            socket_keepalive=True,
            socket_connect_timeout=5,
            retry_on_timeout=True,
        )

        # Test connection
        await cast(Awaitable[bool], redis_client.ping())
        logger.info(
            "redis_initialized",
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
        )
    except Exception as e:
        logger.error("redis_initialization_failed", error=str(e))
        raise


async def close_redis() -> None:
    """Close Redis connection."""
    global redis_client

    if redis_client:
        await redis_client.aclose()
        redis_client = None
        logger.info("redis_connections_closed")


async def get_redis() -> AsyncGenerator[Redis, None]:
    """
    Dependency for getting Redis client.

    Usage:
        @app.get("/cache")
        async def get_cache(redis: Redis = Depends(get_redis)):
            ...
    """
    if redis_client is None:
        raise RuntimeError("Redis client not initialized")

    yield redis_client


async def check_redis_health() -> bool:
    """Check Redis connection health."""
    try:
        if redis_client is None:
            return False
        await cast(Awaitable[bool], redis_client.ping())
        return True
    except Exception as e:
        logger.error("redis_health_check_failed", error=str(e))
        return False
