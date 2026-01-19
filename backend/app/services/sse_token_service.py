"""
SSE Token Service - Secure token exchange for SSE connections.

P1-1 Fix: Instead of passing JWT tokens in URL query parameters (security risk),
this service provides:
1. Exchange endpoint: POST /api/v1/sse/token - exchanges access token for short-lived SSE token
2. SSE tokens are stored in Redis with TTL
3. SSE endpoint validates SSE token instead of JWT

Security benefits:
- SSE tokens are short-lived (5 minutes by default)
- SSE tokens are single-use (deleted after first use)
- JWT access tokens are never exposed in URLs
"""
import secrets
from datetime import datetime

from redis.asyncio import Redis

from app.core.logging import get_logger

logger = get_logger(__name__)


class SSETokenService:
    """Service for managing short-lived SSE tokens."""

    # Redis key prefix for SSE tokens
    KEY_PREFIX = "sse_token:"
    
    # Default TTL for SSE tokens (5 minutes)
    DEFAULT_TTL_SECONDS = 300
    
    def __init__(self, redis: Redis):
        self.redis = redis

    async def create_sse_token(
        self,
        user_id: str,
        session_id: str,
        ttl_seconds: int | None = None,
    ) -> str:
        """
        Create a short-lived SSE token.
        
        Args:
            user_id: User ID who owns this token
            session_id: Session ID this token is valid for
            ttl_seconds: Token TTL in seconds (default: 300)
            
        Returns:
            str: The SSE token
        """
        ttl = ttl_seconds or self.DEFAULT_TTL_SECONDS
        
        # Generate secure random token
        token = secrets.token_urlsafe(32)
        
        # Store token data in Redis
        key = f"{self.KEY_PREFIX}{token}"
        token_data = {
            "user_id": user_id,
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        # Set with TTL
        await self.redis.hset(key, mapping=token_data)
        await self.redis.expire(key, ttl)
        
        logger.info(
            "sse_token_created",
            user_id=user_id,
            session_id=session_id,
            ttl_seconds=ttl,
        )
        
        return token

    async def validate_sse_token(
        self,
        token: str,
        session_id: str,
        consume: bool = True,
    ) -> dict | None:
        """
        Validate and optionally consume an SSE token.
        
        Args:
            token: The SSE token to validate
            session_id: Expected session ID
            consume: If True, delete token after validation (single-use)
            
        Returns:
            dict with user_id and session_id if valid, None otherwise
        """
        key = f"{self.KEY_PREFIX}{token}"
        
        # Get token data
        token_data = await self.redis.hgetall(key)
        
        if not token_data:
            logger.warning("sse_token_invalid_or_expired", token_prefix=token[:8])
            return None
        
        # Validate session_id matches
        stored_session_id = token_data.get("session_id")
        if stored_session_id != session_id:
            logger.warning(
                "sse_token_session_mismatch",
                expected=session_id,
                got=stored_session_id,
            )
            return None
        
        # Consume token (single-use)
        if consume:
            await self.redis.delete(key)
            logger.info(
                "sse_token_consumed",
                user_id=token_data.get("user_id"),
                session_id=session_id,
            )
        
        return {
            "user_id": token_data.get("user_id"),
            "session_id": stored_session_id,
        }

    async def revoke_sse_token(self, token: str) -> bool:
        """
        Revoke an SSE token before it expires.
        
        Args:
            token: The SSE token to revoke
            
        Returns:
            bool: True if token was revoked, False if not found
        """
        key = f"{self.KEY_PREFIX}{token}"
        deleted = await self.redis.delete(key)
        
        if deleted:
            logger.info("sse_token_revoked", token_prefix=token[:8])
            return True
        return False

    async def revoke_user_tokens(self, user_id: str) -> int:
        """
        Revoke all SSE tokens for a user.
        
        Note: This requires scanning Redis keys, which can be slow.
        For production, consider using a secondary index.
        
        Args:
            user_id: User ID whose tokens to revoke
            
        Returns:
            int: Number of tokens revoked
        """
        count = 0
        pattern = f"{self.KEY_PREFIX}*"
        
        async for key in self.redis.scan_iter(match=pattern):
            token_data = await self.redis.hgetall(key)
            if token_data.get("user_id") == user_id:
                await self.redis.delete(key)
                count += 1
        
        if count > 0:
            logger.info(
                "sse_tokens_revoked_for_user",
                user_id=user_id,
                count=count,
            )
        
        return count


# Dependency for FastAPI
_sse_token_service: SSETokenService | None = None


async def get_sse_token_service(redis: Redis) -> SSETokenService:
    """Get SSE token service instance."""
    global _sse_token_service
    if _sse_token_service is None:
        _sse_token_service = SSETokenService(redis)
    return _sse_token_service
