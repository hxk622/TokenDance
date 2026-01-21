"""
Agent Engine 核心类型定义
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

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

    # Timeline 事件 (时光长廊)
    TIMELINE_SEARCH = "timeline_search"
    TIMELINE_READ = "timeline_read"
    TIMELINE_SCREENSHOT = "timeline_screenshot"
    TIMELINE_FINDING = "timeline_finding"
    TIMELINE_MILESTONE = "timeline_milestone"

    # Research Progress 事件 (研究进度透明化)
    RESEARCH_PHASE_CHANGE = "research.phase.change"      # 阶段切换
    RESEARCH_QUERY_START = "research.query.start"        # 搜索开始
    RESEARCH_QUERY_RESULT = "research.query.result"      # 搜索结果
    RESEARCH_SOURCE_START = "research.source.start"      # 来源阅读开始
    RESEARCH_SOURCE_DONE = "research.source.done"        # 来源阅读完成
    RESEARCH_SOURCE_SKIP = "research.source.skip"        # 来源跳过
    RESEARCH_FACT_EXTRACTED = "research.fact.extracted"  # 事实提取
    RESEARCH_PROGRESS_UPDATE = "research.progress.update" # 进度更新


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
    parameters: dict[str, Any]  # JSON Schema format


class SSEEvent(BaseModel):
    """SSE 事件"""
    type: SSEEventType
    data: dict[str, Any]


@dataclass
class AgentAction:
    """Agent 决策结果"""
    type: ActionType
    tool_name: str | None = None
    tool_args: dict[str, Any] | None = None
    tool_call_id: str | None = None  # LLM 返回的工具调用 ID
    answer: str | None = None
    data: dict[str, Any] | None = None


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
    todos: list[TodoItem]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ToolCallRecord:
    """工具调用记录"""
    id: str
    name: str
    args: dict[str, Any]
    status: ToolStatus
    result: str | None = None
    error: str | None = None
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
