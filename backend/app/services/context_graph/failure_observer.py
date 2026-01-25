"""
FailureObserver - 失败信号系统

实现 Agent Runtime 铁律四：智能来自失败，不来自理解
exit code 是最诚实的老师，让失败可被观测。
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class FailureTaxonomy(Enum):
    """失败类型分类 - 用于精准重试策略"""

    # 工具执行失败
    TOOL_EXECUTION_ERROR = "tool_execution_error"
    TOOL_TIMEOUT = "tool_timeout"
    TOOL_PERMISSION_DENIED = "tool_permission_denied"

    # 定位/选择失败
    SELECTION_MISS = "selection_miss"  # 找不到目标文件/函数
    PATCH_CONFLICT = "patch_conflict"  # 代码补丁冲突

    # 验证失败
    TEST_FAIL = "test_fail"
    LINT_FAIL = "lint_fail"
    TYPE_CHECK_FAIL = "type_check_fail"

    # 网络/外部服务
    NETWORK_UNREACHABLE = "network_unreachable"
    API_RATE_LIMITED = "api_rate_limited"
    API_ERROR = "api_error"

    # 资源限制
    CONTEXT_OVERFLOW = "context_overflow"
    BUDGET_EXCEEDED = "budget_exceeded"
    MAX_RETRIES_REACHED = "max_retries_reached"

    # 用户相关
    USER_REJECTED = "user_rejected"
    USER_CANCELLED = "user_cancelled"

    # 未知
    UNKNOWN = "unknown"


@dataclass
class RecoveryStrategy:
    """恢复策略"""

    action: str  # "retry" | "replan" | "expand_context" | "rollback" | "escalate" | "abort"
    suggestion: str  # 人类可读的建议
    params: dict[str, Any] = field(default_factory=dict)  # 策略参数

    @classmethod
    def retry(cls, delay_seconds: float = 1.0) -> "RecoveryStrategy":
        return cls(
            action="retry",
            suggestion="简单重试，可能是临时问题",
            params={"delay_seconds": delay_seconds},
        )

    @classmethod
    def replan(cls, reason: str) -> "RecoveryStrategy":
        return cls(
            action="replan",
            suggestion=f"需要重新规划: {reason}",
            params={"reason": reason},
        )

    @classmethod
    def expand_context(cls, window_size: int = 20) -> "RecoveryStrategy":
        return cls(
            action="expand_context",
            suggestion="扩大上下文窗口重新定位",
            params={"window_size": window_size},
        )

    @classmethod
    def rollback(cls, checkpoint_id: str) -> "RecoveryStrategy":
        return cls(
            action="rollback",
            suggestion="回滚到上一个成功的检查点",
            params={"checkpoint_id": checkpoint_id},
        )

    @classmethod
    def escalate(cls, reason: str) -> "RecoveryStrategy":
        return cls(
            action="escalate",
            suggestion=f"需要用户介入: {reason}",
            params={"reason": reason},
        )

    @classmethod
    def abort(cls, reason: str) -> "RecoveryStrategy":
        return cls(
            action="abort",
            suggestion=f"放弃任务: {reason}",
            params={"reason": reason},
        )


@dataclass
class FailureSignal:
    """
    失败信号 - 让失败可被观测

    核心字段：exit_code 是最诚实的反馈
    """

    # 信号标识
    signal_id: str
    timestamp: datetime

    # 来源信息
    source: str  # "tool" | "validation" | "timeout" | "user" | "system"
    tool_name: str | None = None
    tool_args: dict[str, Any] | None = None

    # 失败分类
    taxonomy: FailureTaxonomy = FailureTaxonomy.UNKNOWN

    # 关键：exit_code
    exit_code: int = 1  # 0=成功, 非0=失败

    # 错误详情
    error_message: str = ""
    stderr: str = ""
    stack_trace: str | None = None

    # 上下文
    state_name: str | None = None  # 发生时的状态
    task_id: str | None = None
    session_id: str | None = None

    # 恢复相关
    retry_count: int = 0
    is_retryable: bool = True
    recovery_strategy: RecoveryStrategy | None = None

    def get_learning(self) -> str:
        """从失败中提取教训"""
        learnings = {
            FailureTaxonomy.TOOL_TIMEOUT: "操作超时，考虑增加超时时间或优化操作",
            FailureTaxonomy.TOOL_PERMISSION_DENIED: "权限不足，检查文件/API权限",
            FailureTaxonomy.SELECTION_MISS: "定位失败，扩大搜索范围或检查路径",
            FailureTaxonomy.PATCH_CONFLICT: "代码冲突，需要 rebase 或手动合并",
            FailureTaxonomy.TEST_FAIL: "测试失败，检查实现逻辑或测试预期",
            FailureTaxonomy.LINT_FAIL: "代码风格问题，运行 auto-fix",
            FailureTaxonomy.TYPE_CHECK_FAIL: "类型错误，检查类型注解",
            FailureTaxonomy.NETWORK_UNREACHABLE: "网络不可达，检查连接或稍后重试",
            FailureTaxonomy.API_RATE_LIMITED: "API 限流，等待后重试",
            FailureTaxonomy.CONTEXT_OVERFLOW: "上下文溢出，需要压缩或分批处理",
            FailureTaxonomy.BUDGET_EXCEEDED: "预算超限，需要用户确认继续",
            FailureTaxonomy.MAX_RETRIES_REACHED: "达到最大重试次数，需要重新规划",
            FailureTaxonomy.USER_REJECTED: "用户拒绝，调整方案后重试",
        }
        return learnings.get(self.taxonomy, f"执行失败: {self.error_message}")

    def get_recovery_strategy(self) -> RecoveryStrategy:
        """获取推荐的恢复策略"""
        if self.recovery_strategy:
            return self.recovery_strategy

        strategies = {
            FailureTaxonomy.TOOL_TIMEOUT: RecoveryStrategy.retry(delay_seconds=2.0),
            FailureTaxonomy.TOOL_PERMISSION_DENIED: RecoveryStrategy.escalate("需要授权"),
            FailureTaxonomy.SELECTION_MISS: RecoveryStrategy.expand_context(window_size=30),
            FailureTaxonomy.PATCH_CONFLICT: RecoveryStrategy.replan("代码冲突需要手动解决"),
            FailureTaxonomy.TEST_FAIL: RecoveryStrategy.replan("测试失败，需要修改实现"),
            FailureTaxonomy.LINT_FAIL: RecoveryStrategy.retry(),
            FailureTaxonomy.TYPE_CHECK_FAIL: RecoveryStrategy.replan("类型错误需要修复"),
            FailureTaxonomy.NETWORK_UNREACHABLE: RecoveryStrategy.retry(delay_seconds=5.0),
            FailureTaxonomy.API_RATE_LIMITED: RecoveryStrategy.retry(delay_seconds=60.0),
            FailureTaxonomy.CONTEXT_OVERFLOW: RecoveryStrategy.replan("需要压缩上下文"),
            FailureTaxonomy.BUDGET_EXCEEDED: RecoveryStrategy.escalate("预算超限"),
            FailureTaxonomy.MAX_RETRIES_REACHED: RecoveryStrategy.abort("达到最大重试次数"),
            FailureTaxonomy.USER_REJECTED: RecoveryStrategy.replan("用户拒绝当前方案"),
            FailureTaxonomy.USER_CANCELLED: RecoveryStrategy.abort("用户取消"),
        }
        return strategies.get(self.taxonomy, RecoveryStrategy.retry())

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "signal_id": self.signal_id,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "taxonomy": self.taxonomy.value,
            "exit_code": self.exit_code,
            "error_message": self.error_message,
            "stderr": self.stderr[:500] if self.stderr else "",  # 截断
            "state_name": self.state_name,
            "task_id": self.task_id,
            "session_id": self.session_id,
            "retry_count": self.retry_count,
            "is_retryable": self.is_retryable,
            "learning": self.get_learning(),
        }


class FailureObserver:
    """
    失败观测器 - 收集和分析失败信号

    核心职责:
    1. 观测和记录失败信号
    2. 检测失败模式 (3-Strike Protocol)
    3. 检索相似历史失败
    4. 推荐恢复策略
    """

    # 3-Strike Protocol: 连续3次相同失败则升级
    STRIKE_THRESHOLD = 3

    def __init__(self, max_history: int = 100) -> None:
        """
        初始化失败观测器

        Args:
            max_history: 最大历史记录数
        """
        self.failure_history: list[FailureSignal] = []
        self.max_history = max_history

        # 失败计数器 (按类型)
        self._failure_counts: dict[FailureTaxonomy, int] = {}

        # 连续失败计数
        self._consecutive_failures: list[FailureSignal] = []

        # Context Graph 引用 (稍后注入)
        self._context_graph: Any = None

    def set_context_graph(self, context_graph: Any) -> None:
        """注入 Context Graph 引用"""
        self._context_graph = context_graph

    async def observe(self, signal: FailureSignal) -> None:
        """
        观测失败信号

        Args:
            signal: 失败信号
        """
        # 1. 记录到历史
        self.failure_history.append(signal)

        # 限制历史大小
        if len(self.failure_history) > self.max_history:
            self.failure_history = self.failure_history[-self.max_history :]

        # 2. 更新失败计数
        self._failure_counts[signal.taxonomy] = (
            self._failure_counts.get(signal.taxonomy, 0) + 1
        )

        # 3. 更新连续失败
        if self._consecutive_failures:
            last = self._consecutive_failures[-1]
            if last.taxonomy == signal.taxonomy:
                self._consecutive_failures.append(signal)
            else:
                self._consecutive_failures = [signal]
        else:
            self._consecutive_failures = [signal]

        # 4. 记录到 Context Graph (如果可用)
        if self._context_graph:
            await self._record_to_context_graph(signal)

        logger.warning(
            f"Failure observed: {signal.taxonomy.value} "
            f"(exit_code={signal.exit_code}, retry={signal.retry_count})"
        )

    async def _record_to_context_graph(self, signal: FailureSignal) -> None:
        """记录失败到 Context Graph"""
        try:
            await self._context_graph.record_failure(signal)
        except Exception as e:
            logger.error(f"Failed to record failure to context graph: {e}")

    def should_abort(self) -> bool:
        """
        判断是否应该放弃 (3-Strike Protocol)

        Returns:
            True 如果连续3次相同类型失败
        """
        if len(self._consecutive_failures) >= self.STRIKE_THRESHOLD:
            return True
        return False

    def get_consecutive_failure_type(self) -> FailureTaxonomy | None:
        """获取连续失败的类型"""
        if len(self._consecutive_failures) >= self.STRIKE_THRESHOLD:
            return self._consecutive_failures[0].taxonomy
        return None

    async def get_similar_failures(
        self,
        current_context: str,
        limit: int = 5,
    ) -> list[FailureSignal]:
        """
        获取相似的历史失败

        Args:
            current_context: 当前上下文描述
            limit: 返回数量限制

        Returns:
            相似的历史失败列表
        """
        # 1. 优先从 Context Graph 检索
        if self._context_graph:
            try:
                similar = await self._context_graph.retrieve_similar_failures(
                    query=current_context,
                    limit=limit,
                )
                if similar:
                    return similar
            except Exception as e:
                logger.warning(f"Failed to retrieve from context graph: {e}")

        # 2. 回退到本地历史
        # 简单的关键词匹配
        keywords = set(current_context.lower().split())
        scored = []

        for failure in self.failure_history:
            error_words = set(failure.error_message.lower().split())
            overlap = len(keywords & error_words)
            if overlap > 0:
                scored.append((overlap, failure))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [f for _, f in scored[:limit]]

    def get_failure_summary(self) -> str:
        """
        生成失败摘要 (用于 Plan Recitation)

        Returns:
            Markdown 格式的失败摘要
        """
        if not self.failure_history:
            return ""

        lines = ["## ⚠️ 历史失败（避免重复）"]

        # 最近5个失败
        recent = self.failure_history[-5:]
        for f in recent:
            lines.append(
                f"- [{f.taxonomy.value}] {f.get_learning()} "
                f"(exit_code={f.exit_code})"
            )

        # 如果接近 3-Strike
        if len(self._consecutive_failures) >= 2:
            lines.append("")
            lines.append(
                f"⚠️ 连续 {len(self._consecutive_failures)} 次 "
                f"{self._consecutive_failures[0].taxonomy.value} 失败！"
            )

        return "\n".join(lines)

    def get_statistics(self) -> dict[str, Any]:
        """获取失败统计"""
        total = len(self.failure_history)
        by_type = {
            t.value: c for t, c in self._failure_counts.items()
        }

        return {
            "total_failures": total,
            "by_type": by_type,
            "consecutive_failures": len(self._consecutive_failures),
            "consecutive_type": (
                self._consecutive_failures[0].taxonomy.value
                if self._consecutive_failures
                else None
            ),
            "should_abort": self.should_abort(),
        }

    def reset(self) -> None:
        """重置观测器状态"""
        self.failure_history.clear()
        self._failure_counts.clear()
        self._consecutive_failures.clear()

    def clear_consecutive(self) -> None:
        """清除连续失败计数 (成功后调用)"""
        self._consecutive_failures.clear()


# 工厂函数：从工具执行结果创建 FailureSignal
def create_failure_signal_from_tool_result(
    tool_name: str,
    tool_args: dict[str, Any],
    exit_code: int,
    stdout: str,
    stderr: str,
    duration_ms: float,
    state_name: str | None = None,
    task_id: str | None = None,
    session_id: str | None = None,
) -> FailureSignal | None:
    """
    从工具执行结果创建失败信号

    Returns:
        FailureSignal 如果是失败，None 如果成功
    """
    import uuid

    if exit_code == 0:
        return None  # 成功，不创建失败信号

    # 根据错误内容推断失败类型
    taxonomy = _infer_taxonomy(exit_code, stderr, tool_name)

    return FailureSignal(
        signal_id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        source="tool",
        tool_name=tool_name,
        tool_args=tool_args,
        taxonomy=taxonomy,
        exit_code=exit_code,
        error_message=stderr[:500] if stderr else f"Exit code: {exit_code}",
        stderr=stderr,
        state_name=state_name,
        task_id=task_id,
        session_id=session_id,
        is_retryable=_is_retryable(taxonomy),
    )


def _infer_taxonomy(exit_code: int, stderr: str, tool_name: str) -> FailureTaxonomy:
    """推断失败类型"""
    stderr_lower = stderr.lower()

    # 超时
    if "timeout" in stderr_lower or exit_code == 124:
        return FailureTaxonomy.TOOL_TIMEOUT

    # 权限
    if "permission" in stderr_lower or "denied" in stderr_lower:
        return FailureTaxonomy.TOOL_PERMISSION_DENIED

    # 找不到
    if "not found" in stderr_lower or "no such file" in stderr_lower:
        return FailureTaxonomy.SELECTION_MISS

    # 网络
    if "connection" in stderr_lower or "network" in stderr_lower:
        return FailureTaxonomy.NETWORK_UNREACHABLE

    # 限流
    if "rate limit" in stderr_lower or "429" in stderr:
        return FailureTaxonomy.API_RATE_LIMITED

    # 测试
    if "test" in tool_name.lower() or "pytest" in tool_name.lower():
        return FailureTaxonomy.TEST_FAIL

    # Lint
    if "lint" in tool_name.lower() or "ruff" in tool_name.lower():
        return FailureTaxonomy.LINT_FAIL

    # 类型检查
    if "mypy" in tool_name.lower() or "type" in tool_name.lower():
        return FailureTaxonomy.TYPE_CHECK_FAIL

    return FailureTaxonomy.TOOL_EXECUTION_ERROR


def _is_retryable(taxonomy: FailureTaxonomy) -> bool:
    """判断是否可重试"""
    non_retryable = {
        FailureTaxonomy.USER_CANCELLED,
        FailureTaxonomy.USER_REJECTED,
        FailureTaxonomy.BUDGET_EXCEEDED,
        FailureTaxonomy.MAX_RETRIES_REACHED,
    }
    return taxonomy not in non_retryable
