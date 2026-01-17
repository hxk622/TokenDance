"""
Team model - multi-tenancy support.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class MemberRole(PyEnum):
    """Member role enum."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class Team(Base):
    """
    Team model - middle-level entity for multi-tenancy.

    Features:
    - Belongs to an organization
    - Has members with roles
    - Can have multiple workspaces
    """

    __tablename__ = "teams"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Organization relationship
    org_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Settings
    settings: Mapped[dict] = mapped_column(
        JSON,
        default={},
        nullable=False
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="teams")
    members: Mapped[list["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="team",
        cascade="all, delete-orphan"
    )

    # Unique constraints
    __table_args__ = (
        UniqueConstraint(
            "org_id",
            "slug",
            name="uq_team_slug",
        ),
    )

    def __repr__(self) -> str:
        return f"<Team(id={self.id}, name={self.name}, org_id={self.org_id})>"


class TeamMember(Base):
    """
    TeamMember model - represents a user's membership in a team.

    Features:
    - Links user to team
    - Defines role and permissions
    """

    __tablename__ = "team_members"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Team relationship
    team_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # User relationship
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # Role and permissions
    role: Mapped[MemberRole] = mapped_column(
        Enum(MemberRole), default=MemberRole.MEMBER, nullable=False
    )
    permissions: Mapped[list[str]] = mapped_column(
        JSON,
        default=[],
        nullable=False
    )

    # Timestamps
    joined_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    team: Mapped["Team"] = relationship("Team", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="team_memberships")

    # Unique constraints
    __table_args__ = (
        UniqueConstraint(
            "team_id",
            "user_id",
            name="uq_team_member",
        ),
    )

    def __repr__(self) -> str:
        return f"<TeamMember(id={self.id}, team_id={self.team_id}, user_id={self.user_id}, role={self.role.value})>"

    @property
    def is_owner(self) -> bool:
        """Check if member is owner."""
        return self.role == MemberRole.OWNER

    @property
    def is_admin(self) -> bool:
        """Check if member is admin or owner."""
        return self.role in [MemberRole.OWNER, MemberRole.ADMIN]

    def has_permission(self, permission: str) -> bool:
        """Check if member has a specific permission."""
        if self.is_owner:
            return True
        return permission in self.permissions
