"""
Human-in-the-Loop (HITL) Service
Manages confirmation requests for high-risk operations.
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import Any

from redis.asyncio import Redis

from app.core.logging import get_logger

logger = get_logger(__name__)

# Redis key prefixes
HITL_REQUEST_PREFIX = "hitl:request:"
HITL_RESPONSE_PREFIX = "hitl:response:"
HITL_TIMEOUT_SECONDS = 300  # 5 minutes


class HITLRequest:
    """HITL confirmation request."""
    
    def __init__(
        self,
        request_id: str,
        session_id: str,
        operation: str,
        description: str,
        context: dict[str, Any] | None = None,
    ):
        self.request_id = request_id
        self.session_id = session_id
        self.operation = operation
        self.description = description
        self.context = context or {}
        self.created_at = datetime.utcnow()
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "session_id": self.session_id,
            "operation": self.operation,
            "description": self.description,
            "context": self.context,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HITLRequest":
        return cls(
            request_id=data["request_id"],
            session_id=data["session_id"],
            operation=data["operation"],
            description=data["description"],
            context=data.get("context", {}),
        )


class HITLResponse:
    """HITL confirmation response."""
    
    def __init__(
        self,
        request_id: str,
        approved: bool,
        user_feedback: str | None = None,
        responded_at: datetime | None = None,
    ):
        self.request_id = request_id
        self.approved = approved
        self.user_feedback = user_feedback
        self.responded_at = responded_at or datetime.utcnow()
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "approved": self.approved,
            "user_feedback": self.user_feedback,
            "responded_at": self.responded_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HITLResponse":
        return cls(
            request_id=data["request_id"],
            approved=data["approved"],
            user_feedback=data.get("user_feedback"),
            responded_at=datetime.fromisoformat(data["responded_at"]) if data.get("responded_at") else None,
        )


class HITLService:
    """Service for managing HITL confirmation flow."""
    
    def __init__(self, redis: Redis):
        self.redis = redis
    
    async def create_request(
        self,
        session_id: str,
        operation: str,
        description: str,
        context: dict[str, Any] | None = None,
    ) -> HITLRequest:
        """
        Create a new HITL confirmation request.
        
        Args:
            session_id: Session ID
            operation: Operation name (e.g., "file_delete", "shell_exec")
            description: Human-readable description
            context: Additional context data
        
        Returns:
            HITLRequest instance
        """
        request_id = str(uuid.uuid4())
        request = HITLRequest(
            request_id=request_id,
            session_id=session_id,
            operation=operation,
            description=description,
            context=context,
        )
        
        # Store in Redis with expiration
        key = f"{HITL_REQUEST_PREFIX}{request_id}"
        await self.redis.setex(
            key,
            HITL_TIMEOUT_SECONDS,
            json.dumps(request.to_dict()),
        )
        
        logger.info(
            "hitl_request_created",
            request_id=request_id,
            session_id=session_id,
            operation=operation,
        )
        
        return request
    
    async def get_request(self, request_id: str) -> HITLRequest | None:
        """Get HITL request by ID."""
        key = f"{HITL_REQUEST_PREFIX}{request_id}"
        data = await self.redis.get(key)
        
        if not data:
            return None
        
        return HITLRequest.from_dict(json.loads(data))
    
    async def submit_response(
        self,
        request_id: str,
        approved: bool,
        user_feedback: str | None = None,
    ) -> HITLResponse:
        """
        Submit user response to HITL request.
        
        Args:
            request_id: Request ID
            approved: Whether user approved the operation
            user_feedback: Optional feedback text
        
        Returns:
            HITLResponse instance
        """
        # Check if request exists
        request = await self.get_request(request_id)
        if not request:
            raise ValueError(f"HITL request {request_id} not found or expired")
        
        # Create response
        response = HITLResponse(
            request_id=request_id,
            approved=approved,
            user_feedback=user_feedback,
        )
        
        # Store response in Redis
        response_key = f"{HITL_RESPONSE_PREFIX}{request_id}"
        await self.redis.setex(
            response_key,
            HITL_TIMEOUT_SECONDS,
            json.dumps(response.to_dict()),
        )
        
        logger.info(
            "hitl_response_submitted",
            request_id=request_id,
            approved=approved,
        )
        
        return response
    
    async def get_response(self, request_id: str) -> HITLResponse | None:
        """Get HITL response by request ID."""
        key = f"{HITL_RESPONSE_PREFIX}{request_id}"
        data = await self.redis.get(key)
        
        if not data:
            return None
        
        return HITLResponse.from_dict(json.loads(data))
    
    async def wait_for_response(
        self,
        request_id: str,
        timeout_seconds: int = HITL_TIMEOUT_SECONDS,
    ) -> HITLResponse | None:
        """
        Wait for user response (polling).
        
        Args:
            request_id: Request ID
            timeout_seconds: Maximum wait time
        
        Returns:
            HITLResponse if received, None if timeout
        """
        import asyncio
        
        start_time = datetime.utcnow()
        
        while True:
            response = await self.get_response(request_id)
            if response:
                return response
            
            # Check timeout
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed >= timeout_seconds:
                logger.warning(
                    "hitl_response_timeout",
                    request_id=request_id,
                    elapsed_seconds=elapsed,
                )
                return None
            
            # Wait before next check
            await asyncio.sleep(1)
    
    async def list_pending_requests(self, session_id: str) -> list[HITLRequest]:
        """List all pending HITL requests for a session."""
        # Scan Redis for requests matching session
        pattern = f"{HITL_REQUEST_PREFIX}*"
        cursor = 0
        requests = []
        
        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
            
            for key in keys:
                data = await self.redis.get(key)
                if data:
                    request = HITLRequest.from_dict(json.loads(data))
                    if request.session_id == session_id:
                        # Check if response exists
                        response = await self.get_response(request.request_id)
                        if not response:
                            requests.append(request)
            
            if cursor == 0:
                break
        
        return requests
