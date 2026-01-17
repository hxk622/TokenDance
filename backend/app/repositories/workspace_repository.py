"""
Workspace repository - database access layer for workspaces.
"""
from uuid import uuid4

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.session import Session
from app.models.workspace import Workspace, WorkspaceType


class WorkspaceRepository:
    """Repository for Workspace database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        owner_id: str,
        name: str,
        slug: str,
        description: str | None = None,
        workspace_type: WorkspaceType = WorkspaceType.PERSONAL,
        team_id: str | None = None,
        filesystem_path: str | None = None,
    ) -> Workspace:
        """Create a new workspace."""
        workspace = Workspace(
            id=str(uuid4()),
            owner_id=owner_id,
            name=name,
            slug=slug,
            description=description,
            workspace_type=workspace_type,
            team_id=team_id,
            filesystem_path=filesystem_path or f"/data/users/{owner_id}/workspaces/{uuid4()}",
        )
        self.db.add(workspace)
        await self.db.commit()
        await self.db.refresh(workspace)
        return workspace

    async def get_by_id(
        self,
        workspace_id: str,
        include_sessions: bool = False,
    ) -> Workspace | None:
        """Get workspace by ID with optional eager loading."""
        query = select(Workspace).where(Workspace.id == workspace_id)

        if include_sessions:
            query = query.options(selectinload(Workspace.sessions))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_owner(
        self,
        owner_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Workspace], int]:
        """
        Get workspaces by owner with pagination.
        Returns (workspaces, total_count).
        """
        count_query = select(func.count()).select_from(Workspace).where(
            Workspace.owner_id == owner_id
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()

        query = (
            select(Workspace)
            .where(Workspace.owner_id == owner_id)
            .order_by(Workspace.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        workspaces = list(result.scalars().all())

        return workspaces, total

    async def get_by_slug(
        self,
        owner_id: str,
        slug: str,
    ) -> Workspace | None:
        """Get workspace by owner and slug."""
        query = select(Workspace).where(
            and_(
                Workspace.owner_id == owner_id,
                Workspace.slug == slug,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update(
        self,
        workspace_id: str,
        **updates,
    ) -> Workspace | None:
        """Update workspace fields."""
        workspace = await self.get_by_id(workspace_id)
        if not workspace:
            return None

        for key, value in updates.items():
            if hasattr(workspace, key) and value is not None:
                setattr(workspace, key, value)

        await self.db.commit()
        await self.db.refresh(workspace)
        return workspace

    async def delete(self, workspace_id: str) -> bool:
        """
        Delete a workspace.
        Sessions will be cascade deleted.
        """
        workspace = await self.get_by_id(workspace_id)
        if not workspace:
            return False

        await self.db.delete(workspace)
        await self.db.commit()
        return True

    async def get_session_count(self, workspace_id: str) -> int:
        """Get the number of sessions in a workspace."""
        query = select(func.count()).select_from(Session).where(
            Session.workspace_id == workspace_id
        )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def update_last_accessed(self, workspace_id: str) -> Workspace | None:
        """Update the last_accessed_at timestamp."""
        from datetime import datetime
        return await self.update(workspace_id, last_accessed_at=datetime.utcnow())

    async def increment_workspace_count(self, user_id: str) -> None:
        """Increment workspace count for user usage stats."""
        from app.models.user import User

        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if user:
            user.usage_stats["current_workspaces"] += 1
            await self.db.commit()

    async def decrement_workspace_count(self, user_id: str) -> None:
        """Decrement workspace count for user usage stats."""
        from app.models.user import User

        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if user and user.usage_stats["current_workspaces"] > 0:
            user.usage_stats["current_workspaces"] -= 1
            await self.db.commit()
