"""
Message Pydantic schemas for API request/response validation.
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.message import MessageRole

# ============ Nested Schemas ============

class ToolCall(BaseModel):
    """Tool call schema."""
    id: str
    name: str
    args: dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"  # pending, running, success, error, cancelled
    result: Any | None = None
    error: str | None = None


class Citation(BaseModel):
    """Citation reference schema."""
    index: int
    url: str
    title: str
    domain: str | None = None
    snippet: str | None = None


class Attachment(BaseModel):
    """Message attachment schema.
    
    Supported types:
    - image: Image files (PNG, JPEG, GIF, WebP)
    - document: Document files (PDF, DOCX, XLSX, PPTX, TXT, CSV, MD)
    """
    type: str  # image, document
    file_id: str | None = None
    url: str | None = None  # base64 data URL
    name: str | None = None


# ============ Base Schemas ============

class MessageBase(BaseModel):
    """Base message schema."""
    content: str | None = None


# ============ Create Schemas ============

class MessageCreate(MessageBase):
    """Schema for creating a new message (user input)."""
    content: str = Field(..., min_length=1)
    attachments: list[Attachment] | None = None


class AssistantMessageCreate(MessageBase):
    """Schema for creating assistant message (internal)."""
    role: MessageRole = MessageRole.ASSISTANT
    content: str | None = None
    thinking: str | None = None
    tool_calls: list[ToolCall] | None = None
    citations: list[Citation] | None = None
    tokens_used: int = 0


class ToolMessageCreate(MessageBase):
    """Schema for creating tool response message (internal)."""
    role: MessageRole = MessageRole.TOOL
    content: str
    tool_call_id: str


# ============ Response Schemas ============

class MessageResponse(MessageBase):
    """Schema for message response."""
    id: str
    session_id: str | None = None  # Can be None for conversation-based messages
    role: MessageRole
    content: str | None = None
    thinking: str | None = None
    tool_calls: list[ToolCall] | None = None
    citations: list[Citation] | None = None
    tokens_used: int = 0
    feedback: str | None = None  # "like" | "dislike" | None
    feedback_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)



class MessageList(BaseModel):
    """List of messages."""
    items: list[MessageResponse]
    total: int


# ============ SSE Event Schemas ============

class ThinkingEvent(BaseModel):
    """SSE event for thinking/reasoning."""
    type: str = "thinking"
    content: str
    status: str | None = None  # start, end


class ToolCallEvent(BaseModel):
    """SSE event for tool call."""
    type: str = "tool_call"
    id: str
    name: str
    args: dict[str, Any] | None = None
    status: str  # pending, running


class ToolResultEvent(BaseModel):
    """SSE event for tool result."""
    type: str = "tool_result"
    id: str
    status: str  # success, error, cancelled
    result: str | None = None
    error: str | None = None


class ContentEvent(BaseModel):
    """SSE event for content chunk."""
    type: str = "content"
    content: str
    citations: list[Citation] | None = None


class ConfirmRequiredEvent(BaseModel):
    """SSE event for HITL confirmation."""
    type: str = "confirm_required"
    action_id: str
    tool: str
    args: dict[str, Any]
    description: str


class DoneEvent(BaseModel):
    """SSE event for completion."""
    type: str = "done"
    status: str  # completed, stopped, max_iterations_reached
    message_id: str
    tokens_used: int


class ErrorEvent(BaseModel):
    """SSE event for error."""
    type: str = "error"
    message: str
    code: str | None = None


# ============ Chat Request Schemas ============

class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""
    content: str = Field(..., min_length=1)
    attachments: list[Attachment] | None = None


class ConfirmRequest(BaseModel):
    """Request schema for HITL confirmation."""
    action_id: str
    confirmed: bool


# ============ Feedback Schemas ============

class FeedbackRequest(BaseModel):
    """Request schema for message feedback."""
    feedback: str | None = Field(
        None,
        description="Feedback type: 'like', 'dislike', or null to clear"
    )


class FeedbackResponse(BaseModel):
    """Response schema for message feedback."""
    message_id: str
    feedback: str | None
    feedback_at: datetime | None
