"""
Agent Engine 核心类型定义
"""
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from pydantic import BaseModel


class ActionType(str, Enum):
    """Agent 决策类型"""
    TOOL_CALL = "tool_call"
    ANSWER = "answer"
    CONFIRM_REQUIRED = "confirm_required"


class SSEEventType(str, Enum):
    """SSE 事件类型"""
    THINKING = "thinking"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    CONTENT = "content"
    CONFIRM_REQUIRED = "confirm_required"
    DONE = "done"
    ERROR = "error"


class ToolStatus(str, Enum):
    """工具执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"


# Pydantic models for API compatibility
class ToolSchema(BaseModel):
    """工具 Schema - 给 LLM 使用"""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema format


class SSEEvent(BaseModel):
    """SSE 事件"""
    type: SSEEventType
    data: Dict[str, Any]


@dataclass
class AgentAction:
    """Agent 决策结果"""
    type: ActionType
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    answer: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


@dataclass
class TodoItem:
    """TODO 项"""
    id: str
    title: str
    description: str = ""
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Plan:
    """执行计划"""
    todos: List[TodoItem]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ToolCallRecord:
    """工具调用记录"""
    id: str
    name: str
    args: Dict[str, Any]
    status: ToolStatus
    result: Optional[str] = None
    error: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
