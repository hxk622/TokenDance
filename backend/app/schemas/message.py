"""
Message Pydantic schemas for API request/response validation.
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.message import MessageRole


# ============ Nested Schemas ============

class ToolCall(BaseModel):
    """Tool call schema."""
    id: str
    name: str
    args: dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"  # pending, running, success, error, cancelled
    result: Optional[Any] = None
    error: Optional[str] = None


class Citation(BaseModel):
    """Citation reference schema."""
    index: int
    url: str
    title: str
    domain: Optional[str] = None
    snippet: Optional[str] = None


class Attachment(BaseModel):
    """Message attachment schema."""
    type: str  # file, image
    file_id: Optional[str] = None
    url: Optional[str] = None
    name: Optional[str] = None


# ============ Base Schemas ============

class MessageBase(BaseModel):
    """Base message schema."""
    content: Optional[str] = None


# ============ Create Schemas ============

class MessageCreate(MessageBase):
    """Schema for creating a new message (user input)."""
    content: str = Field(..., min_length=1)
    attachments: Optional[list[Attachment]] = None


class AssistantMessageCreate(MessageBase):
    """Schema for creating assistant message (internal)."""
    role: MessageRole = MessageRole.ASSISTANT
    content: Optional[str] = None
    thinking: Optional[str] = None
    tool_calls: Optional[list[ToolCall]] = None
    citations: Optional[list[Citation]] = None
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
    session_id: str
    role: MessageRole
    content: Optional[str] = None
    thinking: Optional[str] = None
    tool_calls: Optional[list[ToolCall]] = None
    citations: Optional[list[Citation]] = None
    tokens_used: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)  # 



class MessageList(BaseModel):
    """List of messages."""
    items: list[MessageResponse]
    total: int


# ============ SSE Event Schemas ============

class ThinkingEvent(BaseModel):
    """SSE event for thinking/reasoning."""
    type: str = "thinking"
    content: str
    status: Optional[str] = None  # start, end


class ToolCallEvent(BaseModel):
    """SSE event for tool call."""
    type: str = "tool_call"
    id: str
    name: str
    args: Optional[dict[str, Any]] = None
    status: str  # pending, running


class ToolResultEvent(BaseModel):
    """SSE event for tool result."""
    type: str = "tool_result"
    id: str
    status: str  # success, error, cancelled
    result: Optional[str] = None
    error: Optional[str] = None


class ContentEvent(BaseModel):
    """SSE event for content chunk."""
    type: str = "content"
    content: str
    citations: Optional[list[Citation]] = None


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
    code: Optional[str] = None


# ============ Chat Request Schemas ============

class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""
    content: str = Field(..., min_length=1)
    attachments: Optional[list[Attachment]] = None


class ConfirmRequest(BaseModel):
    """Request schema for HITL confirmation."""
    action_id: str
    confirmed: bool
