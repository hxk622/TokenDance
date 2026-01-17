"""Permission service - Row-Level Security for multi-tenancy."""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.session import Session
from app.models.user import User
from app.models.workspace import Workspace
from app.repositories.session_repository import SessionRepository
from app.repositories.workspace_repository import WorkspaceRepository

logger = get_logger(__name__)


class PermissionError(Exception):
    """Permission denied exception."""
    pass


class PermissionService:
    """Service for checking access permissions (Row-Level Security)."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.workspace_repo = WorkspaceRepository(db)
        self.session_repo = SessionRepository(db)

    async def check_workspace_access(
        self,
        user: User,
        workspace_id: str,
        require_owner: bool = False,
    ) -> Workspace:
        """
        Check if user has access to a workspace.

        Args:
            user: Current authenticated user
            workspace_id: Workspace ID to check
            require_owner: If True, user must be the owner

        Returns:
            Workspace object if access granted

        Raises:
            PermissionError: If access denied
        """
        workspace = await self.workspace_repo.get_by_id(workspace_id)

        if not workspace:
            logger.warning(
                "workspace_not_found",
                user_id=str(user.id),
                workspace_id=workspace_id,
            )
            raise PermissionError(f"Workspace {workspace_id} not found")

        # For Personal workspaces, check ownership
        if workspace.is_personal:
            if workspace.owner_id != str(user.id):
                logger.warning(
                    "workspace_access_denied_not_owner",
                    user_id=str(user.id),
                    workspace_id=workspace_id,
                    workspace_owner_id=workspace.owner_id,
                )
                raise PermissionError("You do not have access to this workspace")
        # For Team workspaces (Phase 3), check team membership
        elif workspace.is_team:
            # TODO: Implement team membership check in Phase 3
            logger.warning(
                "team_workspace_not_implemented",
                user_id=str(user.id),
                workspace_id=workspace_id,
            )
            raise PermissionError("Team workspaces are not yet implemented")

        return workspace

    async def check_session_access(
        self,
        user: User,
        session_id: str,
        require_owner: bool = False,
    ) -> Session:
        """
        Check if user has access to a session.

        Args:
            user: Current authenticated user
            session_id: Session ID to check
            require_owner: If True, user must be the workspace owner

        Returns:
            Session object if access granted

        Raises:
            PermissionError: If access denied
        """
        session = await self.session_repo.get_by_id(session_id)

        if not session:
            logger.warning(
                "session_not_found",
                user_id=str(user.id),
                session_id=session_id,
            )
            raise PermissionError(f"Session {session_id} not found")

        # Check workspace access first
        await self.check_workspace_access(
            user,
            session.workspace_id,
            require_owner=require_owner,
        )

        return session

    async def can_create_workspace(self, user: User) -> bool:
        """
        Check if user can create a new workspace.

        Args:
            user: Current authenticated user

        Returns:
            True if user can create workspace
        """
        # Check personal quota
        if not user.can_create_workspace():
            logger.warning(
                "workspace_quota_exceeded",
                user_id=str(user.id),
                current_workspaces=user.usage_stats["current_workspaces"],
                max_workspaces=user.personal_quota["max_workspaces"],
            )
            raise PermissionError(
                f"You have reached your workspace limit ({user.personal_quota['max_workspaces']})"
            )

        return True

    async def can_create_session(self, user: User, workspace_id: str) -> bool:
        """
        Check if user can create a new session in a workspace.

        Args:
            user: Current authenticated user
            workspace_id: Workspace ID

        Returns:
            True if user can create session
        """
        # Check workspace access
        await self.check_workspace_access(user, workspace_id)

        return True

    async def check_user_is_active(self, user: User) -> None:
        """
        Check if user account is active.

        Args:
            user: Current authenticated user

        Raises:
            PermissionError: If user is inactive
        """
        if not user.is_active:
            logger.warning(
                "user_account_inactive",
                user_id=str(user.id),
            )
            raise PermissionError("Your account is inactive")

    async def check_user_is_verified(self, user: User) -> None:
        """
        Check if user email is verified.

        Args:
            user: Current authenticated user

        Raises:
            PermissionError: If user is not verified
        """
        if not user.is_verified:
            logger.warning(
                "user_email_not_verified",
                user_id=str(user.id),
            )
            raise PermissionError("Please verify your email address")

    def raise_permission_error(self, message: str = "Permission denied") -> None:
        """
        Raise a permission error as HTTPException.

        Args:
            message: Error message

        Raises:
            HTTPException: With 403 status code
        """
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message,
        )
