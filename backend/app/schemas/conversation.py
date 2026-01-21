"""
Conversation Pydantic schemas for API request/response validation.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.conversation import ConversationPurpose, ConversationStatus

# ============ Selection Context ============

class SelectionRange(BaseModel):
    """Selection range within an artifact."""
    start: int
    end: int


class SelectionContext(BaseModel):
    """Context for in-place editing with selection."""
    artifact_id: str
    selected_text: str
    selection_range: SelectionRange


# ============ Base Schemas ============

class ConversationBase(BaseModel):
    """Base conversation schema."""
    title: str = Field(default="New Conversation", max_length=200)
    purpose: ConversationPurpose = ConversationPurpose.GENERAL


# ============ Create Schemas ============

class ConversationCreate(BaseModel):
    """Schema for creating a new conversation within a project."""
    purpose: ConversationPurpose = Field(default=ConversationPurpose.GENERAL)
    title: str | None = Field(None, max_length=200)
    selection: SelectionContext | None = Field(None, description="Selection context for in-place editing")


# ============ Update Schemas ============

class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""
    title: str | None = Field(None, max_length=200)
    status: ConversationStatus | None = None
    selection_context: SelectionContext | None = None


# ============ Chat Schemas ============

class ChatMessage(BaseModel):
    """Schema for sending a chat message within a project."""
    message: str = Field(..., description="User's message")
    conversation_id: str | None = Field(None, description="Conversation ID (uses latest if not provided)")
    selection: SelectionContext | None = Field(None, description="Selection context for in-place editing")


class ChatResponse(BaseModel):
    """Schema for chat response (used for non-streaming)."""
    conversation_id: str
    message_id: str
    content: str
    thinking: str | None = None
    tool_calls: list[dict] | None = None
    artifact_changes: list[dict] | None = None
    tokens_used: int = 0


# ============ Response Schemas ============

class ConversationResponse(ConversationBase):
    """Schema for conversation response."""
    id: str
    project_id: str
    status: ConversationStatus
    tokens_used: int = 0
    message_count: int = 0
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ConversationDetail(ConversationResponse):
    """Detailed conversation response with selection context."""
    selection_context: SelectionContext | None = None
    context_summary: str | None = None


class ConversationList(BaseModel):
    """List of conversations."""
    items: list[ConversationResponse]
    total: int


# ============ Internal Schemas ============

class ConversationInDB(ConversationBase):
    """Conversation as stored in database."""
    id: str
    project_id: str
    status: ConversationStatus
    selection_context: dict | None = None
    context_summary: str | None = None
    tokens_used: int = 0
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
