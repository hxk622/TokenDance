"""
HITL (Human-in-the-Loop) API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from redis.asyncio import Redis

from app.core.redis import get_redis
from app.services.hitl_service import HITLService

router = APIRouter()


class HITLConfirmRequest(BaseModel):
    """Request body for HITL confirmation."""

    approved: bool
    user_feedback: str | None = None


class HITLRequestResponse(BaseModel):
    """Response for HITL request."""

    request_id: str
    session_id: str
    operation: str
    description: str
    context: dict
    created_at: str


class HITLConfirmResponse(BaseModel):
    """Response for HITL confirmation."""

    request_id: str
    approved: bool
    user_feedback: str | None = None
    responded_at: str


@router.get("/sessions/{session_id}/hitl/pending")
async def list_pending_hitl_requests(
    session_id: str,
    redis: Redis = Depends(get_redis),
) -> list[HITLRequestResponse]:
    """
    List all pending HITL requests for a session.

    This endpoint allows the UI to poll for pending confirmation requests.
    """
    service = HITLService(redis)
    requests = await service.list_pending_requests(session_id)

    return [
        HITLRequestResponse(
            request_id=req.request_id,
            session_id=req.session_id,
            operation=req.operation,
            description=req.description,
            context=req.context,
            created_at=req.created_at.isoformat(),
        )
        for req in requests
    ]


@router.post("/hitl/{request_id}/confirm")
async def confirm_hitl_request(
    request_id: str,
    body: HITLConfirmRequest,
    redis: Redis = Depends(get_redis),
) -> HITLConfirmResponse:
    """
    Submit user confirmation for a HITL request.

    Args:
        request_id: HITL request ID
        body: Confirmation details

    Returns:
        Confirmation response
    """
    service = HITLService(redis)

    try:
        response = await service.submit_response(
            request_id=request_id,
            approved=body.approved,
            user_feedback=body.user_feedback,
        )

        return HITLConfirmResponse(
            request_id=response.request_id,
            approved=response.approved,
            user_feedback=response.user_feedback,
            responded_at=response.responded_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/hitl/{request_id}")
async def get_hitl_request(
    request_id: str,
    redis: Redis = Depends(get_redis),
) -> HITLRequestResponse:
    """Get HITL request details by ID."""
    service = HITLService(redis)
    request = await service.get_request(request_id)

    if not request:
        raise HTTPException(status_code=404, detail="HITL request not found or expired")

    return HITLRequestResponse(
        request_id=request.request_id,
        session_id=request.session_id,
        operation=request.operation,
        description=request.description,
        context=request.context,
        created_at=request.created_at.isoformat(),
    )
