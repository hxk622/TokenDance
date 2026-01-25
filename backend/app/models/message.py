"""
Message model - represents a single message in a session or conversation.

Supports both legacy Session-based messages and new Conversation-based messages
for backward compatibility during migration.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.session import Session


class MessageRole(PyEnum):
    """Message role enum."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class FeedbackType(PyEnum):
    """Feedback type for message actions."""
    LIKE = "like"
    DISLIKE = "dislike"


class Message(Base):
    """
    Message model - a single message in a chat session.

    Features:
    - Supports different roles (user, assistant, system, tool)
    - Stores thinking/reasoning process
    - Tracks tool calls and their results
    - Maintains citation references
    - Records token usage
    """

    __tablename__ = "messages"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Session relationship (kept for backward compatibility)
    session_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=True, index=True  # Changed to nullable for migration
    )

    # Conversation relationship (new in Project-First architecture)
    conversation_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=True, index=True
    )

    # Turn relationship (multi-turn conversation)
    turn_id: Mapped[str | None] = mapped_column(
        String(26), nullable=True, index=True
    )

    # Message content
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Agent thinking/reasoning (for assistant messages)
    thinking: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Tool calls (for assistant messages with function calls)
    # Format: [{"id": "tc_1", "name": "web_search", "args": {...}, "status": "success", "result": "..."}]
    tool_calls: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Tool call reference (for tool messages - response to a tool call)
    tool_call_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Citations (for assistant messages with references)
    # Format: [{"index": 1, "url": "...", "title": "...", "snippet": "..."}]
    citations: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Token tracking
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # For Dual Context Streams - reference to full result in file system
    full_result_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Extra data (named 'extra_data' to avoid conflict with SQLAlchemy reserved 'metadata')
    extra_data: Mapped[dict] = mapped_column(
        JSON,
        default={},
        nullable=False
    )

    # User feedback (for SFT training data collection)
    feedback: Mapped[FeedbackType | None] = mapped_column(
        Enum(FeedbackType, values_callable=lambda x: [e.value for e in x]),
        nullable=True
    )
    feedback_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # Relationships
    session: Mapped["Session"] = relationship(
        "Session",
        back_populates="messages",
        foreign_keys=[session_id]
    )
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages",
        foreign_keys=[conversation_id]
    )

    def __repr__(self) -> str:
        content_preview = (self.content[:50] + "...") if self.content and len(self.content) > 50 else self.content
        return f"<Message(id={self.id}, role={self.role.value}, content={content_preview})>"

    @property
    def is_user_message(self) -> bool:
        """Check if this is a user message."""
        return self.role == MessageRole.USER

    @property
    def is_assistant_message(self) -> bool:
        """Check if this is an assistant message."""
        return self.role == MessageRole.ASSISTANT

    @property
    def has_tool_calls(self) -> bool:
        """Check if this message has tool calls."""
        return bool(self.tool_calls)

    @property
    def has_citations(self) -> bool:
        """Check if this message has citations."""
        return bool(self.citations)

    def get_successful_tool_calls(self) -> list[dict]:
        """Get list of successful tool calls."""
        if not self.tool_calls:
            return []
        return [tc for tc in self.tool_calls if tc.get("status") == "success"]

    def get_failed_tool_calls(self) -> list[dict]:
        """Get list of failed tool calls (for Keep the Failures)."""
        if not self.tool_calls:
            return []
        return [tc for tc in self.tool_calls if tc.get("status") in ("error", "failed")]

    def to_llm_format(self) -> dict:
        """Convert message to LLM-compatible format."""
        base = {
            "role": self.role.value,
            "content": self.content or ""
        }

        # Add tool calls for assistant messages
        if self.role == MessageRole.ASSISTANT and self.tool_calls:
            base["tool_calls"] = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": tc.get("args", {})
                    }
                }
                for tc in self.tool_calls
            ]

        # Add tool_call_id for tool messages
        if self.role == MessageRole.TOOL and self.tool_call_id:
            base["tool_call_id"] = self.tool_call_id

        return base
