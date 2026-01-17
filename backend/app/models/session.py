"""
Session model - represents a chat conversation within a workspace.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.agent_config import AgentConfig
    from app.models.agent_state import AgentState
    from app.models.artifact import Artifact
    from app.models.message import Message
    from app.models.workspace import Workspace


class SessionStatus(PyEnum):
    """Session status enum."""
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class Session(Base):
    """
    Session model - a chat conversation within a workspace.

    Features:
    - Linked to a workspace
    - Tracks current skill activation
    - Maintains TODO list for Plan Recitation
    - Stores context summary for compression
    """

    __tablename__ = "sessions"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Workspace relationship
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # Agent configuration
    agent_config_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("agent_configs.id", ondelete="SET NULL"),
        nullable=True, index=True
    )

    # Basic info
    title: Mapped[str] = mapped_column(String(200), default="New Chat", nullable=False)

    # Status
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus), default=SessionStatus.ACTIVE, nullable=False
    )

    # Skill tracking
    skill_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Context management
    context_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Plan Recitation - TODO list for the session
    todo_list: Mapped[list | None] = mapped_column(
        JSON,
        default=None,
        nullable=True
    )

    # Token tracking
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Extra data (named 'extra_data' to avoid conflict with SQLAlchemy reserved 'metadata')
    extra_data: Mapped[dict] = mapped_column(
        JSON,
        default={},
        nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="sessions")
    agent_config: Mapped["AgentConfig"] = relationship("AgentConfig", back_populates="sessions")
    agent_state: Mapped["AgentState"] = relationship("AgentState", back_populates="session", uselist=False)
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )
    artifacts: Mapped[list["Artifact"]] = relationship(
        "Artifact",
        back_populates="session",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, title={self.title}, status={self.status.value})>"

    @property
    def is_active(self) -> bool:
        """Check if session is active."""
        return self.status == SessionStatus.ACTIVE

    @property
    def message_count(self) -> int:
        """Get the number of messages in this session."""
        return len(self.messages) if self.messages else 0

    def get_pending_todos(self) -> list[dict]:
        """Get pending TODO items for Plan Recitation."""
        if not self.todo_list:
            return []
        return [todo for todo in self.todo_list if not todo.get("completed", False)]

    def update_todo(self, todo_index: int, completed: bool = True) -> None:
        """Update a TODO item's completion status."""
        if self.todo_list and 0 <= todo_index < len(self.todo_list):
            self.todo_list[todo_index]["completed"] = completed
