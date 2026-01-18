"""User-related Pydantic schemas."""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""
    id: UUID
    email: str
    username: str
    display_name: str | None = None
    avatar_url: str | None = None
    auth_provider: str = "email_password"
    is_active: bool
    is_verified: bool
    email_verified: bool = False
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None
    personal_quota: dict[str, Any] | None = None
    usage_stats: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str


class RegisterResponse(BaseModel):
    """Schema for registration response."""
    user: UserResponse
    tokens: TokenResponse
    default_workspace_id: str


class LoginResponse(BaseModel):
    """Schema for login response."""
    user: UserResponse
    tokens: TokenResponse
    default_workspace_id: str | None = None
