"""
Agent Stop Service - Graceful agent execution termination.

P1-2 Fix: Implements stop signal mechanism using Redis.
When user clicks "stop" button:
1. Frontend calls POST /api/v1/sessions/{session_id}/stop
2. Backend sets stop flag in Redis
3. Agent checks this flag in its main loop
4. Agent gracefully terminates and updates session status to CANCELLED

Usage in agent loop:
    stop_service = AgentStopService(redis)
    while running:
        if await stop_service.should_stop(session_id):
            break
        # ... continue agent work
"""
from redis.asyncio import Redis

from app.core.logging import get_logger

logger = get_logger(__name__)


class AgentStopService:
    """Service for managing agent stop signals via Redis."""

    # Redis key prefix for stop signals
    KEY_PREFIX = "agent_stop:"

    # TTL for stop signals (10 minutes - should be longer than max agent run time)
    STOP_SIGNAL_TTL = 600

    def __init__(self, redis: Redis):
        self.redis = redis

    def _get_key(self, session_id: str) -> str:
        """Get Redis key for session stop signal."""
        return f"{self.KEY_PREFIX}{session_id}"

    async def request_stop(self, session_id: str, user_id: str) -> bool:
        """
        Request agent to stop execution.

        Args:
            session_id: Session ID to stop
            user_id: User ID requesting the stop

        Returns:
            bool: True if stop signal was set
        """
        key = self._get_key(session_id)

        # Set stop signal with TTL
        await self.redis.setex(
            key,
            self.STOP_SIGNAL_TTL,
            user_id,
        )

        logger.info(
            "agent_stop_requested",
            session_id=session_id,
            user_id=user_id,
        )

        return True

    async def should_stop(self, session_id: str) -> bool:
        """
        Check if agent should stop execution.

        This should be called periodically in the agent loop.

        Args:
            session_id: Session ID to check

        Returns:
            bool: True if stop was requested
        """
        key = self._get_key(session_id)
        exists = await self.redis.exists(key)
        return bool(exists)

    async def clear_stop_signal(self, session_id: str) -> bool:
        """
        Clear stop signal after agent has stopped.

        Args:
            session_id: Session ID to clear

        Returns:
            bool: True if signal was cleared
        """
        key = self._get_key(session_id)
        deleted = await self.redis.delete(key)

        if deleted:
            logger.info("agent_stop_signal_cleared", session_id=session_id)
            return True
        return False

    async def get_stop_info(self, session_id: str) -> dict | None:
        """
        Get information about who requested the stop.

        Args:
            session_id: Session ID to check

        Returns:
            dict with user_id if stop was requested, None otherwise
        """
        key = self._get_key(session_id)
        user_id = await self.redis.get(key)

        if user_id:
            return {"user_id": user_id, "session_id": session_id}
        return None


# Global instance
_stop_service: AgentStopService | None = None


def get_agent_stop_service(redis: Redis) -> AgentStopService:
    """Get agent stop service instance."""
    global _stop_service
    if _stop_service is None:
        _stop_service = AgentStopService(redis)
    return _stop_service
