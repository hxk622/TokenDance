"""
Session Pydantic schemas for API request/response validation.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.session import SessionStatus


# ============ Base Schemas ============

class TodoItem(BaseModel):
    """TODO item for Plan Recitation."""
    title: str
    description: Optional[str] = None
    completed: bool = False


class SessionBase(BaseModel):
    """Base session schema."""
    title: str = Field(default="New Chat", max_length=200)


# ============ Create Schemas ============

class SessionCreate(SessionBase):
    """Schema for creating a new session."""
    workspace_id: str = Field(..., description="Workspace ID")
    skill_id: Optional[str] = Field(None, description="Initial skill to activate")


# ============ Update Schemas ============

class SessionUpdate(BaseModel):
    """Schema for updating a session."""
    title: Optional[str] = Field(None, max_length=200)
    status: Optional[SessionStatus] = None
    skill_id: Optional[str] = None
    todo_list: Optional[list[TodoItem]] = None


class SessionStatusUpdate(BaseModel):
    """Schema for updating session status only."""
    status: SessionStatus


# ============ Response Schemas ============

class SessionResponse(SessionBase):
    """Schema for session response."""
    id: str
    workspace_id: str
    status: SessionStatus
    skill_id: Optional[str] = None
    total_tokens_used: int = 0
    message_count: int = 0
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SessionDetail(SessionResponse):
    """Detailed session response with context info."""
    context_summary: Optional[str] = None
    todo_list: Optional[list[TodoItem]] = None
    extra_data: dict = Field(default_factory=dict)


class SessionList(BaseModel):
    """Paginated list of sessions."""
    items: list[SessionResponse]
    total: int
    limit: int
    offset: int


# ============ Internal Schemas ============

class SessionInDB(SessionBase):
    """Session as stored in database."""
    id: str
    workspace_id: str
    status: SessionStatus
    skill_id: Optional[str] = None
    context_summary: Optional[str] = None
    todo_list: Optional[list[TodoItem]] = None
    total_tokens_used: int = 0
    extra_data: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
