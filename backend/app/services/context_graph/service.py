"""
ContextGraphService - 统一的 Context Graph 服务

提供:
- 内存模式 (默认，无需 Neo4j)
- Neo4j 模式 (可选，高性能持久化)
- 决策轨迹记录
- 失败信号存储和检索
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from app.core.config import settings

from ..knowledge_graph import (
    Entity,
    EntityType,
    GraphQueryEngine,
    Relation,
    RelationType,
    ResearchKnowledgeGraph,
)
from .failure_observer import FailureObserver, FailureSignal, FailureTaxonomy

logger = logging.getLogger(__name__)


class StorageMode(Enum):
    """存储模式"""
    MEMORY = "memory"  # 内存模式 (默认)
    NEO4J = "neo4j"    # Neo4j 模式


class DecisionType(Enum):
    """决策类型"""
    STATE_TRANSITION = "state_transition"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    PLAN_CREATED = "plan_created"
    PLAN_UPDATED = "plan_updated"
    USER_INPUT = "user_input"
    FAILURE = "failure"
    RECOVERY = "recovery"


@dataclass
class DecisionTrace:
    """决策轨迹记录"""
    trace_id: str
    timestamp: datetime
    decision_type: DecisionType
    task_id: str | None = None
    session_id: str | None = None

    # 状态转移相关
    from_state: str | None = None
    to_state: str | None = None
    signal: str | None = None

    # 工具调用相关
    tool_name: str | None = None
    tool_args: dict[str, Any] | None = None
    tool_result: Any = None
    exit_code: int | None = None
    duration_ms: float | None = None

    # 额外上下文
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "trace_id": self.trace_id,
            "timestamp": self.timestamp.isoformat(),
            "decision_type": self.decision_type.value,
            "task_id": self.task_id,
            "session_id": self.session_id,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "signal": self.signal,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "context": self.context,
        }


class ContextGraphService:
    """
    Context Graph 统一服务

    职责:
    1. 记录决策轨迹 (每个状态转移、工具调用)
    2. 存储和检索失败信号
    3. 提供多跳查询能力
    4. 支持内存/Neo4j 双模式
    """

    def __init__(
        self,
        mode: StorageMode = StorageMode.MEMORY,
        neo4j_uri: str | None = None,
        neo4j_user: str | None = None,
        neo4j_password: str | None = None,
    ) -> None:
        """
        初始化 Context Graph 服务

        Args:
            mode: 存储模式
            neo4j_uri: Neo4j URI (仅 NEO4J 模式)
            neo4j_user: Neo4j 用户名
            neo4j_password: Neo4j 密码
        """
        self.mode = mode
        self._neo4j_uri = neo4j_uri or settings.NEO4J_URI
        self._neo4j_user = neo4j_user or settings.NEO4J_USER
        self._neo4j_password = neo4j_password or settings.NEO4J_PASSWORD

        # 内存存储
        self._graph = ResearchKnowledgeGraph()
        self._decision_traces: list[DecisionTrace] = []
        self._failure_signals: list[FailureSignal] = []

        # 查询引擎
        self._query_engine = GraphQueryEngine(graph=self._graph)

        # Neo4j 存储 (延迟初始化)
        self._neo4j_storage: Any = None

        # 失败观测器
        self.failure_observer = FailureObserver()
        self.failure_observer.set_context_graph(self)

        # 统计
        self._stats = {
            "total_traces": 0,
            "total_failures": 0,
            "total_entities": 0,
            "total_relations": 0,
        }

        logger.info(f"ContextGraphService initialized (mode={mode.value})")

    async def initialize(self) -> None:
        """异步初始化 (连接 Neo4j 等)"""
        if self.mode == StorageMode.NEO4J:
            try:
                from ..knowledge_graph import Neo4jStorage, get_neo4j_storage

                self._neo4j_storage = await get_neo4j_storage()
                self._query_engine.neo4j_storage = self._neo4j_storage
                logger.info("Neo4j storage connected")
            except Exception as e:
                logger.warning(f"Failed to connect Neo4j, falling back to memory: {e}")
                self.mode = StorageMode.MEMORY

    async def close(self) -> None:
        """关闭连接"""
        if self._neo4j_storage:
            from ..knowledge_graph import close_neo4j_storage
            await close_neo4j_storage()
            self._neo4j_storage = None

    # ==================== 决策轨迹记录 ====================

    async def record_state_transition(
        self,
        from_state: str,
        to_state: str,
        signal: str,
        task_id: str | None = None,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> DecisionTrace:
        """
        记录状态转移

        Args:
            from_state: 源状态
            to_state: 目标状态
            signal: 触发信号
            task_id: 任务ID
            session_id: 会话ID
            context: 额外上下文

        Returns:
            DecisionTrace 记录
        """
        trace = DecisionTrace(
            trace_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            decision_type=DecisionType.STATE_TRANSITION,
            task_id=task_id,
            session_id=session_id,
            from_state=from_state,
            to_state=to_state,
            signal=signal,
            context=context or {},
        )

        await self._store_trace(trace)
        return trace

    async def record_tool_call(
        self,
        tool_name: str,
        tool_args: dict[str, Any],
        task_id: str | None = None,
        session_id: str | None = None,
        state_name: str | None = None,
    ) -> DecisionTrace:
        """
        记录工具调用开始

        Args:
            tool_name: 工具名称
            tool_args: 工具参数
            task_id: 任务ID
            session_id: 会话ID
            state_name: 当前状态

        Returns:
            DecisionTrace 记录
        """
        trace = DecisionTrace(
            trace_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            decision_type=DecisionType.TOOL_CALL,
            task_id=task_id,
            session_id=session_id,
            from_state=state_name,
            tool_name=tool_name,
            tool_args=tool_args,
        )

        await self._store_trace(trace)
        return trace

    async def record_tool_result(
        self,
        tool_name: str,
        tool_args: dict[str, Any],
        result: Any,
        exit_code: int,
        duration_ms: float,
        stdout: str = "",
        stderr: str = "",
        task_id: str | None = None,
        session_id: str | None = None,
        state_name: str | None = None,
    ) -> DecisionTrace:
        """
        记录工具执行结果

        Args:
            tool_name: 工具名称
            tool_args: 工具参数
            result: 执行结果
            exit_code: 退出码
            duration_ms: 执行时间(毫秒)
            stdout: 标准输出
            stderr: 标准错误
            task_id: 任务ID
            session_id: 会话ID
            state_name: 当前状态

        Returns:
            DecisionTrace 记录
        """
        trace = DecisionTrace(
            trace_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            decision_type=DecisionType.TOOL_RESULT,
            task_id=task_id,
            session_id=session_id,
            from_state=state_name,
            tool_name=tool_name,
            tool_args=tool_args,
            tool_result=result if exit_code == 0 else None,
            exit_code=exit_code,
            duration_ms=duration_ms,
            context={
                "stdout_preview": stdout[:200] if stdout else "",
                "stderr_preview": stderr[:200] if stderr else "",
            },
        )

        await self._store_trace(trace)

        # 如果失败，记录失败信号
        if exit_code != 0:
            from .failure_observer import create_failure_signal_from_tool_result

            failure_signal = create_failure_signal_from_tool_result(
                tool_name=tool_name,
                tool_args=tool_args,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                duration_ms=duration_ms,
                state_name=state_name,
                task_id=task_id,
                session_id=session_id,
            )
            if failure_signal:
                await self.failure_observer.observe(failure_signal)

        return trace

    async def _store_trace(self, trace: DecisionTrace) -> None:
        """存储决策轨迹"""
        # 内存存储
        self._decision_traces.append(trace)
        self._stats["total_traces"] += 1

        # 限制内存大小
        if len(self._decision_traces) > 1000:
            self._decision_traces = self._decision_traces[-500:]

        # 同时创建图实体
        await self._create_trace_entity(trace)

        # Neo4j 存储 (如果可用)
        if self._neo4j_storage:
            try:
                await self._store_trace_to_neo4j(trace)
            except Exception as e:
                logger.warning(f"Failed to store trace to Neo4j: {e}")

    async def _create_trace_entity(self, trace: DecisionTrace) -> None:
        """为决策轨迹创建图实体"""
        entity = Entity.create(
            name=f"{trace.decision_type.value}:{trace.trace_id[:8]}",
            entity_type=EntityType.EVENT,
            source_id=trace.session_id,
            trace_id=trace.trace_id,
            decision_type=trace.decision_type.value,
            timestamp=trace.timestamp.isoformat(),
            tool_name=trace.tool_name,
            exit_code=trace.exit_code,
        )
        self._graph.add_entity(entity)
        self._stats["total_entities"] += 1

    async def _store_trace_to_neo4j(self, trace: DecisionTrace) -> None:
        """存储轨迹到 Neo4j"""
        if not self._neo4j_storage:
            return

        query = """
        CREATE (t:DecisionTrace {
            trace_id: $trace_id,
            timestamp: datetime($timestamp),
            decision_type: $decision_type,
            task_id: $task_id,
            session_id: $session_id,
            from_state: $from_state,
            to_state: $to_state,
            signal: $signal,
            tool_name: $tool_name,
            exit_code: $exit_code,
            duration_ms: $duration_ms
        })
        """

        async with self._neo4j_storage._session() as session:
            await session.run(
                query,
                trace_id=trace.trace_id,
                timestamp=trace.timestamp.isoformat(),
                decision_type=trace.decision_type.value,
                task_id=trace.task_id,
                session_id=trace.session_id,
                from_state=trace.from_state,
                to_state=trace.to_state,
                signal=trace.signal,
                tool_name=trace.tool_name,
                exit_code=trace.exit_code,
                duration_ms=trace.duration_ms,
            )

    # ==================== 失败信号存储和检索 ====================

    async def record_failure(self, signal: FailureSignal) -> None:
        """
        记录失败信号

        Args:
            signal: 失败信号
        """
        self._failure_signals.append(signal)
        self._stats["total_failures"] += 1

        # 限制大小
        if len(self._failure_signals) > 500:
            self._failure_signals = self._failure_signals[-250:]

        # 创建失败实体
        entity = Entity.create(
            name=f"failure:{signal.signal_id[:8]}",
            entity_type=EntityType.EVENT,
            source_id=signal.session_id,
            signal_id=signal.signal_id,
            taxonomy=signal.taxonomy.value,
            exit_code=signal.exit_code,
            error_message=signal.error_message[:200],
            tool_name=signal.tool_name,
            learning=signal.get_learning(),
        )
        self._graph.add_entity(entity)

        # Neo4j 存储
        if self._neo4j_storage:
            await self._store_failure_to_neo4j(signal)

        logger.info(f"Failure recorded: {signal.taxonomy.value}")

    async def _store_failure_to_neo4j(self, signal: FailureSignal) -> None:
        """存储失败到 Neo4j"""
        if not self._neo4j_storage:
            return

        query = """
        CREATE (f:FailureSignal {
            signal_id: $signal_id,
            timestamp: datetime($timestamp),
            taxonomy: $taxonomy,
            exit_code: $exit_code,
            error_message: $error_message,
            tool_name: $tool_name,
            task_id: $task_id,
            session_id: $session_id,
            learning: $learning
        })
        """

        try:
            async with self._neo4j_storage._session() as session:
                await session.run(
                    query,
                    signal_id=signal.signal_id,
                    timestamp=signal.timestamp.isoformat(),
                    taxonomy=signal.taxonomy.value,
                    exit_code=signal.exit_code,
                    error_message=signal.error_message[:500],
                    tool_name=signal.tool_name,
                    task_id=signal.task_id,
                    session_id=signal.session_id,
                    learning=signal.get_learning(),
                )
        except Exception as e:
            logger.warning(f"Failed to store failure to Neo4j: {e}")

    async def retrieve_similar_failures(
        self,
        query: str,
        limit: int = 5,
    ) -> list[FailureSignal]:
        """
        检索相似失败

        Args:
            query: 查询描述
            limit: 返回数量

        Returns:
            相似的失败信号列表
        """
        # 简单的关键词匹配
        keywords = set(query.lower().split())
        scored = []

        for failure in self._failure_signals:
            # 匹配工具名、错误信息、分类
            text = f"{failure.tool_name or ''} {failure.error_message} {failure.taxonomy.value}"
            words = set(text.lower().split())
            overlap = len(keywords & words)
            if overlap > 0:
                scored.append((overlap, failure))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [f for _, f in scored[:limit]]

    # ==================== 查询接口 ====================

    def get_recent_traces(
        self,
        limit: int = 20,
        decision_type: DecisionType | None = None,
        session_id: str | None = None,
    ) -> list[DecisionTrace]:
        """
        获取最近的决策轨迹

        Args:
            limit: 返回数量
            decision_type: 过滤决策类型
            session_id: 过滤会话ID

        Returns:
            决策轨迹列表
        """
        traces = self._decision_traces

        if decision_type:
            traces = [t for t in traces if t.decision_type == decision_type]

        if session_id:
            traces = [t for t in traces if t.session_id == session_id]

        return traces[-limit:]

    def get_tool_call_history(
        self,
        tool_name: str | None = None,
        session_id: str | None = None,
        limit: int = 20,
    ) -> list[DecisionTrace]:
        """
        获取工具调用历史

        Args:
            tool_name: 过滤工具名
            session_id: 过滤会话ID
            limit: 返回数量

        Returns:
            工具调用轨迹列表
        """
        traces = [
            t for t in self._decision_traces
            if t.decision_type in [DecisionType.TOOL_CALL, DecisionType.TOOL_RESULT]
        ]

        if tool_name:
            traces = [t for t in traces if t.tool_name == tool_name]

        if session_id:
            traces = [t for t in traces if t.session_id == session_id]

        return traces[-limit:]

    def get_failure_history(
        self,
        taxonomy: FailureTaxonomy | None = None,
        session_id: str | None = None,
        limit: int = 20,
    ) -> list[FailureSignal]:
        """
        获取失败历史

        Args:
            taxonomy: 过滤失败类型
            session_id: 过滤会话ID
            limit: 返回数量

        Returns:
            失败信号列表
        """
        failures = self._failure_signals

        if taxonomy:
            failures = [f for f in failures if f.taxonomy == taxonomy]

        if session_id:
            failures = [f for f in failures if f.session_id == session_id]

        return failures[-limit:]

    # ==================== 统计和诊断 ====================

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            "mode": self.mode.value,
            "neo4j_connected": self._neo4j_storage is not None,
            "failure_observer": self.failure_observer.get_statistics(),
            "graph_stats": self._graph.get_statistics(),
        }

    def get_session_summary(self, session_id: str) -> dict[str, Any]:
        """获取会话摘要"""
        traces = [t for t in self._decision_traces if t.session_id == session_id]
        failures = [f for f in self._failure_signals if f.session_id == session_id]

        # 统计
        tool_calls = [t for t in traces if t.decision_type == DecisionType.TOOL_CALL]
        state_transitions = [
            t for t in traces if t.decision_type == DecisionType.STATE_TRANSITION
        ]

        return {
            "session_id": session_id,
            "total_traces": len(traces),
            "tool_calls": len(tool_calls),
            "state_transitions": len(state_transitions),
            "failures": len(failures),
            "failure_types": list(set(f.taxonomy.value for f in failures)),
            "unique_tools": list(set(t.tool_name for t in tool_calls if t.tool_name)),
        }

    def export_traces(self, session_id: str | None = None) -> list[dict[str, Any]]:
        """导出决策轨迹"""
        traces = self._decision_traces
        if session_id:
            traces = [t for t in traces if t.session_id == session_id]
        return [t.to_dict() for t in traces]

    def clear(self, session_id: str | None = None) -> None:
        """
        清除数据

        Args:
            session_id: 如果提供，只清除该会话的数据
        """
        if session_id:
            self._decision_traces = [
                t for t in self._decision_traces if t.session_id != session_id
            ]
            self._failure_signals = [
                f for f in self._failure_signals if f.session_id != session_id
            ]
        else:
            self._decision_traces.clear()
            self._failure_signals.clear()
            self._graph = ResearchKnowledgeGraph()
            self._query_engine.set_graph(self._graph)
            self.failure_observer.reset()
            self._stats = {
                "total_traces": 0,
                "total_failures": 0,
                "total_entities": 0,
                "total_relations": 0,
            }

        logger.info(f"Context graph cleared (session_id={session_id})")


# ==================== 单例管理 ====================

_service_instance: ContextGraphService | None = None


async def get_context_graph_service(
    mode: StorageMode | None = None,
) -> ContextGraphService:
    """
    获取 Context Graph 服务单例

    Args:
        mode: 存储模式 (首次调用时有效)

    Returns:
        ContextGraphService 实例
    """
    global _service_instance

    if _service_instance is None:
        # 从环境变量读取模式
        if mode is None:
            mode_str = settings.CONTEXT_GRAPH_MODE.lower()
            mode = StorageMode.NEO4J if mode_str == "neo4j" else StorageMode.MEMORY

        _service_instance = ContextGraphService(mode=mode)
        await _service_instance.initialize()

    return _service_instance


async def close_context_graph_service() -> None:
    """关闭 Context Graph 服务"""
    global _service_instance

    if _service_instance:
        await _service_instance.close()
        _service_instance = None
