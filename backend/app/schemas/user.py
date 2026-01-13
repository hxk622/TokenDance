"""User-related Pydantic schemas."""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(min_length=8, max_length=72)


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""
    id: UUID
    email: str
    username: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    personal_quota: Optional[Dict[str, Any]] = None
    usage_stats: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


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


class LoginResponse(BaseModel):
    """Schema for login response."""
    user: UserResponse
    tokens: TokenResponse
