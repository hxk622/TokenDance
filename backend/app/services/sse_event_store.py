"""
SSE Event Store - Event persistence for reconnection recovery.

P1-3 Fix: When SSE connection drops and reconnects, the client may have
missed events. This service:
1. Stores all SSE events in Redis with sequence numbers
2. Provides replay capability for missed events
3. Automatically expires old events (configurable TTL)

Usage:
- On event emit: store_event(session_id, event_type, data)
- On reconnect: get_events_since(session_id, last_seq) to replay missed events
- Client sends ?last_seq=X to indicate last received event
"""
import json
import time
from typing import Any

from redis.asyncio import Redis

from app.core.logging import get_logger

logger = get_logger(__name__)


class SSEEventStore:
    """Service for storing and replaying SSE events."""

    # Redis key prefixes
    EVENTS_KEY_PREFIX = "sse_events:"  # Sorted set: score=seq, member=event_json
    SEQ_KEY_PREFIX = "sse_seq:"  # Counter for sequence numbers
    
    # Default TTL for events (30 minutes)
    DEFAULT_EVENT_TTL = 1800
    
    # Maximum events to store per session
    MAX_EVENTS_PER_SESSION = 500

    def __init__(self, redis: Redis, event_ttl: int | None = None):
        self.redis = redis
        self.event_ttl = event_ttl or self.DEFAULT_EVENT_TTL

    def _get_events_key(self, session_id: str) -> str:
        """Get Redis key for session events."""
        return f"{self.EVENTS_KEY_PREFIX}{session_id}"

    def _get_seq_key(self, session_id: str) -> str:
        """Get Redis key for session sequence counter."""
        return f"{self.SEQ_KEY_PREFIX}{session_id}"

    async def store_event(
        self,
        session_id: str,
        event_type: str,
        data: dict[str, Any],
    ) -> int:
        """
        Store an SSE event with sequence number.
        
        Args:
            session_id: Session ID
            event_type: Event type (e.g., 'agent_thinking', 'tool_call')
            data: Event data
            
        Returns:
            int: Sequence number assigned to this event
        """
        seq_key = self._get_seq_key(session_id)
        events_key = self._get_events_key(session_id)
        
        # Get next sequence number
        seq = await self.redis.incr(seq_key)
        
        # Create event record
        event_record = {
            "seq": seq,
            "event": event_type,
            "data": data,
            "timestamp": time.time(),
        }
        
        # Store in sorted set (score = sequence number)
        await self.redis.zadd(
            events_key,
            {json.dumps(event_record): seq},
        )
        
        # Set TTL on first event
        if seq == 1:
            await self.redis.expire(events_key, self.event_ttl)
            await self.redis.expire(seq_key, self.event_ttl)
        
        # Trim old events if needed
        event_count = await self.redis.zcard(events_key)
        if event_count > self.MAX_EVENTS_PER_SESSION:
            # Remove oldest events
            await self.redis.zremrangebyrank(
                events_key,
                0,
                event_count - self.MAX_EVENTS_PER_SESSION - 1,
            )
        
        return seq

    async def get_events_since(
        self,
        session_id: str,
        last_seq: int,
        max_events: int = 100,
    ) -> list[dict]:
        """
        Get events since a given sequence number (for replay).
        
        Args:
            session_id: Session ID
            last_seq: Last sequence number client received
            max_events: Maximum events to return
            
        Returns:
            list of events with seq > last_seq
        """
        events_key = self._get_events_key(session_id)
        
        # Get events with score > last_seq
        # ZRANGEBYSCORE with min=(last_seq exclusive
        raw_events = await self.redis.zrangebyscore(
            events_key,
            f"({last_seq}",  # Exclusive min
            "+inf",
            start=0,
            num=max_events,
        )
        
        events = []
        for raw in raw_events:
            try:
                event = json.loads(raw)
                events.append(event)
            except json.JSONDecodeError:
                logger.warning("sse_event_parse_error", raw=raw[:50])
                continue
        
        if events:
            logger.info(
                "sse_events_replayed",
                session_id=session_id,
                last_seq=last_seq,
                count=len(events),
            )
        
        return events

    async def get_latest_seq(self, session_id: str) -> int:
        """
        Get the latest sequence number for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            int: Latest sequence number, or 0 if no events
        """
        seq_key = self._get_seq_key(session_id)
        seq = await self.redis.get(seq_key)
        return int(seq) if seq else 0

    async def get_all_events(self, session_id: str) -> list[dict]:
        """
        Get all stored events for a session (for debugging).
        
        Args:
            session_id: Session ID
            
        Returns:
            list of all stored events
        """
        events_key = self._get_events_key(session_id)
        raw_events = await self.redis.zrange(events_key, 0, -1)
        
        events = []
        for raw in raw_events:
            try:
                event = json.loads(raw)
                events.append(event)
            except json.JSONDecodeError:
                continue
        
        return events

    async def clear_events(self, session_id: str) -> bool:
        """
        Clear all events for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            bool: True if events were cleared
        """
        events_key = self._get_events_key(session_id)
        seq_key = self._get_seq_key(session_id)
        
        deleted = await self.redis.delete(events_key, seq_key)
        
        if deleted:
            logger.info("sse_events_cleared", session_id=session_id)
            return True
        return False

    async def extend_ttl(self, session_id: str, additional_seconds: int = 600) -> bool:
        """
        Extend TTL for session events (e.g., when session is still active).
        
        Args:
            session_id: Session ID
            additional_seconds: Seconds to add to TTL
            
        Returns:
            bool: True if TTL was extended
        """
        events_key = self._get_events_key(session_id)
        seq_key = self._get_seq_key(session_id)
        
        # Get current TTL and extend
        events_ttl = await self.redis.ttl(events_key)
        if events_ttl > 0:
            new_ttl = events_ttl + additional_seconds
            await self.redis.expire(events_key, new_ttl)
            await self.redis.expire(seq_key, new_ttl)
            return True
        return False


# Global instance
_event_store: SSEEventStore | None = None


def get_sse_event_store(redis: Redis) -> SSEEventStore:
    """Get SSE event store instance."""
    global _event_store
    if _event_store is None:
        _event_store = SSEEventStore(redis)
    return _event_store
