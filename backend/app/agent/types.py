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


class ExecutionMode(str, Enum):
    """执行模式

    用于统一入口 execute() 方法选择执行策略
    """
    AUTO = "auto"          # 自动选择 (根据任务复杂度)
    DIRECT = "direct"      # 直接执行 (单 Task，无 Planning)
    PLANNING = "planning"  # 计划执行 (多 Task DAG)


class SSEEventType(str, Enum):
    """SSE 事件类型"""
    THINKING = "thinking"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    TOOL_ERROR = "tool_error"      # 工具执行错误
    CONTENT = "content"
    CONFIRM_REQUIRED = "confirm_required"
    STATUS = "status"              # 状态信息
    DONE = "done"
    ERROR = "error"

    # ========== Plan 事件 (与前端 WorkflowGraph 同步) ==========
    PLAN_CREATED = "plan.created"          # Plan 创建，推送整个 DAG
    PLAN_REVISED = "plan.revised"          # Plan 重规划，推送新 DAG
    TASK_UPDATE = "task.update"            # 单个 Task 状态变更
    TASK_START = "task.start"              # Task 开始执行
    TASK_COMPLETE = "task.complete"        # Task 执行完成
    TASK_FAILED = "task.failed"            # Task 执行失败

    # ========== Validation events (LLM-as-a-Judge) ==========
    VALIDATION_START = "validation.start"      # 验证开始
    VALIDATION_RESULT = "validation.result"    # 验证结果
    VALIDATION_RETRY = "validation.retry"      # 验证失败触发重试

    # ========== Answer events (AnswerAgent) ==========
    ANSWER_GENERATING = "answer.generating"    # 正在生成答案
    ANSWER_READY = "answer.ready"              # 答案已就绪

    # Timeline 事件 (时光长廊)
    TIMELINE_SEARCH = "timeline_search"
    TIMELINE_READ = "timeline_read"
    TIMELINE_SCREENSHOT = "timeline_screenshot"
    TIMELINE_FINDING = "timeline_finding"
    TIMELINE_MILESTONE = "timeline_milestone"

    # Reasoning Trace 事件 (推理可视化)
    REASONING_DECISION = "reasoning.decision"            # AI 决策点
    REASONING_ALTERNATIVE = "reasoning.alternative"      # 备选方案
    REASONING_EVIDENCE = "reasoning.evidence"            # 支撑证据

    # Research Progress 事件 (研究进度透明化)
    RESEARCH_PHASE_CHANGE = "research.phase.change"      # 阶段切换
    RESEARCH_QUERY_START = "research.query.start"        # 搜索开始
    RESEARCH_QUERY_RESULT = "research.query.result"      # 搜索结果
    RESEARCH_SOURCE_START = "research.source.start"      # 来源阅读开始
    RESEARCH_SOURCE_DONE = "research.source.done"        # 来源阅读完成
    RESEARCH_SOURCE_SKIP = "research.source.skip"        # 来源跳过
    RESEARCH_FACT_EXTRACTED = "research.fact.extracted"  # 事实提取
    RESEARCH_PROGRESS_UPDATE = "research.progress.update" # 进度更新
    RESEARCH_REPORT_READY = "research.report.ready"      # 报告生成完成(带引用)

    # Diagram 事件 (draw.io 图表生成)
    DIAGRAM_GENERATED = "diagram.generated"              # 图表生成完成

    # Knowledge Graph 事件 (知识图谱生成)
    KNOWLEDGE_GRAPH_GENERATED = "knowledge_graph.generated"  # 知识图谱生成完成

    # Agent Thinking 事件 (DeepSeek R1 等模型的 reasoning 过程)
    AGENT_THINKING = "agent.thinking"  # LLM 推理过程


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
    thinking: str | None = None  # DeepSeek R1 等模型的 reasoning/thinking 内容


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


class ContextBlockStatus(str, Enum):
    """Context Block 状态"""
    ACTIVE = "active"          # 活跃，正常参与 Context
    RETAINED = "retained"      # 被 Agent 标记为重要，优先保留
    SUMMARIZED = "summarized"  # 已被压缩，原始内容可恢复
    DELETED = "deleted"        # 已删除（软删除，24h 内可恢复）
    PINNED = "pinned"          # 已固定到长期记忆


@dataclass
class ContextBlock:
    """Context 内容块 (MemAct Memory-as-Action)

    每个消息/工具结果/摘要都是一个 Block，Agent 可通过 block_id 引用和操作。
    这是 MemAct 框架的核心数据结构，让 Agent 可以主动管理自己的 Context。
    """
    block_id: str                              # 唯一标识 (e.g., "b_001", "b_002")
    content: str                               # 内容
    block_type: str                            # 类型: user_message, assistant_message, tool_result, summary
    token_count: int = 0                       # Token 数（估算）
    importance: float = 0.5                    # 重要性 (0-1)，影响压缩决策
    status: ContextBlockStatus = ContextBlockStatus.ACTIVE

    # 元数据
    source_block_ids: list[str] = field(default_factory=list)  # 如果是 summary，记录原始 block IDs
    metadata: dict[str, Any] = field(default_factory=dict)     # 扩展字段

    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    deleted_at: datetime | None = None        # 软删除时间

    def estimate_tokens(self) -> int:
        """估算 token 数"""
        # 粗略估算：中文约 2 字符/token，英文约 4 字符/token
        return len(self.content) // 3

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "block_id": self.block_id,
            "content": self.content,
            "block_type": self.block_type,
            "token_count": self.token_count,
            "importance": self.importance,
            "status": self.status.value,
            "source_block_ids": self.source_block_ids,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class CitationSource:
    """引用来源"""
    url: str
    title: str
    domain: str
    publish_date: str | None = None
    credibility: int = 50  # 0-100
    source_type: str = "unknown"  # academic, report, news, blog, official


@dataclass
class Citation:
    """引用详情"""
    id: int  # 引用序号 (1, 2, 3...)
    source: CitationSource
    excerpt: str  # 原文摘录
    excerpt_context: str = ""  # 更大范围的上下文
    claim_text: str = ""  # 报告中引用此来源的文本

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "source": {
                "url": self.source.url,
                "title": self.source.title,
                "domain": self.source.domain,
                "publishDate": self.source.publish_date,
                "credibility": self.source.credibility,
                "credibilityLevel": self._get_credibility_level(),
                "type": self.source.source_type,
            },
            "excerpt": self.excerpt,
            "excerptContext": self.excerpt_context,
            "claimText": self.claim_text,
        }

    def _get_credibility_level(self) -> str:
        """获取可信度等级"""
        if self.source.credibility >= 95:
            return "authoritative"
        if self.source.credibility >= 70:
            return "reliable"
        if self.source.credibility >= 40:
            return "moderate"
        return "questionable"
