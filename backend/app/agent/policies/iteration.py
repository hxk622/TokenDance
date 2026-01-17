"""
Dynamic Iteration Policy - 动态迭代预算管理

突破硬编码的 max_iterations=20 限制，支持 100+ 迭代

核心功能：
1. 基于任务复杂度动态计算迭代预算
2. 实时监控执行状态（context、time、iterations）
3. 智能判断是否应该继续迭代

参考：AGENT_ROBUSTNESS_ASSESSMENT.md - 阶段 1.1
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class IterationBudget:
    """迭代预算"""
    base_budget: int  # 基础预算
    calculated_budget: int  # 计算后的预算
    max_iterations: int  # 绝对上限
    complexity_factor: float  # 复杂度因子
    time_budget_seconds: float  # 时间预算


class DynamicIterationPolicy:
    """动态迭代策略

    根据任务复杂度、可用时间和 Context 状态动态计算迭代预算
    """

    # 复杂度关键词权重
    COMPLEXITY_KEYWORDS = {
        # 高复杂度关键词 (权重 2.0-3.0)
        r'(研究|research|调研|分析|analysis)': 2.5,
        r'(生成|generate|创建|create|build)': 2.0,
        r'(优化|optimize|重构|refactor)': 2.5,
        r'(测试|test|验证|validate)': 2.0,
        r'(调试|debug|修复|fix|bug)': 2.5,
        r'(集成|integrate|整合)': 2.0,

        # 中等复杂度关键词 (权重 1.5)
        r'(编写|write|实现|implement)': 1.5,
        r'(修改|modify|更新|update)': 1.5,
        r'(查找|search|find)': 1.5,

        # 低复杂度关键词 (权重 1.0)
        r'(读取|read|查看|view)': 1.0,
        r'(解释|explain|说明)': 1.0,
    }

    def __init__(
        self,
        base_budget: int = 30,
        max_iterations: int = 100,
        available_time_seconds: float = 300.0,
        context_window_limit: int = 200_000,
    ):
        """初始化动态迭代策略

        Args:
            base_budget: 基础迭代预算（默认 30）
            max_iterations: 绝对迭代上限（默认 100）
            available_time_seconds: 可用时间预算（默认 300s = 5分钟）
            context_window_limit: Context 窗口大小限制
        """
        self.base_budget = base_budget
        self.max_iterations = max_iterations
        self.available_time_seconds = available_time_seconds
        self.context_window_limit = context_window_limit

        # 运行时状态
        self.start_time: datetime | None = None
        self.iteration_count = 0

        logger.info(
            f"DynamicIterationPolicy initialized: "
            f"base={base_budget}, max={max_iterations}, time={available_time_seconds}s"
        )

    def calculate_budget(self, task_description: str) -> IterationBudget:
        """根据任务复杂度计算迭代预算

        Args:
            task_description: 任务描述

        Returns:
            IterationBudget: 迭代预算
        """
        # 1. 分析任务复杂度
        complexity = self._analyze_complexity(task_description)

        # 2. 基于时间估算可用迭代数
        # 假设每次迭代平均耗时 3-5 秒
        avg_time_per_iter = 4.0
        iterations_by_time = int(self.available_time_seconds / avg_time_per_iter)

        # 3. 综合计算预算
        calculated_budget = int(self.base_budget * complexity)

        # 4. 取各种限制的最小值
        final_budget = min(
            calculated_budget,
            iterations_by_time,
            self.max_iterations
        )

        # 5. 确保至少有基础预算
        final_budget = max(final_budget, self.base_budget)

        logger.info(
            f"Iteration budget calculated: {final_budget} "
            f"(complexity={complexity:.2f}, by_time={iterations_by_time})"
        )

        return IterationBudget(
            base_budget=self.base_budget,
            calculated_budget=calculated_budget,
            max_iterations=self.max_iterations,
            complexity_factor=complexity,
            time_budget_seconds=self.available_time_seconds,
        )

    def _analyze_complexity(self, text: str) -> float:
        """分析任务复杂度

        基于关键词匹配计算复杂度因子

        Args:
            text: 任务描述文本

        Returns:
            float: 复杂度因子 (1.0 - 3.0)
        """
        text_lower = text.lower()

        # 匹配关键词并累积权重
        total_weight = 0.0
        match_count = 0

        for pattern, weight in self.COMPLEXITY_KEYWORDS.items():
            if re.search(pattern, text_lower):
                total_weight += weight
                match_count += 1

        if match_count == 0:
            # 默认复杂度
            return 1.0

        # 计算平均权重
        avg_weight = total_weight / match_count

        # 归一化到 1.0 - 3.0 范围
        complexity = max(1.0, min(3.0, avg_weight))

        return complexity

    def should_continue(
        self,
        iteration: int,
        context_tokens_used: int,
        has_fatal_error: bool = False,
        elapsed_seconds: float | None = None,
    ) -> tuple[bool, str]:
        """判断是否应该继续迭代

        Args:
            iteration: 当前迭代次数
            context_tokens_used: Context 已使用的 token 数
            has_fatal_error: 是否有致命错误
            elapsed_seconds: 已耗时（秒）

        Returns:
            tuple[bool, str]: (是否继续, 原因)
        """
        # 1. 检查致命错误
        if has_fatal_error:
            return False, "致命错误，停止迭代"

        # 2. 检查绝对迭代上限
        if iteration >= self.max_iterations:
            return False, f"达到绝对迭代上限 ({self.max_iterations})"

        # 3. 检查 Context 窗口使用率
        context_usage_ratio = context_tokens_used / self.context_window_limit
        if context_usage_ratio >= 0.95:
            return False, f"Context 窗口使用率过高 ({context_usage_ratio:.1%})"

        # 4. 检查时间预算
        if elapsed_seconds is not None:
            if elapsed_seconds >= self.available_time_seconds:
                return False, f"超过时间预算 ({elapsed_seconds:.1f}s / {self.available_time_seconds}s)"

        # 5. Context 使用率警告（不停止，但记录）
        if context_usage_ratio >= 0.80:
            logger.warning(
                f"Context usage high: {context_usage_ratio:.1%}, "
                f"consider compression"
            )

        # 所有检查通过
        return True, "继续迭代"

    def get_remaining_budget(
        self,
        budget: IterationBudget,
        current_iteration: int,
    ) -> int:
        """获取剩余迭代预算

        Args:
            budget: 迭代预算
            current_iteration: 当前迭代次数

        Returns:
            int: 剩余迭代次数
        """
        return max(0, budget.calculated_budget - current_iteration)

    def estimate_time_remaining(
        self,
        budget: IterationBudget,
        current_iteration: int,
        elapsed_seconds: float,
    ) -> float:
        """估算剩余执行时间

        Args:
            budget: 迭代预算
            current_iteration: 当前迭代次数
            elapsed_seconds: 已耗时

        Returns:
            float: 预计剩余时间（秒）
        """
        if current_iteration == 0:
            return budget.time_budget_seconds

        # 计算平均每次迭代耗时
        avg_time_per_iter = elapsed_seconds / current_iteration

        # 估算剩余时间
        remaining_iters = self.get_remaining_budget(budget, current_iteration)
        estimated_remaining = remaining_iters * avg_time_per_iter

        return min(estimated_remaining, budget.time_budget_seconds - elapsed_seconds)

    def get_policy_stats(self) -> dict[str, Any]:
        """获取策略统计信息

        Returns:
            Dict: 统计信息
        """
        return {
            "base_budget": self.base_budget,
            "max_iterations": self.max_iterations,
            "available_time_seconds": self.available_time_seconds,
            "context_window_limit": self.context_window_limit,
        }
