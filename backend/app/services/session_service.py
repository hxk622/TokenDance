"""
Session service - business logic for session management.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.session import SessionStatus
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.session_repository import SessionRepository
from app.schemas.session import (
    SessionCreate,
    SessionDetail,
    SessionList,
    SessionResponse,
    SessionUpdate,
)

logger = get_logger(__name__)


class SessionService:
    """Service for session-related business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.session_repo = SessionRepository(db)
        self.message_repo = MessageRepository(db)
        self.artifact_repo = ArtifactRepository(db)

    async def create_session(
        self,
        data: SessionCreate,
    ) -> SessionResponse:
        """Create a new session."""
        session = await self.session_repo.create(
            workspace_id=data.workspace_id,
            title=data.title,
            skill_id=data.skill_id,
        )

        logger.info(
            "session_created",
            session_id=session.id,
            workspace_id=session.workspace_id,
        )

        # Manually construct response to avoid lazy loading issue
        return SessionResponse(
            id=session.id,
            workspace_id=session.workspace_id,
            title=session.title,
            status=session.status,
            skill_id=session.skill_id,
            total_tokens_used=session.total_tokens_used,
            message_count=0,  # New session has no messages
            created_at=session.created_at,
            updated_at=session.updated_at,
            completed_at=session.completed_at,
        )

    async def get_session(
        self,
        session_id: str,
        include_details: bool = False,
    ) -> SessionResponse | SessionDetail | None:
        """Get session by ID."""
        session = await self.session_repo.get_by_id(
            session_id,
            include_messages=include_details,
            include_artifacts=include_details,
        )

        if not session:
            return None

        # Get message count separately to avoid lazy loading
        message_count = await self.session_repo.get_message_count(session_id)

        if include_details:
            session_data = SessionDetail(
                id=session.id,
                workspace_id=session.workspace_id,
                title=session.title,
                status=session.status,
                skill_id=session.skill_id,
                total_tokens_used=session.total_tokens_used,
                message_count=message_count,
                created_at=session.created_at,
                updated_at=session.updated_at,
                completed_at=session.completed_at,
                context_summary=session.context_summary,
                todo_list=session.todo_list,
                extra_data=session.extra_data or {},
            )
            return session_data

        return SessionResponse(
            id=session.id,
            workspace_id=session.workspace_id,
            title=session.title,
            status=session.status,
            skill_id=session.skill_id,
            total_tokens_used=session.total_tokens_used,
            message_count=message_count,
            created_at=session.created_at,
            updated_at=session.updated_at,
            completed_at=session.completed_at,
        )

    async def list_sessions(
        self,
        workspace_id: str,
        limit: int = 20,
        offset: int = 0,
        status: SessionStatus | None = None,
    ) -> SessionList:
        """List sessions for a workspace."""
        sessions, total = await self.session_repo.get_by_workspace(
            workspace_id=workspace_id,
            limit=limit,
            offset=offset,
            status=status,
        )

        # Get message counts for each session
        session_responses = []
        for session in sessions:
            message_count = await self.session_repo.get_message_count(session.id)
            session_data = SessionResponse(
                id=session.id,
                workspace_id=session.workspace_id,
                title=session.title,
                status=session.status,
                skill_id=session.skill_id,
                total_tokens_used=session.total_tokens_used,
                message_count=message_count,
                created_at=session.created_at,
                updated_at=session.updated_at,
                completed_at=session.completed_at,
            )
            session_responses.append(session_data)

        return SessionList(
            items=session_responses,
            total=total,
            limit=limit,
            offset=offset,
        )

    async def update_session(
        self,
        session_id: str,
        data: SessionUpdate,
    ) -> SessionResponse | None:
        """Update session."""
        updates = data.model_dump(exclude_unset=True)

        if not updates:
            # No updates provided, just return current
            return await self.get_session(session_id)

        session = await self.session_repo.update(session_id, **updates)

        if not session:
            return None

        logger.info(
            "session_updated",
            session_id=session_id,
            updates=list(updates.keys()),
        )

        message_count = await self.session_repo.get_message_count(session_id)
        return SessionResponse(
            id=session.id,
            workspace_id=session.workspace_id,
            title=session.title,
            status=session.status,
            skill_id=session.skill_id,
            total_tokens_used=session.total_tokens_used,
            message_count=message_count,
            created_at=session.created_at,
            updated_at=session.updated_at,
            completed_at=session.completed_at,
        )

    async def complete_session(
        self,
        session_id: str,
    ) -> SessionResponse | None:
        """Mark session as completed."""
        from datetime import datetime

        session = await self.session_repo.update(
            session_id,
            status=SessionStatus.COMPLETED,
            completed_at=datetime.utcnow(),
        )

        if not session:
            return None

        logger.info("session_completed", session_id=session_id)

        message_count = await self.session_repo.get_message_count(session_id)
        return SessionResponse(
            id=session.id,
            workspace_id=session.workspace_id,
            title=session.title,
            status=session.status,
            skill_id=session.skill_id,
            total_tokens_used=session.total_tokens_used,
            message_count=message_count,
            created_at=session.created_at,
            updated_at=session.updated_at,
            completed_at=session.completed_at,
        )

    async def delete_session(
        self,
        session_id: str,
    ) -> bool:
        """Delete a session and all associated data."""
        success = await self.session_repo.delete(session_id)

        if success:
            logger.info("session_deleted", session_id=session_id)

        return success

    async def get_session_messages(
        self,
        session_id: str,
        limit: int | None = None,
    ):
        """Get messages for a session."""
        from app.schemas.message import MessageList, MessageResponse

        messages = await self.message_repo.get_by_session(session_id, limit=limit)

        return MessageList(
            items=[MessageResponse.model_validate(msg) for msg in messages],
            total=len(messages),
        )

    async def get_session_artifacts(
        self,
        session_id: str,
    ):
        """Get artifacts for a session."""
        from app.schemas.artifact import ArtifactList, ArtifactResponse

        artifacts = await self.artifact_repo.get_by_session(session_id)

        return ArtifactList(
            items=[ArtifactResponse.model_validate(art) for art in artifacts],
            total=len(artifacts),
        )

    async def archive_old_sessions(
        self,
        workspace_id: str,
        days: int = 30,
    ) -> int:
        """Archive old completed sessions."""
        count = await self.session_repo.archive_old_sessions(workspace_id, days)

        logger.info(
            "sessions_archived",
            workspace_id=workspace_id,
            count=count,
            days=days,
        )

        return count
