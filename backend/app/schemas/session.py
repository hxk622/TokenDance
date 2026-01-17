"""
Session Pydantic schemas for API request/response validation.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.session import SessionStatus

# ============ Base Schemas ============

class TodoItem(BaseModel):
    """TODO item for Plan Recitation."""
    title: str
    description: str | None = None
    completed: bool = False


class SessionBase(BaseModel):
    """Base session schema."""
    title: str = Field(default="New Chat", max_length=200)


# ============ Create Schemas ============

class SessionCreate(SessionBase):
    """Schema for creating a new session."""
    workspace_id: str = Field(..., description="Workspace ID")
    skill_id: str | None = Field(None, description="Initial skill to activate")


# ============ Update Schemas ============

class SessionUpdate(BaseModel):
    """Schema for updating a session."""
    title: str | None = Field(None, max_length=200)
    status: SessionStatus | None = None
    skill_id: str | None = None
    todo_list: list[TodoItem] | None = None


class SessionStatusUpdate(BaseModel):
    """Schema for updating session status only."""
    status: SessionStatus


# ============ Response Schemas ============

class SessionResponse(SessionBase):
    """Schema for session response."""
    id: str
    workspace_id: str
    status: SessionStatus
    skill_id: str | None = None
    total_tokens_used: int = 0
    message_count: int = 0
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class SessionDetail(SessionResponse):
    """Detailed session response with context info."""
    context_summary: str | None = None
    todo_list: list[TodoItem] | None = None
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
    skill_id: str | None = None
    context_summary: str | None = None
    todo_list: list[TodoItem] | None = None
    total_tokens_used: int = 0
    extra_data: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
