"""
Organization model - multi-tenancy support.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.team import Team


class OrgStatus(PyEnum):
    """Organization status enum."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class Organization(Base):
    """
    Organization model - top-level entity for multi-tenancy.

    Features:
    - Resource quotas for the entire organization
    - Settings and preferences
    - Status management (active/suspended/deleted)
    """

    __tablename__ = "organizations"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)

    # Status
    status: Mapped[OrgStatus] = mapped_column(
        Enum(OrgStatus, values_callable=lambda x: [e.value for e in x]),
        default=OrgStatus.ACTIVE,
        nullable=False
    )

    # Settings
    settings: Mapped[dict] = mapped_column(
        JSON,
        default={},
        nullable=False
    )

    # Resource quotas
    max_teams: Mapped[int] = mapped_column(default=10, nullable=False)
    max_workspaces: Mapped[int] = mapped_column(default=100, nullable=False)
    max_sessions: Mapped[int] = mapped_column(default=1000, nullable=False)
    storage_quota_gb: Mapped[int] = mapped_column(default=100, nullable=False)

    # Usage tracking
    current_teams: Mapped[int] = mapped_column(default=0, nullable=False)
    current_workspaces: Mapped[int] = mapped_column(default=0, nullable=False)
    current_sessions: Mapped[int] = mapped_column(default=0, nullable=False)
    storage_used_gb: Mapped[int] = mapped_column(default=0, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    teams: Mapped[list["Team"]] = relationship(
        "Team",
        back_populates="organization",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name}, status={self.status.value})>"

    @property
    def is_active(self) -> bool:
        """Check if organization is active."""
        return self.status == OrgStatus.ACTIVE

    @property
    def is_over_quota(self) -> bool:
        """Check if organization has exceeded its quotas."""
        return (
            self.current_teams >= self.max_teams
            or self.current_workspaces >= self.max_workspaces
            or self.current_sessions >= self.max_sessions
            or self.storage_used_gb >= self.storage_quota_gb
        )

    def can_create_team(self) -> bool:
        """Check if organization can create a new team."""
        return self.current_teams < self.max_teams

    def can_create_workspace(self) -> bool:
        """Check if organization can create a new workspace."""
        return self.current_workspaces < self.max_workspaces
