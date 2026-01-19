"""
Workspace model - currently supports Personal mode only.
Team mode will be added in Phase 3.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.agent_config import AgentConfig
    from app.models.session import Session
    from app.models.user import User


class WorkspaceType(PyEnum):
    """Workspace type enum."""

    PERSONAL = "personal"
    TEAM = "team"  # Will be implemented in Phase 3


class Workspace(Base):
    """
    Workspace model - unified for both Personal and Team modes.

    For Phase 1 (MVP), only Personal mode is implemented:
    - workspace_type = PERSONAL
    - team_id = None
    - owner_id = current user
    """

    __tablename__ = "workspaces"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Type and ownership
    workspace_type: Mapped[WorkspaceType] = mapped_column(
        Enum(WorkspaceType, values_callable=lambda x: [e.value for e in x]),
        default=WorkspaceType.PERSONAL,
        nullable=False
    )
    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    team_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True  # NULL for Personal mode
    )

    # FileSystem path (physical isolation)
    # Personal: /data/users/{user_id}/workspaces/{workspace_id}/
    # Team: /data/orgs/{org_id}/teams/{team_id}/workspaces/{workspace_id}/
    filesystem_path: Mapped[str] = mapped_column(String(500), nullable=False)

    # Settings
    settings: Mapped[dict] = mapped_column(
        JSON,
        default={
            "llm_model": "claude-3-5-sonnet-20241022",
            "enable_auto_save": True,
            "max_context_tokens": 128000,
            "compression_threshold": 10240,  # 10KB
        },
        nullable=False,
    )

    # Statistics
    stats: Mapped[dict] = mapped_column(
        JSON,
        default={
            "total_tasks": 0,
            "completed_tasks": 0,
            "active_agents": 0,
            "storage_used_mb": 0,
            "monthly_tokens_used": 0,
        },
        nullable=False,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="personal_workspaces")
    sessions: Mapped[list["Session"]] = relationship(
        "Session",
        back_populates="workspace",
        cascade="all, delete-orphan"
    )
    agent_configs: Mapped[list["AgentConfig"]] = relationship(
        "AgentConfig",
        back_populates="workspace",
        cascade="all, delete-orphan"
    )

    # Unique constraints
    __table_args__ = (
        # Personal mode: owner_id + slug must be unique (when team_id is NULL)
        UniqueConstraint(
            "owner_id",
            "slug",
            name="uq_personal_workspace_slug",
            # Note: This constraint applies when team_id IS NULL
            # PostgreSQL partial unique index will be added in migration
        ),
    )

    def __repr__(self) -> str:
        return f"<Workspace(id={self.id}, name={self.name}, type={self.workspace_type.value})>"

    @property
    def is_personal(self) -> bool:
        """Check if this is a Personal workspace."""
        return self.workspace_type == WorkspaceType.PERSONAL and self.team_id is None

    @property
    def is_team(self) -> bool:
        """Check if this is a Team workspace."""
        return self.workspace_type == WorkspaceType.TEAM and self.team_id is not None
