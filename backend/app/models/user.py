"""
User model - supports Personal mode, Team memberships, and multiple authentication methods.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.research_task import ResearchTask
    from app.models.team import TeamMember
    from app.models.workspace import Workspace


class AuthProvider(PyEnum):
    """Authentication provider enum."""
    EMAIL_PASSWORD = "email_password"
    WECHAT = "wechat"
    GMAIL = "gmail"


class User(Base):
    """User model for authentication and Personal mode workspace ownership."""

    __tablename__ = "users"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Basic Info
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Authentication
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    auth_provider: Mapped[str] = mapped_column(
        String(50), nullable=False, default=AuthProvider.EMAIL_PASSWORD.value
    )

    # WeChat OAuth
    wechat_openid: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True, index=True)
    wechat_unionid: Mapped[str | None] = mapped_column(String(100), nullable=True)
    wechat_nickname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    wechat_headimgurl: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Gmail OAuth
    gmail_sub: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    gmail_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gmail_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    gmail_picture: Mapped[str | None] = mapped_column(String(500), nullable=True)
    gmail_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    gmail_refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    gmail_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Account Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

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
    team_memberships: Mapped[list["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    research_tasks: Mapped[list["ResearchTask"]] = relationship(
        "ResearchTask",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, username={self.username}, auth_provider={self.auth_provider})>"

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

    @property
    def has_password_auth(self) -> bool:
        """Check if user has password authentication."""
        return self.auth_provider == AuthProvider.EMAIL_PASSWORD and self.password_hash is not None

    @property
    def has_wechat_auth(self) -> bool:
        """Check if user has WeChat authentication."""
        return self.auth_provider == AuthProvider.WECHAT and self.wechat_openid is not None

    @property
    def has_gmail_auth(self) -> bool:
        """Check if user has Gmail authentication."""
        return self.auth_provider == AuthProvider.GMAIL and self.gmail_sub is not None
