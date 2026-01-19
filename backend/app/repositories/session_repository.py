"""
Session repository - database access layer for sessions.
"""
from uuid import uuid4

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.message import Message
from app.models.session import Session, SessionStatus


class SessionRepository:
    """Repository for Session database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        workspace_id: str,
        title: str = "New Chat",
        skill_id: str | None = None,
    ) -> Session:
        """Create a new session with PENDING status."""
        session = Session(
            id=str(uuid4()),
            workspace_id=workspace_id,
            title=title,
            skill_id=skill_id,
            status=SessionStatus.PENDING,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_by_id(
        self,
        session_id: str,
        include_messages: bool = False,
        include_artifacts: bool = False,
    ) -> Session | None:
        """Get session by ID with optional eager loading."""
        query = select(Session).where(Session.id == session_id)

        # Eager load relationships if requested
        if include_messages:
            query = query.options(selectinload(Session.messages))
        if include_artifacts:
            query = query.options(selectinload(Session.artifacts))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_workspace(
        self,
        workspace_id: str,
        limit: int = 20,
        offset: int = 0,
        status: SessionStatus | None = None,
    ) -> tuple[list[Session], int]:
        """
        Get sessions by workspace with pagination.
        Returns (sessions, total_count).
        """
        # Build base query
        conditions = [Session.workspace_id == workspace_id]
        if status:
            conditions.append(Session.status == status)

        # Count query
        count_query = select(func.count()).select_from(Session).where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()

        # Data query
        query = (
            select(Session)
            .where(and_(*conditions))
            .order_by(Session.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        sessions = list(result.scalars().all())

        return sessions, total

    async def update(
        self,
        session_id: str,
        **updates,
    ) -> Session | None:
        """Update session fields."""
        session = await self.get_by_id(session_id)
        if not session:
            return None

        for key, value in updates.items():
            if hasattr(session, key) and value is not None:
                setattr(session, key, value)

        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def update_status(
        self,
        session_id: str,
        status: SessionStatus,
    ) -> Session | None:
        """Update session status."""
        return await self.update(session_id, status=status)

    async def start_session(
        self,
        session_id: str,
    ) -> Session | None:
        """Mark session as RUNNING (agent started)."""
        return await self.update(session_id, status=SessionStatus.RUNNING)

    async def complete_session(
        self,
        session_id: str,
        total_tokens_used: int | None = None,
    ) -> Session | None:
        """Mark session as COMPLETED."""
        from datetime import datetime
        updates = {
            "status": SessionStatus.COMPLETED,
            "completed_at": datetime.utcnow(),
        }
        if total_tokens_used is not None:
            updates["total_tokens_used"] = total_tokens_used
        return await self.update(session_id, **updates)

    async def fail_session(
        self,
        session_id: str,
        error_message: str | None = None,
    ) -> Session | None:
        """Mark session as FAILED."""
        from datetime import datetime
        updates = {
            "status": SessionStatus.FAILED,
            "completed_at": datetime.utcnow(),
        }
        if error_message:
            # Store error in extra_data
            session = await self.get_by_id(session_id)
            if session:
                extra = session.extra_data or {}
                extra["last_error"] = error_message
                updates["extra_data"] = extra
        return await self.update(session_id, **updates)

    async def cancel_session(
        self,
        session_id: str,
    ) -> Session | None:
        """Mark session as CANCELLED (user stopped)."""
        from datetime import datetime
        return await self.update(
            session_id,
            status=SessionStatus.CANCELLED,
            completed_at=datetime.utcnow(),
        )

    async def update_todo_list(
        self,
        session_id: str,
        todo_list: list[dict],
    ) -> Session | None:
        """Update session TODO list (for Plan Recitation)."""
        return await self.update(session_id, todo_list=todo_list)

    async def add_tokens_used(
        self,
        session_id: str,
        tokens: int,
    ) -> Session | None:
        """Add tokens to session total."""
        session = await self.get_by_id(session_id)
        if not session:
            return None

        session.total_tokens_used += tokens
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def delete(self, session_id: str) -> bool:
        """
        Delete a session.
        Messages and artifacts will be cascade deleted.
        """
        session = await self.get_by_id(session_id)
        if not session:
            return False

        await self.db.delete(session)
        await self.db.commit()
        return True

    async def get_message_count(self, session_id: str) -> int:
        """Get the number of messages in a session."""
        query = select(func.count()).select_from(Message).where(Message.session_id == session_id)
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_latest_messages(
        self,
        session_id: str,
        limit: int = 10,
    ) -> list[Message]:
        """Get the latest N messages in a session."""
        query = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        messages = list(result.scalars().all())
        return list(reversed(messages))  # Return in chronological order

    async def archive_old_sessions(
        self,
        workspace_id: str,
        days: int = 30,
    ) -> int:
        """
        Archive completed sessions older than N days.
        Returns the number of archived sessions.
        """
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query = (
            select(Session)
            .where(
                and_(
                    Session.workspace_id == workspace_id,
                    Session.status == SessionStatus.COMPLETED,
                    Session.updated_at < cutoff_date,
                )
            )
        )
        result = await self.db.execute(query)
        sessions = result.scalars().all()

        count = 0
        for session in sessions:
            session.status = SessionStatus.ARCHIVED
            count += 1

        await self.db.commit()
        return count
