"""
Session service - business logic for session management.
"""
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import SessionStatus
from app.repositories.session_repository import SessionRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.artifact_repository import ArtifactRepository
from app.schemas.session import SessionCreate, SessionUpdate, SessionResponse, SessionDetail, SessionList
from app.core.logging import get_logger

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
        
        return SessionResponse.model_validate(session)

    async def get_session(
        self,
        session_id: str,
        include_details: bool = False,
    ) -> Optional[SessionResponse | SessionDetail]:
        """Get session by ID."""
        session = await self.session_repo.get_by_id(
            session_id,
            include_messages=include_details,
            include_artifacts=include_details,
        )
        
        if not session:
            return None
        
        if include_details:
            # Get message count separately for performance
            message_count = await self.session_repo.get_message_count(session_id)
            session_data = SessionDetail.model_validate(session)
            session_data.message_count = message_count
            return session_data
        
        return SessionResponse.model_validate(session)

    async def list_sessions(
        self,
        workspace_id: str,
        limit: int = 20,
        offset: int = 0,
        status: Optional[SessionStatus] = None,
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
            session_data = SessionResponse.model_validate(session)
            session_data.message_count = message_count
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
    ) -> Optional[SessionResponse]:
        """Update session."""
        updates = data.model_dump(exclude_unset=True)
        
        if not updates:
            # No updates provided, just return current
            session = await self.session_repo.get_by_id(session_id)
            return SessionResponse.model_validate(session) if session else None
        
        session = await self.session_repo.update(session_id, **updates)
        
        if session:
            logger.info(
                "session_updated",
                session_id=session_id,
                updates=list(updates.keys()),
            )
        
        return SessionResponse.model_validate(session) if session else None

    async def complete_session(
        self,
        session_id: str,
    ) -> Optional[SessionResponse]:
        """Mark session as completed."""
        from datetime import datetime
        
        session = await self.session_repo.update(
            session_id,
            status=SessionStatus.COMPLETED,
            completed_at=datetime.utcnow(),
        )
        
        if session:
            logger.info("session_completed", session_id=session_id)
        
        return SessionResponse.model_validate(session) if session else None

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
        limit: Optional[int] = None,
    ):
        """Get messages for a session."""
        from app.schemas.message import MessageResponse, MessageList
        
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
        from app.schemas.artifact import ArtifactResponse, ArtifactList
        
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
