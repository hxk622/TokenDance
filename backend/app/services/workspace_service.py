"""
Workspace service - business logic for workspace management.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.workspace import WorkspaceType
from app.repositories.session_repository import SessionRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.workspace import (
    WorkspaceDetail,
    WorkspaceList,
    WorkspaceResponse,
    WorkspaceUpdate,
)

logger = get_logger(__name__)


class WorkspaceService:
    """Service for workspace-related business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.workspace_repo = WorkspaceRepository(db)
        self.session_repo = SessionRepository(db)

    async def create_workspace(
        self,
        owner_id: str,
        name: str,
        slug: str,
        description: str | None = None,
        workspace_type: WorkspaceType = WorkspaceType.PERSONAL,
    ) -> WorkspaceResponse:
        """Create a new workspace."""
        # Check if slug already exists for this owner
        existing = await self.workspace_repo.get_by_slug(owner_id, slug)
        if existing:
            raise ValueError(f"Workspace with slug '{slug}' already exists")

        workspace = await self.workspace_repo.create(
            owner_id=owner_id,
            name=name,
            slug=slug,
            description=description,
            workspace_type=workspace_type,
        )

        # Increment user's workspace count
        await self.workspace_repo.increment_workspace_count(owner_id)

        logger.info(
            "workspace_created",
            workspace_id=workspace.id,
            owner_id=owner_id,
            name=name,
        )

        return WorkspaceResponse.model_validate(workspace)

    async def get_workspace(
        self,
        workspace_id: str,
        include_details: bool = False,
    ) -> WorkspaceResponse | WorkspaceDetail | None:
        """Get workspace by ID."""
        workspace = await self.workspace_repo.get_by_id(
            workspace_id,
            include_sessions=include_details,
        )

        if not workspace:
            return None

        if include_details:
            # Get session count separately for performance
            session_count = await self.workspace_repo.get_session_count(workspace_id)
            workspace_data = WorkspaceDetail.model_validate(workspace)
            workspace_data.session_count = session_count
            return workspace_data

        return WorkspaceResponse.model_validate(workspace)

    async def list_workspaces(
        self,
        owner_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> WorkspaceList:
        """List workspaces for an owner with pagination."""
        workspaces, total = await self.workspace_repo.get_by_owner(
            owner_id=owner_id,
            limit=limit,
            offset=offset,
        )

        # Get session counts for each workspace
        workspace_responses = []
        for workspace in workspaces:
            session_count = await self.workspace_repo.get_session_count(workspace.id)
            workspace_data = WorkspaceResponse.model_validate(workspace)
            workspace_data.session_count = session_count
            workspace_responses.append(workspace_data)

        return WorkspaceList(
            items=workspace_responses,
            total=total,
            limit=limit,
            offset=offset,
        )

    async def update_workspace(
        self,
        workspace_id: str,
        data: WorkspaceUpdate,
    ) -> WorkspaceResponse | None:
        """Update workspace."""
        updates = data.model_dump(exclude_unset=True)

        if not updates:
            # No updates provided, just return current
            workspace = await self.workspace_repo.get_by_id(workspace_id)
            return WorkspaceResponse.model_validate(workspace) if workspace else None

        # Check if slug is being updated and if it conflicts
        if "slug" in updates:
            workspace = await self.workspace_repo.get_by_id(workspace_id)
            if workspace:
                existing = await self.workspace_repo.get_by_slug(
                    workspace.owner_id,
                    updates["slug"],
                )
                if existing and existing.id != workspace_id:
                    raise ValueError(f"Workspace with slug '{updates['slug']}' already exists")

        workspace = await self.workspace_repo.update(workspace_id, **updates)

        if workspace:
            logger.info(
                "workspace_updated",
                workspace_id=workspace_id,
                updates=list(updates.keys()),
            )

        return WorkspaceResponse.model_validate(workspace) if workspace else None

    async def delete_workspace(
        self,
        workspace_id: str,
    ) -> bool:
        """Delete a workspace and all associated data."""
        workspace = await self.workspace_repo.get_by_id(workspace_id)
        if not workspace:
            return False

        owner_id = workspace.owner_id

        success = await self.workspace_repo.delete(workspace_id)

        if success:
            # Decrement user's workspace count
            await self.workspace_repo.decrement_workspace_count(owner_id)
            logger.info("workspace_deleted", workspace_id=workspace_id)

        return success

    async def get_workspace_sessions(
        self,
        workspace_id: str,
    ):
        """Get sessions for a workspace."""
        from app.schemas.session import SessionList, SessionResponse

        sessions, total = await self.session_repo.get_by_workspace(
            workspace_id=workspace_id,
            limit=100,
            offset=0,
        )

        return SessionList(
            items=[SessionResponse.model_validate(session) for session in sessions],
            total=total,
            limit=100,
            offset=0,
        )

    async def update_last_accessed(
        self,
        workspace_id: str,
    ) -> WorkspaceResponse | None:
        """Update last_accessed_at timestamp."""
        workspace = await self.workspace_repo.update_last_accessed(workspace_id)

        return WorkspaceResponse.model_validate(workspace) if workspace else None
