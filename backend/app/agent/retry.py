"""
Unified Retry Strategy - 统一重试策略

提供细粒度的重试控制：
- 按错误类型配置不同的重试策略
- 指数退避 + 随机抖动防止惊群
- 与 FailureSignal 系统集成

使用示例：
    policy = RetryPolicy.for_error_type(FailureType.RATE_LIMITED)
    result = await RetryExecutor(policy).execute(async_func, *args)
"""

import asyncio
import logging
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypeVar

from .failure.signal import FailureSignal, FailureType

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryStrategy(Enum):
    """重试策略类型"""

    NONE = "none"                    # 不重试
    IMMEDIATE = "immediate"          # 立即重试
    LINEAR = "linear"                # 线性退避
    EXPONENTIAL = "exponential"      # 指数退避（推荐）
    EXPONENTIAL_JITTER = "exponential_jitter"  # 指数退避 + 抖动（最佳实践）


@dataclass
class RetryPolicy:
    """重试策略配置

    Attributes:
        max_retries: 最大重试次数（不含首次尝试）
        strategy: 重试策略类型
        initial_delay: 初始延迟（秒）
        max_delay: 最大延迟（秒）
        backoff_factor: 退避因子（用于指数退避）
        jitter_factor: 抖动因子（0-1，用于随机化延迟）
        retryable_types: 可重试的错误类型（空=全部可重试类型）
    """

    max_retries: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_JITTER
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter_factor: float = 0.2
    retryable_types: set[FailureType] = field(default_factory=set)

    def get_delay(self, attempt: int) -> float:
        """计算第 N 次重试的延迟时间

        Args:
            attempt: 当前重试次数（从 1 开始）

        Returns:
            延迟秒数
        """
        if self.strategy == RetryStrategy.NONE:
            return 0.0

        if self.strategy == RetryStrategy.IMMEDIATE:
            return 0.0

        if self.strategy == RetryStrategy.LINEAR:
            delay = self.initial_delay * attempt

        elif self.strategy in (RetryStrategy.EXPONENTIAL, RetryStrategy.EXPONENTIAL_JITTER):
            delay = self.initial_delay * (self.backoff_factor ** (attempt - 1))

        else:
            delay = self.initial_delay

        # 应用最大延迟限制
        delay = min(delay, self.max_delay)

        # 添加抖动（防止惊群效应）
        if self.strategy == RetryStrategy.EXPONENTIAL_JITTER and self.jitter_factor > 0:
            jitter = delay * self.jitter_factor * random.random()
            delay = delay + jitter

        return delay

    def should_retry(self, failure: FailureSignal, attempt: int) -> bool:
        """判断是否应该重试

        Args:
            failure: 失败信号
            attempt: 已尝试次数

        Returns:
            是否应该重试
        """
        # 超过最大重试次数
        if attempt >= self.max_retries:
            return False

        # 策略为不重试
        if self.strategy == RetryStrategy.NONE:
            return False

        # 检查失败信号是否可重试
        if not failure.is_retryable():
            return False

        # 如果配置了可重试类型，检查是否在列表中
        if self.retryable_types and failure.failure_type not in self.retryable_types:
            return False

        return True

    @classmethod
    def for_error_type(cls, error_type: FailureType) -> "RetryPolicy":
        """根据错误类型返回推荐的重试策略

        不同错误类型有不同的最佳重试策略：
        - RATE_LIMITED: 长延迟 + 更多重试
        - NETWORK_ERROR: 中等延迟 + 指数退避
        - TIMEOUT: 较少重试，避免资源浪费
        - EXECUTION_ERROR: 快速重试，可能是瞬时错误
        """
        strategies = {
            FailureType.RATE_LIMITED: cls(
                max_retries=5,
                strategy=RetryStrategy.EXPONENTIAL_JITTER,
                initial_delay=5.0,  # 限流需要更长初始延迟
                max_delay=120.0,
                backoff_factor=2.5,
                jitter_factor=0.3,
            ),
            FailureType.NETWORK_ERROR: cls(
                max_retries=3,
                strategy=RetryStrategy.EXPONENTIAL_JITTER,
                initial_delay=1.0,
                max_delay=30.0,
                backoff_factor=2.0,
                jitter_factor=0.2,
            ),
            FailureType.TIMEOUT: cls(
                max_retries=2,
                strategy=RetryStrategy.EXPONENTIAL,
                initial_delay=2.0,
                max_delay=10.0,
                backoff_factor=1.5,
                jitter_factor=0.0,  # 超时通常不需要抖动
            ),
            FailureType.EXECUTION_ERROR: cls(
                max_retries=2,
                strategy=RetryStrategy.EXPONENTIAL_JITTER,
                initial_delay=0.5,
                max_delay=5.0,
                backoff_factor=2.0,
                jitter_factor=0.1,
            ),
            FailureType.RESOURCE_NOT_FOUND: cls(
                max_retries=1,  # 资源不存在通常不应重试太多
                strategy=RetryStrategy.IMMEDIATE,
                initial_delay=0.0,
            ),
            # 不可重试的类型
            FailureType.PERMISSION_DENIED: cls(
                max_retries=0,
                strategy=RetryStrategy.NONE,
            ),
            FailureType.INVALID_PARAMS: cls(
                max_retries=0,
                strategy=RetryStrategy.NONE,
            ),
            FailureType.REJECTED: cls(
                max_retries=0,
                strategy=RetryStrategy.NONE,
            ),
        }

        return strategies.get(error_type, cls.default())

    @classmethod
    def default(cls) -> "RetryPolicy":
        """默认重试策略"""
        return cls(
            max_retries=3,
            strategy=RetryStrategy.EXPONENTIAL_JITTER,
            initial_delay=1.0,
            max_delay=30.0,
            backoff_factor=2.0,
            jitter_factor=0.2,
        )

    @classmethod
    def no_retry(cls) -> "RetryPolicy":
        """不重试策略"""
        return cls(max_retries=0, strategy=RetryStrategy.NONE)

    @classmethod
    def aggressive(cls) -> "RetryPolicy":
        """激进重试策略（用于关键操作）"""
        return cls(
            max_retries=5,
            strategy=RetryStrategy.EXPONENTIAL_JITTER,
            initial_delay=0.5,
            max_delay=60.0,
            backoff_factor=2.0,
            jitter_factor=0.3,
        )


@dataclass
class RetryResult:
    """重试执行结果"""

    success: bool
    result: Any = None
    error: str | None = None
    failure_signal: FailureSignal | None = None
    attempts: int = 1
    total_delay: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "error": self.error,
            "attempts": self.attempts,
            "total_delay": self.total_delay,
            "failure_type": self.failure_signal.failure_type.value if self.failure_signal else None,
        }


class RetryExecutor:
    """重试执行器

    封装重试逻辑，支持：
    - 异步函数执行
    - 自动错误类型推断
    - 详细日志记录
    - FailureSignal 集成

    使用示例：
        executor = RetryExecutor(RetryPolicy.default())
        result = await executor.execute(some_async_func, arg1, arg2)

        if not result.success:
            print(f"Failed after {result.attempts} attempts: {result.error}")
    """

    def __init__(
        self,
        policy: RetryPolicy | None = None,
        tool_name: str | None = None,
    ):
        """
        Args:
            policy: 重试策略，默认使用 default()
            tool_name: 工具名称（用于日志和 FailureSignal）
        """
        self.policy = policy or RetryPolicy.default()
        self.tool_name = tool_name

    async def execute(
        self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> RetryResult:
        """执行函数并自动重试

        Args:
            func: 要执行的异步函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            RetryResult 包含执行结果和统计信息
        """
        attempt = 0
        total_delay = 0.0
        last_failure: FailureSignal | None = None
        last_error: str | None = None

        while True:
            attempt += 1

            try:
                # 执行函数
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # 成功
                logger.debug(
                    f"Execution succeeded on attempt {attempt}"
                    + (f" for {self.tool_name}" if self.tool_name else "")
                )

                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempt,
                    total_delay=total_delay,
                )

            except Exception as e:
                last_error = str(e)

                # 创建失败信号
                last_failure = FailureSignal.from_tool_result(
                    tool_name=self.tool_name or "unknown",
                    success=False,
                    error=last_error,
                )

                # 判断是否应该重试
                if not self.policy.should_retry(last_failure, attempt):
                    logger.warning(
                        f"Not retrying after attempt {attempt}: {last_error}"
                        + (f" for {self.tool_name}" if self.tool_name else "")
                        + f" (type={last_failure.failure_type.value})"
                    )
                    break

                # 计算延迟
                delay = self.policy.get_delay(attempt)
                total_delay += delay

                logger.info(
                    f"Retry {attempt}/{self.policy.max_retries} after {delay:.2f}s: {last_error}"
                    + (f" for {self.tool_name}" if self.tool_name else "")
                )

                # 等待
                if delay > 0:
                    await asyncio.sleep(delay)

        # 所有重试都失败
        return RetryResult(
            success=False,
            error=last_error,
            failure_signal=last_failure,
            attempts=attempt,
            total_delay=total_delay,
        )

    async def execute_with_fallback(
        self,
        primary_func: Callable[..., Any],
        fallback_func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> RetryResult:
        """执行主函数，失败后尝试备用函数

        用于多数据源场景，如 OpenBB -> AkShare 备用

        Args:
            primary_func: 主函数
            fallback_func: 备用函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            RetryResult
        """
        # 先尝试主函数
        result = await self.execute(primary_func, *args, **kwargs)

        if result.success:
            return result

        # 主函数失败，尝试备用
        logger.info(
            "Primary function failed, trying fallback"
            + (f" for {self.tool_name}" if self.tool_name else "")
        )

        fallback_result = await self.execute(fallback_func, *args, **kwargs)

        # 合并统计信息
        fallback_result.attempts += result.attempts
        fallback_result.total_delay += result.total_delay

        return fallback_result


# ============================================================================
# 便捷函数
# ============================================================================

async def retry_with_policy(
    func: Callable[..., Any],
    policy: RetryPolicy | None = None,
    tool_name: str | None = None,
    *args: Any,
    **kwargs: Any,
) -> RetryResult:
    """便捷函数：带重试策略执行

    Example:
        result = await retry_with_policy(
            fetch_data,
            policy=RetryPolicy.for_error_type(FailureType.RATE_LIMITED),
            tool_name="fetch_data",
            url="https://api.example.com",
        )
    """
    executor = RetryExecutor(policy, tool_name)
    return await executor.execute(func, *args, **kwargs)


async def retry_on_rate_limit(
    func: Callable[..., Any],
    tool_name: str | None = None,
    *args: Any,
    **kwargs: Any,
) -> RetryResult:
    """便捷函数：针对限流的重试策略"""
    policy = RetryPolicy.for_error_type(FailureType.RATE_LIMITED)
    return await retry_with_policy(func, policy, tool_name, *args, **kwargs)


async def retry_on_network_error(
    func: Callable[..., Any],
    tool_name: str | None = None,
    *args: Any,
    **kwargs: Any,
) -> RetryResult:
    """便捷函数：针对网络错误的重试策略"""
    policy = RetryPolicy.for_error_type(FailureType.NETWORK_ERROR)
    return await retry_with_policy(func, policy, tool_name, *args, **kwargs)
