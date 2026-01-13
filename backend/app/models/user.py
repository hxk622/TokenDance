"""
User model - supports Personal mode.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.workspace import Workspace


class User(Base):
    """User model for authentication and Personal mode workspace ownership."""

    __tablename__ = "users"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Authentication
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Personal quota (for Personal mode)
    personal_quota: Mapped[dict] = mapped_column(
        JSON,
        default={
            "max_workspaces": 10,
            "max_monthly_tokens": 1_000_000,
            "max_storage_gb": 10,
        },
        nullable=False,
    )

    # Usage tracking
    usage_stats: Mapped[dict] = mapped_column(
        JSON,
        default={
            "current_workspaces": 0,
            "monthly_tokens_used": 0,
            "storage_used_gb": 0,
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
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    personal_workspaces: Mapped[list["Workspace"]] = relationship(
        "Workspace",
        back_populates="owner",
        cascade="all, delete-orphan",
        overlaps="owner",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"

    @property
    def is_over_quota(self) -> bool:
        """Check if user has exceeded their Personal quota."""
        stats = self.usage_stats
        quota = self.personal_quota

        return (
            stats["current_workspaces"] >= quota["max_workspaces"]
            or stats["monthly_tokens_used"] >= quota["max_monthly_tokens"]
            or stats["storage_used_gb"] >= quota["max_storage_gb"]
        )

    def can_create_workspace(self) -> bool:
        """Check if user can create a new Personal workspace."""
        return self.usage_stats["current_workspaces"] < self.personal_quota["max_workspaces"]
