"""
Workspace API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_permission_service
from app.models.user import User
from app.models.workspace import WorkspaceType
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceDetail,
    WorkspaceList,
    WorkspaceResponse,
    WorkspaceUpdate,
)
from app.services.permission_service import PermissionError, PermissionService
from app.services.workspace_service import WorkspaceService

router = APIRouter()


def get_workspace_service(db: AsyncSession = Depends(get_db)) -> WorkspaceService:
    """Dependency to get WorkspaceService instance."""
    return WorkspaceService(db)


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    data: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service),
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Create a new workspace."""
    # Check if user can create workspace
    try:
        await permission_service.can_create_workspace(current_user)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e

    return await service.create_workspace(
        owner_id=str(current_user.id),
        name=data.name,
        slug=data.slug,
        description=data.description,
        workspace_type=data.workspace_type or WorkspaceType.PERSONAL,
    )


@router.get("", response_model=WorkspaceList)
async def list_workspaces(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
):
    """List workspaces for current user with pagination."""
    return await service.list_workspaces(
        owner_id=str(current_user.id),
        limit=limit,
        offset=offset,
    )


@router.get("/{workspace_id}", response_model=WorkspaceResponse | WorkspaceDetail)
async def get_workspace(
    workspace_id: str,
    include_details: bool = Query(False, description="Include detailed info"),
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service),
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Get workspace by ID."""
    # Check workspace access
    try:
        await permission_service.check_workspace_access(current_user, workspace_id)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e

    workspace = await service.get_workspace(workspace_id, include_details=include_details)

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace {workspace_id} not found",
        )

    return workspace


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: str,
    data: WorkspaceUpdate,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service),
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Update workspace."""
    # Check workspace access (require owner for updates)
    try:
        await permission_service.check_workspace_access(
            current_user,
            workspace_id,
            require_owner=True,
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e

    workspace = await service.update_workspace(workspace_id, data)

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace {workspace_id} not found",
        )

    return workspace


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service),
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Delete workspace."""
    # Check workspace access (require owner for deletion)
    try:
        await permission_service.check_workspace_access(
            current_user,
            workspace_id,
            require_owner=True,
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e

    success = await service.delete_workspace(workspace_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace {workspace_id} not found",
        )


@router.get("/{workspace_id}/sessions", response_model=WorkspaceList)
async def get_workspace_sessions(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service),
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Get sessions for a workspace."""
    # Check workspace access
    try:
        await permission_service.check_workspace_access(current_user, workspace_id)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e

    return await service.get_workspace_sessions(workspace_id)
