"""
Session API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_permission_service
from app.models.session import SessionStatus
from app.models.user import User
from app.schemas.artifact import ArtifactList
from app.schemas.intent import IntentValidationRequest, IntentValidationResponse
from app.schemas.message import MessageList
from app.schemas.session import (
    SessionCreate,
    SessionDetail,
    SessionList,
    SessionResponse,
    SessionUpdate,
)
from app.services.intent_validation_service import IntentValidationService
from app.services.permission_service import PermissionError, PermissionService
from app.services.session_service import SessionService

router = APIRouter()


def get_session_service(db: AsyncSession = Depends(get_db)) -> SessionService:
    """Dependency to get SessionService instance."""
    return SessionService(db)


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: SessionCreate,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service),
    service: SessionService = Depends(get_session_service),
):
    """Create a new session."""
    # Check if user can create session in this workspace
    try:
        await permission_service.can_create_session(current_user, data.workspace_id)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e

    return await service.create_session(data)


@router.get("", response_model=SessionList)
async def list_sessions(
    workspace_id: str = Query(..., description="Workspace ID"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: SessionStatus | None = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service),
    service: SessionService = Depends(get_session_service),
):
    """List sessions for a workspace with pagination."""
    # Check workspace access
    try:
        await permission_service.check_workspace_access(current_user, workspace_id)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e

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
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service),
    service: SessionService = Depends(get_session_service),
):
    """Get session by ID."""
    # Check session access
    try:
        await permission_service.check_session_access(current_user, session_id)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e

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
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service),
    service: SessionService = Depends(get_session_service),
):
    """Update session."""
    # Check session access
    try:
        await permission_service.check_session_access(current_user, session_id)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e

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
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service),
    service: SessionService = Depends(get_session_service),
):
    """Delete session."""
    # Check session access
    try:
        await permission_service.check_session_access(current_user, session_id)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e

    success = await service.delete_session(session_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )


@router.post("/{session_id}/complete", response_model=SessionResponse)
async def complete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service),
    service: SessionService = Depends(get_session_service),
):
    """Mark session as completed."""
    # Check session access
    try:
        await permission_service.check_session_access(current_user, session_id)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e

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
    limit: int | None = Query(None, ge=1, le=1000, description="Max messages to return"),
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service),
    service: SessionService = Depends(get_session_service),
):
    """Get messages for a session."""
    # Check session access
    try:
        await permission_service.check_session_access(current_user, session_id)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e

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
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service),
    service: SessionService = Depends(get_session_service),
):
    """Get artifacts for a session."""
    # Check session access
    try:
        await permission_service.check_session_access(current_user, session_id)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e

    # Verify session exists
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    return await service.get_session_artifacts(session_id)


@router.post("/preflight", response_model=IntentValidationResponse)
async def preflight_check(
    data: IntentValidationRequest,
):
    """Pre-flight check to validate user intent completeness.

    This endpoint analyzes user input to determine if it contains
    sufficient information to execute a task. No authentication required.

    Returns:
        IntentValidationResponse: Validation results including:
        - is_complete: Whether the intent is actionable
        - confidence_score: Confidence in the validation (0-1)
        - missing_info: List of missing critical information
        - suggested_questions: Questions to clarify intent
    """
    try:
        service = IntentValidationService()
        return await service.validate_intent(data)
    except ValueError as e:
        # No LLM API key configured
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    except Exception as e:
        # LLM call failed - return permissive response
        return IntentValidationResponse(
            is_complete=True,
            confidence_score=0.0,
            missing_info=[],
            suggested_questions=[],
            reasoning=f"验证服务暂不可用: {str(e)}",
        )
