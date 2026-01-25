"""
Context Graph 与 Agent Engine 集成

提供:
- AgentEngine 与 ContextGraphService 的桥接
- 自动记录状态转移和工具调用
- 失败信号同步到 Context Graph
"""

import logging
from typing import Any

from app.agent.state import AgentState, Signal

logger = logging.getLogger(__name__)


class ContextGraphIntegration:
    """
    Context Graph 集成器

    职责:
    1. 监听 AgentEngine 的状态转移，记录到 ContextGraphService
    2. 监听工具调用，记录到 ContextGraphService
    3. 同步失败信号到 ContextGraphService
    """

    def __init__(
        self,
        task_id: str | None = None,
        session_id: str | None = None,
    ) -> None:
        """
        初始化集成器

        Args:
            task_id: 任务ID
            session_id: 会话ID
        """
        self.task_id = task_id
        self.session_id = session_id
        self._context_graph_service: Any = None
        self._initialized = False

    async def initialize(self) -> None:
        """异步初始化 ContextGraphService"""
        if self._initialized:
            return

        try:
            from app.services.context_graph import get_context_graph_service

            self._context_graph_service = await get_context_graph_service()
            self._initialized = True
            logger.info(
                f"ContextGraphIntegration initialized "
                f"(session={self.session_id}, mode={self._context_graph_service.mode.value})"
            )
        except Exception as e:
            logger.warning(f"Failed to initialize ContextGraphService: {e}")
            self._initialized = False

    @property
    def is_available(self) -> bool:
        """检查 ContextGraphService 是否可用"""
        return self._initialized and self._context_graph_service is not None

    async def on_state_transition(
        self,
        from_state: AgentState,
        to_state: AgentState,
        signal: Signal,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        处理状态转移事件

        Args:
            from_state: 源状态
            to_state: 目标状态
            signal: 触发信号
            context: 额外上下文
        """
        if not self.is_available:
            return

        try:
            await self._context_graph_service.record_state_transition(
                from_state=from_state.value,
                to_state=to_state.value,
                signal=signal.value,
                task_id=self.task_id,
                session_id=self.session_id,
                context=context,
            )
        except Exception as e:
            logger.warning(f"Failed to record state transition: {e}")

    async def on_tool_call(
        self,
        tool_name: str,
        tool_args: dict[str, Any],
        state_name: str | None = None,
    ) -> None:
        """
        处理工具调用事件

        Args:
            tool_name: 工具名称
            tool_args: 工具参数
            state_name: 当前状态名
        """
        if not self.is_available:
            return

        try:
            await self._context_graph_service.record_tool_call(
                tool_name=tool_name,
                tool_args=tool_args,
                task_id=self.task_id,
                session_id=self.session_id,
                state_name=state_name,
            )
        except Exception as e:
            logger.warning(f"Failed to record tool call: {e}")

    async def on_tool_result(
        self,
        tool_name: str,
        tool_args: dict[str, Any],
        result: Any,
        exit_code: int,
        duration_ms: float,
        stdout: str = "",
        stderr: str = "",
        state_name: str | None = None,
    ) -> None:
        """
        处理工具执行结果

        Args:
            tool_name: 工具名称
            tool_args: 工具参数
            result: 执行结果
            exit_code: 退出码
            duration_ms: 执行时间(毫秒)
            stdout: 标准输出
            stderr: 标准错误
            state_name: 当前状态名
        """
        if not self.is_available:
            return

        try:
            await self._context_graph_service.record_tool_result(
                tool_name=tool_name,
                tool_args=tool_args,
                result=result,
                exit_code=exit_code,
                duration_ms=duration_ms,
                stdout=stdout,
                stderr=stderr,
                task_id=self.task_id,
                session_id=self.session_id,
                state_name=state_name,
            )

            # 如果成功，清除连续失败计数
            if exit_code == 0:
                self._context_graph_service.failure_observer.clear_consecutive()

        except Exception as e:
            logger.warning(f"Failed to record tool result: {e}")

    def should_abort(self) -> bool:
        """
        检查是否应该中止 (3-Strike Protocol)

        Returns:
            True 如果应该中止
        """
        if not self.is_available:
            return False

        return self._context_graph_service.failure_observer.should_abort()

    def get_failure_summary(self) -> str:
        """
        获取失败摘要 (用于 Plan Recitation)

        Returns:
            失败摘要字符串
        """
        if not self.is_available:
            return ""

        return self._context_graph_service.failure_observer.get_failure_summary()

    async def get_similar_failures(self, context: str, limit: int = 5) -> list[Any]:
        """
        获取相似失败

        Args:
            context: 当前上下文
            limit: 返回数量

        Returns:
            相似失败列表
        """
        if not self.is_available:
            return []

        try:
            return await self._context_graph_service.failure_observer.get_similar_failures(
                current_context=context,
                limit=limit,
            )
        except Exception as e:
            logger.warning(f"Failed to get similar failures: {e}")
            return []

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        if not self.is_available:
            return {"available": False}

        stats = self._context_graph_service.get_statistics()
        stats["available"] = True
        return stats

    def get_session_summary(self) -> dict[str, Any]:
        """获取会话摘要"""
        if not self.is_available or not self.session_id:
            return {}

        return self._context_graph_service.get_session_summary(self.session_id)


# 工厂函数
_integration_instances: dict[str, ContextGraphIntegration] = {}


async def get_context_graph_integration(
    session_id: str,
    task_id: str | None = None,
) -> ContextGraphIntegration:
    """
    获取或创建 ContextGraphIntegration 实例

    Args:
        session_id: 会话ID
        task_id: 任务ID

    Returns:
        ContextGraphIntegration 实例
    """
    if session_id not in _integration_instances:
        integration = ContextGraphIntegration(
            task_id=task_id,
            session_id=session_id,
        )
        await integration.initialize()
        _integration_instances[session_id] = integration

    return _integration_instances[session_id]


def clear_integration(session_id: str) -> None:
    """清除指定会话的集成实例"""
    if session_id in _integration_instances:
        del _integration_instances[session_id]
