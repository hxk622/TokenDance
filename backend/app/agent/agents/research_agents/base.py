"""
Research Agent 基类和协议

定义:
- AgentTask: 任务数据结构
- AgentResult: 结果数据结构
- BaseResearchAgent: Agent 基类
- HandoffProtocol: Agent 间通信协议
"""

import logging
import uuid
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Agent 角色"""
    SEARCHER = "searcher"       # 搜索 Agent
    READER = "reader"           # 阅读/内容提取 Agent
    ANALYST = "analyst"         # 分析 Agent
    VERIFIER = "verifier"       # 验证 Agent
    SYNTHESIZER = "synthesizer" # 综合 Agent
    ORCHESTRATOR = "orchestrator"  # 编排 Agent


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentTask:
    """
    Agent 任务

    Attributes:
        id: 任务唯一标识
        type: 任务类型
        input_data: 输入数据
        context: 上下文信息
        priority: 优先级
        timeout: 超时时间 (秒)
        created_at: 创建时间
        parent_task_id: 父任务 ID (用于子任务)
        metadata: 额外元数据
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    input_data: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: float = 60.0
    created_at: datetime = field(default_factory=datetime.now)
    parent_task_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "input_data": self.input_data,
            "context": self.context,
            "priority": self.priority.value,
            "timeout": self.timeout,
            "created_at": self.created_at.isoformat(),
            "parent_task_id": self.parent_task_id,
            "metadata": self.metadata,
        }


@dataclass
class AgentResult:
    """
    Agent 执行结果

    Attributes:
        task_id: 对应的任务 ID
        status: 执行状态
        output_data: 输出数据
        error: 错误信息 (如果失败)
        execution_time: 执行时间 (秒)
        agent_role: 执行 Agent 的角色
        next_actions: 建议的后续动作
        confidence: 结果置信度
    """
    task_id: str
    status: TaskStatus
    output_data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    execution_time: float = 0.0
    agent_role: AgentRole | None = None
    next_actions: list[str] = field(default_factory=list)
    confidence: float = 1.0

    @property
    def is_success(self) -> bool:
        return self.status == TaskStatus.COMPLETED

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "output_data": self.output_data,
            "error": self.error,
            "execution_time": self.execution_time,
            "agent_role": self.agent_role.value if self.agent_role else None,
            "next_actions": self.next_actions,
            "confidence": self.confidence,
        }


@dataclass
class HandoffMessage:
    """
    Agent 间通信消息

    用于 Agent 之间传递任务和结果
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_agent: AgentRole = AgentRole.ORCHESTRATOR
    to_agent: AgentRole = AgentRole.SEARCHER
    message_type: str = "task"  # task, result, query, notification
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: str | None = None  # 关联 ID (用于追踪对话)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "from_agent": self.from_agent.value,
            "to_agent": self.to_agent.value,
            "message_type": self.message_type,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
        }


class BaseResearchAgent(ABC):
    """
    Research Agent 基类

    所有专业化 Agent 都继承此类
    """

    def __init__(
        self,
        role: AgentRole,
        llm_client: Any = None,
        model: str = "gpt-4o-mini",
        name: str | None = None
    ):
        """
        初始化 Agent

        Args:
            role: Agent 角色
            llm_client: LLM 客户端
            model: 使用的模型
            name: Agent 名称 (可选)
        """
        self.role = role
        self.llm_client = llm_client
        self.model = model
        self.name = name or f"{role.value}_agent"

        # 状态
        self._is_running = False
        self._current_task: AgentTask | None = None

        # 消息处理器
        self._message_handlers: dict[str, Callable] = {}

        # 能力描述 (用于 Orchestrator 路由)
        self._capabilities: list[str] = []

        logger.info(f"Initialized {self.name}")

    @property
    def capabilities(self) -> list[str]:
        """Agent 能力列表"""
        return self._capabilities

    @property
    def is_busy(self) -> bool:
        """是否正在执行任务"""
        return self._is_running

    # ==================== 抽象方法 ====================

    @abstractmethod
    async def execute(self, task: AgentTask) -> AgentResult:
        """
        执行任务 (子类必须实现)

        Args:
            task: 要执行的任务

        Returns:
            执行结果
        """
        pass

    @abstractmethod
    def can_handle(self, task: AgentTask) -> bool:
        """
        判断是否能处理某任务 (子类必须实现)

        Args:
            task: 待判断的任务

        Returns:
            是否能处理
        """
        pass

    # ==================== 公共方法 ====================

    async def run(self, task: AgentTask) -> AgentResult:
        """
        运行任务 (带状态管理和错误处理)
        """
        self._is_running = True
        self._current_task = task
        start_time = datetime.now()

        try:
            logger.info(f"{self.name} starting task {task.id}")
            result = await self.execute(task)
            result.execution_time = (datetime.now() - start_time).total_seconds()
            result.agent_role = self.role
            logger.info(f"{self.name} completed task {task.id} in {result.execution_time:.2f}s")
            return result

        except Exception as e:
            logger.error(f"{self.name} failed task {task.id}: {e}")
            return AgentResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
                agent_role=self.role,
            )

        finally:
            self._is_running = False
            self._current_task = None

    async def handle_message(self, message: HandoffMessage) -> HandoffMessage | None:
        """
        处理来自其他 Agent 的消息
        """
        handler = self._message_handlers.get(message.message_type)
        if handler:
            return await handler(message)

        logger.warning(f"{self.name} received unhandled message type: {message.message_type}")
        return None

    def register_handler(
        self,
        message_type: str,
        handler: Callable[[HandoffMessage], Awaitable[HandoffMessage | None]]
    ) -> None:
        """注册消息处理器"""
        self._message_handlers[message_type] = handler

    def get_status(self) -> dict[str, Any]:
        """获取 Agent 状态"""
        return {
            "name": self.name,
            "role": self.role.value,
            "is_busy": self._is_running,
            "current_task": self._current_task.id if self._current_task else None,
            "capabilities": self._capabilities,
        }

    # ==================== 辅助方法 ====================

    async def _call_llm(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        json_mode: bool = False
    ) -> str:
        """
        调用 LLM

        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            temperature: 温度
            max_tokens: 最大 token
            json_mode: 是否启用 JSON 模式

        Returns:
            LLM 响应文本
        """
        if not self.llm_client:
            raise ValueError(f"{self.name} has no LLM client")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = await self.llm_client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    def _create_result(
        self,
        task: AgentTask,
        status: TaskStatus,
        output_data: dict[str, Any],
        error: str | None = None,
        confidence: float = 1.0,
        next_actions: list[str] | None = None
    ) -> AgentResult:
        """创建结果的辅助方法"""
        return AgentResult(
            task_id=task.id,
            status=status,
            output_data=output_data,
            error=error,
            agent_role=self.role,
            confidence=confidence,
            next_actions=next_actions or [],
        )


# ==================== 协议定义 ====================

class HandoffProtocol:
    """
    Agent 间通信协议

    定义标准的消息类型和数据格式
    """

    # 消息类型
    MSG_TYPE_TASK = "task"              # 任务分配
    MSG_TYPE_RESULT = "result"          # 结果返回
    MSG_TYPE_QUERY = "query"            # 查询请求
    MSG_TYPE_NOTIFICATION = "notification"  # 通知
    MSG_TYPE_HANDOFF = "handoff"        # 任务移交

    @staticmethod
    def create_task_message(
        from_agent: AgentRole,
        to_agent: AgentRole,
        task: AgentTask,
        correlation_id: str | None = None
    ) -> HandoffMessage:
        """创建任务消息"""
        return HandoffMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=HandoffProtocol.MSG_TYPE_TASK,
            payload={"task": task.to_dict()},
            correlation_id=correlation_id,
        )

    @staticmethod
    def create_result_message(
        from_agent: AgentRole,
        to_agent: AgentRole,
        result: AgentResult,
        correlation_id: str | None = None
    ) -> HandoffMessage:
        """创建结果消息"""
        return HandoffMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=HandoffProtocol.MSG_TYPE_RESULT,
            payload={"result": result.to_dict()},
            correlation_id=correlation_id,
        )

    @staticmethod
    def create_query_message(
        from_agent: AgentRole,
        to_agent: AgentRole,
        query_type: str,
        query_data: dict[str, Any],
        correlation_id: str | None = None
    ) -> HandoffMessage:
        """创建查询消息"""
        return HandoffMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=HandoffProtocol.MSG_TYPE_QUERY,
            payload={
                "query_type": query_type,
                "query_data": query_data,
            },
            correlation_id=correlation_id,
        )

    @staticmethod
    def create_handoff_message(
        from_agent: AgentRole,
        to_agent: AgentRole,
        task: AgentTask,
        context: dict[str, Any],
        reason: str,
        correlation_id: str | None = None
    ) -> HandoffMessage:
        """创建任务移交消息"""
        return HandoffMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=HandoffProtocol.MSG_TYPE_HANDOFF,
            payload={
                "task": task.to_dict(),
                "context": context,
                "reason": reason,
            },
            correlation_id=correlation_id,
        )


# ==================== 任务工厂 ====================

class TaskFactory:
    """任务工厂"""

    @staticmethod
    def create_search_task(
        query: str,
        num_results: int = 10,
        search_type: str = "web",
        **kwargs
    ) -> AgentTask:
        """创建搜索任务"""
        return AgentTask(
            type="search",
            input_data={
                "query": query,
                "num_results": num_results,
                "search_type": search_type,
                **kwargs,
            },
        )

    @staticmethod
    def create_read_task(
        url: str,
        extract_type: str = "content",  # content, summary, entities
        **kwargs
    ) -> AgentTask:
        """创建阅读任务"""
        return AgentTask(
            type="read",
            input_data={
                "url": url,
                "extract_type": extract_type,
                **kwargs,
            },
        )

    @staticmethod
    def create_analyze_task(
        content: str,
        analysis_type: str = "general",  # general, comparison, trend
        question: str | None = None,
        **kwargs
    ) -> AgentTask:
        """创建分析任务"""
        return AgentTask(
            type="analyze",
            input_data={
                "content": content,
                "analysis_type": analysis_type,
                "question": question,
                **kwargs,
            },
        )

    @staticmethod
    def create_verify_task(
        claim: str,
        evidence: list[str] | None = None,
        **kwargs
    ) -> AgentTask:
        """创建验证任务"""
        return AgentTask(
            type="verify",
            input_data={
                "claim": claim,
                "evidence": evidence or [],
                **kwargs,
            },
        )

    @staticmethod
    def create_synthesize_task(
        findings: list[dict[str, Any]],
        format_type: str = "report",  # report, summary, outline
        question: str | None = None,
        **kwargs
    ) -> AgentTask:
        """创建综合任务"""
        return AgentTask(
            type="synthesize",
            input_data={
                "findings": findings,
                "format_type": format_type,
                "question": question,
                **kwargs,
            },
        )
