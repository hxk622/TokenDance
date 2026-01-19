"""
ResearchTask model - represents a deep research task with MinIO object references.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.workspace import Workspace


class ResearchTaskStatus(PyEnum):
    """Research task status enum.

    Status transitions:
    - PENDING: Task created, waiting to start
    - SEARCHING: Searching for sources
    - READING: Reading and analyzing sources
    - SYNTHESIZING: Synthesizing information
    - COMPLETED: Research finished successfully
    - FAILED: Research failed with error
    - CANCELLED: User cancelled the task
    """
    PENDING = "pending"
    SEARCHING = "searching"
    READING = "reading"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResearchTask(Base):
    """
    ResearchTask model - a deep research task with persistent state.

    Features:
    - Tracks research progress and status
    - Stores MinIO object keys for report artifacts
    - Links to user and workspace for multi-tenancy
    - Supports soft delete (deleted_at)
    """

    __tablename__ = "research_tasks"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Ownership
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # Basic info
    topic: Mapped[str] = mapped_column(String(500), nullable=False)

    # Status tracking
    status: Mapped[ResearchTaskStatus] = mapped_column(
        Enum(ResearchTaskStatus, values_callable=lambda x: [e.value for e in x]),
        default=ResearchTaskStatus.PENDING,
        nullable=False,
        index=True
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    phase: Mapped[str] = mapped_column(String(50), default="init", nullable=False)

    # Research metrics
    sources_collected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # MinIO object references
    report_object_key: Mapped[str | None] = mapped_column(String(200), nullable=True)
    timeline_object_key: Mapped[str | None] = mapped_column(String(200), nullable=True)
    findings_object_key: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Error tracking
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="research_tasks")
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="research_tasks")

    def __repr__(self) -> str:
        return f"<ResearchTask(id={self.id}, topic={self.topic[:50]}, status={self.status.value})>"

    @property
    def is_completed(self) -> bool:
        """Check if research is completed."""
        return self.status == ResearchTaskStatus.COMPLETED

    @property
    def is_active(self) -> bool:
        """Check if research is in progress."""
        return self.status in (
            ResearchTaskStatus.PENDING,
            ResearchTaskStatus.SEARCHING,
            ResearchTaskStatus.READING,
            ResearchTaskStatus.SYNTHESIZING,
        )

    @property
    def has_report(self) -> bool:
        """Check if report artifacts exist in MinIO."""
        return self.report_object_key is not None
