"""
Conversation model - represents a multi-turn interaction within a Project.

In the Project-First architecture, Conversation is a child of Project,
not a top-level entity. It represents one conversation thread within
a project, focused on a specific purpose (initial draft, refinement, etc.)
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.datetime_utils import utc_now_naive

if TYPE_CHECKING:
    from app.models.message import Message
    from app.models.project import Project
    from app.models.turn import Turn


class ConversationStatus(PyEnum):
    """Conversation status enum.

    Simplified compared to Session status:
    - ACTIVE: Conversation is ongoing
    - COMPLETED: Conversation finished
    """
    ACTIVE = "active"
    COMPLETED = "completed"


class ConversationPurpose(PyEnum):
    """Purpose of the conversation within a project.

    Helps categorize what the user is trying to achieve:
    - GENERAL: General discussion or questions
    - INITIAL_DRAFT: Creating the initial artifact
    - REFINEMENT: Refining/editing existing artifact
    - REVIEW: Reviewing and providing feedback
    - EXPORT: Preparing for export/delivery
    """
    GENERAL = "general"
    INITIAL_DRAFT = "initial_draft"
    REFINEMENT = "refinement"
    REVIEW = "review"
    EXPORT = "export"


class ConversationType(PyEnum):
    """Type of conversation (legacy compatibility).

    Note: This enum is maintained for backward compatibility.
    For new code, consider using ConversationPurpose instead.
    """
    CHAT = "chat"
    RESEARCH = "research"
    TASK = "task"


class Conversation(Base):
    """
    Conversation model - a multi-turn interaction within a Project.

    Features:
    - Linked to a Project (not standalone)
    - Purpose-driven (initial_draft, refinement, etc.)
    - Supports selection context for in-place editing
    - Tracks token usage per conversation
    """

    __tablename__ = "conversations"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Project relationship (core change from Session)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # Session relationship - links to execution session for SSE streaming
    # When a conversation is active, it has a corresponding session for agent execution
    current_session_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("sessions.id", ondelete="SET NULL"),
        nullable=True, index=True
    )

    # Basic info
    title: Mapped[str] = mapped_column(String(200), default="New Conversation", nullable=False)

    # Purpose
    purpose: Mapped[ConversationPurpose] = mapped_column(
        Enum(ConversationPurpose, values_callable=lambda x: [e.value for e in x]),
        default=ConversationPurpose.GENERAL,
        nullable=False
    )

    # Status (simplified)
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus, values_callable=lambda x: [e.value for e in x]),
        default=ConversationStatus.ACTIVE,
        nullable=False
    )

    # Selection context for in-place editing
    selection_context: Mapped[dict | None] = mapped_column(
        JSON,
        default=None,
        nullable=True
    )
    # Structure of selection_context:
    # {
    #     "artifact_id": "uuid",
    #     "selected_text": "the text user selected",
    #     "selection_range": {"start": 0, "end": 100}
    # }

    # Context summary (for compression)
    context_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Token tracking
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Extra data for migration tracking and extensibility
    extra_data: Mapped[dict] = mapped_column(
        JSON,
        default=dict,  # Use callable to avoid mutable default bug
        nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now_naive, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now_naive, onupdate=utc_now_naive, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )
    turns: Mapped[list["Turn"]] = relationship(
        "Turn",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Turn.turn_number"
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, purpose={self.purpose.value}, status={self.status.value})>"

    @property
    def is_active(self) -> bool:
        """Check if conversation is active."""
        return self.status == ConversationStatus.ACTIVE

    @property
    def is_completed(self) -> bool:
        """Check if conversation is completed."""
        return self.status == ConversationStatus.COMPLETED

    @property
    def message_count(self) -> int:
        """Get the number of messages in this conversation."""
        return len(self.messages) if self.messages else 0

    @property
    def has_selection(self) -> bool:
        """Check if this conversation has a selection context."""
        return self.selection_context is not None and bool(self.selection_context.get("artifact_id"))

    def set_selection(
        self,
        artifact_id: str,
        selected_text: str,
        start: int,
        end: int
    ) -> None:
        """Set the selection context for in-place editing."""
        self.selection_context = {
            "artifact_id": artifact_id,
            "selected_text": selected_text,
            "selection_range": {"start": start, "end": end}
        }

    def clear_selection(self) -> None:
        """Clear the selection context."""
        self.selection_context = None

    def complete(self) -> None:
        """Mark conversation as completed."""
        self.status = ConversationStatus.COMPLETED
        self.completed_at = utc_now_naive()
