"""
Session API endpoints.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.session import SessionStatus
from app.services.session_service import SessionService
from app.schemas.session import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionDetail,
    SessionList,
)
from app.schemas.message import MessageList
from app.schemas.artifact import ArtifactList

router = APIRouter()


def get_session_service(db: AsyncSession = Depends(get_db)) -> SessionService:
    """Dependency to get SessionService instance."""
    return SessionService(db)


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: SessionCreate,
    service: SessionService = Depends(get_session_service),
):
    """Create a new session."""
    return await service.create_session(data)


@router.get("", response_model=SessionList)
async def list_sessions(
    workspace_id: str = Query(..., description="Workspace ID"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[SessionStatus] = Query(None, description="Filter by status"),
    service: SessionService = Depends(get_session_service),
):
    """List sessions for a workspace with pagination."""
    return await service.list_sessions(
        workspace_id=workspace_id,
        limit=limit,
        offset=offset,
        status=status,
    )


@router.get("/{session_id}", response_model=SessionResponse | SessionDetail)
async def get_session(
    session_id: str,
    include_details: bool = Query(False, description="Include detailed info"),
    service: SessionService = Depends(get_session_service),
):
    """Get session by ID."""
    session = await service.get_session(session_id, include_details=include_details)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    return session


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    data: SessionUpdate,
    service: SessionService = Depends(get_session_service),
):
    """Update session."""
    session = await service.update_session(session_id, data)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    service: SessionService = Depends(get_session_service),
):
    """Delete session."""
    success = await service.delete_session(session_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )


@router.post("/{session_id}/complete", response_model=SessionResponse)
async def complete_session(
    session_id: str,
    service: SessionService = Depends(get_session_service),
):
    """Mark session as completed."""
    session = await service.complete_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    return session


@router.get("/{session_id}/messages", response_model=MessageList)
async def get_session_messages(
    session_id: str,
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Max messages to return"),
    service: SessionService = Depends(get_session_service),
):
    """Get messages for a session."""
    # Verify session exists
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    return await service.get_session_messages(session_id, limit=limit)


@router.get("/{session_id}/artifacts", response_model=ArtifactList)
async def get_session_artifacts(
    session_id: str,
    service: SessionService = Depends(get_session_service),
):
    """Get artifacts for a session."""
    # Verify session exists
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    return await service.get_session_artifacts(session_id)
