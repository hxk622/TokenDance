"""
Token Budget Manager - Token 预算管理

动态管理每次迭代的 token 预算，避免突然耗尽

核心功能：
1. Token 预算计算
2. 使用率监控
3. 模式切换建议（正常 → 摘要）
4. 预算预警

参考：AGENT_ROBUSTNESS_ASSESSMENT.md - 阶段 1.3
"""

from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TokenUsage:
    """Token 使用情况"""
    input_tokens: int  # 输入 token 数
    output_tokens: int  # 输出 token 数
    total_tokens: int  # 总 token 数
    usage_ratio: float  # 使用率


class TokenBudgetManager:
    """Token 预算管理器
    
    动态管理 token 预算，防止突然耗尽
    """
    
    # 模式切换阈值
    SUMMARY_MODE_THRESHOLD = 0.85  # 超过 85% 切换到摘要模式
    WARNING_THRESHOLD = 0.70  # 超过 70% 发出警告
    
    def __init__(
        self,
        total_budget: int = 200_000,  # Claude 3.5 Sonnet context window
        reserved_ratio: float = 0.20,  # 保留 20% 用于最终回答
        min_iteration_budget: int = 2000,  # 每次迭代最少 token
    ):
        """初始化 Token 预算管理器
        
        Args:
            total_budget: 总 token 预算
            reserved_ratio: 保留比例（用于最终回答）
            min_iteration_budget: 每次迭代最少 token 预算
        """
        self.total_budget = total_budget
        self.reserved_ratio = reserved_ratio
        self.reserved_tokens = int(total_budget * reserved_ratio)
        self.available_budget = total_budget - self.reserved_tokens
        self.min_iteration_budget = min_iteration_budget
        
        # 运行时状态
        self.used_tokens = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.iteration_history: list[TokenUsage] = []
        
        logger.info(
            f"TokenBudgetManager initialized: "
            f"total={total_budget}, reserved={self.reserved_tokens}, "
            f"available={self.available_budget}"
        )
    
    def record_usage(self, input_tokens: int, output_tokens: int) -> TokenUsage:
        """记录 token 使用
        
        Args:
            input_tokens: 本次输入 token 数
            output_tokens: 本次输出 token 数
            
        Returns:
            TokenUsage: 使用情况
        """
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.used_tokens = self.input_tokens + self.output_tokens
        
        usage = TokenUsage(
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            total_tokens=self.used_tokens,
            usage_ratio=self.used_tokens / self.total_budget,
        )
        
        self.iteration_history.append(usage)
        
        logger.debug(
            f"Token usage recorded: +{input_tokens}/{output_tokens}, "
            f"total={self.used_tokens} ({usage.usage_ratio:.1%})"
        )
        
        return usage
    
    def get_iteration_budget(self) -> int:
        """获取下一次迭代的 token 预算
        
        基于剩余预算和预估迭代次数计算
        
        Returns:
            int: 推荐的迭代预算
        """
        remaining = self.available_budget - self.used_tokens
        
        if remaining <= 0:
            return 0
        
        # 估算剩余迭代次数（基于历史平均消耗）
        if self.iteration_history:
            # 计算平均每次迭代消耗
            avg_per_iter = self.used_tokens / len(self.iteration_history)
            estimated_remaining_iters = max(1, int(remaining / avg_per_iter))
        else:
            # 默认估算 20 次迭代
            estimated_remaining_iters = 20
        
        # 计算每次迭代预算
        iteration_budget = max(
            self.min_iteration_budget,
            remaining // estimated_remaining_iters
        )
        
        return iteration_budget
    
    def should_switch_to_summary_mode(self) -> Tuple[bool, str]:
        """判断是否应该切换到摘要模式
        
        Returns:
            tuple[bool, str]: (是否切换, 原因)
        """
        usage_ratio = self.used_tokens / self.total_budget
        
        if usage_ratio >= self.SUMMARY_MODE_THRESHOLD:
            return True, f"Token 使用率 {usage_ratio:.1%} 超过阈值 {self.SUMMARY_MODE_THRESHOLD:.0%}"
        
        # 检查剩余预算是否足够最终回答
        remaining_for_final = self.total_budget - self.used_tokens
        if remaining_for_final < self.reserved_tokens * 1.5:  # 安全余量
            return True, f"剩余预算 {remaining_for_final} 接近保留预算 {self.reserved_tokens}"
        
        return False, "正常模式"
    
    def get_budget_status(self) -> Dict[str, Any]:
        """获取预算状态
        
        Returns:
            Dict: 预算状态
        """
        usage_ratio = self.used_tokens / self.total_budget
        remaining = self.total_budget - self.used_tokens
        available_remaining = self.available_budget - self.used_tokens
        
        # 状态等级
        if usage_ratio >= self.SUMMARY_MODE_THRESHOLD:
            status_level = "critical"
        elif usage_ratio >= self.WARNING_THRESHOLD:
            status_level = "warning"
        else:
            status_level = "normal"
        
        return {
            "total_budget": self.total_budget,
            "used_tokens": self.used_tokens,
            "remaining_tokens": remaining,
            "available_remaining": available_remaining,
            "reserved_tokens": self.reserved_tokens,
            "usage_ratio": usage_ratio,
            "status_level": status_level,
            "iteration_count": len(self.iteration_history),
            "avg_tokens_per_iteration": (
                self.used_tokens / len(self.iteration_history)
                if self.iteration_history else 0
            ),
        }
    
    def estimate_remaining_iterations(self) -> int:
        """估算剩余可执行的迭代次数
        
        Returns:
            int: 预计剩余迭代次数
        """
        if not self.iteration_history:
            # 默认估算
            return max(1, (self.available_budget - self.used_tokens) // 5000)
        
        # 基于历史平均计算
        avg_per_iter = self.used_tokens / len(self.iteration_history)
        remaining = self.available_budget - self.used_tokens
        
        if avg_per_iter <= 0:
            return 100  # 避免除零
        
        return max(0, int(remaining / avg_per_iter))
    
    def get_warning_message(self) -> Optional[str]:
        """获取预警消息
        
        Returns:
            Optional[str]: 预警消息，或 None
        """
        usage_ratio = self.used_tokens / self.total_budget
        
        if usage_ratio >= self.SUMMARY_MODE_THRESHOLD:
            return (
                f"⚠️ Token 预算紧张 ({usage_ratio:.1%})！"
                f"建议切换到摘要模式，或尽快完成任务。"
            )
        elif usage_ratio >= self.WARNING_THRESHOLD:
            remaining_iters = self.estimate_remaining_iterations()
            return (
                f"⚠️ Token 使用率 {usage_ratio:.1%}，"
                f"预计还可执行约 {remaining_iters} 次迭代。"
            )
        
        return None
    
    def can_continue(self) -> Tuple[bool, str]:
        """判断是否有足够预算继续
        
        Returns:
            tuple[bool, str]: (是否可继续, 原因)
        """
        remaining = self.available_budget - self.used_tokens
        
        if remaining <= self.min_iteration_budget:
            return False, f"剩余预算 {remaining} 不足最小迭代预算 {self.min_iteration_budget}"
        
        # 确保有足够的保留预算
        total_remaining = self.total_budget - self.used_tokens
        if total_remaining < self.reserved_tokens:
            return False, f"需保留 {self.reserved_tokens} token 用于最终回答"
        
        return True, "预算充足"
    
    def reset(self) -> None:
        """重置预算管理器状态"""
        self.used_tokens = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.iteration_history.clear()
        
        logger.info("TokenBudgetManager reset")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            "total_budget": self.total_budget,
            "reserved_ratio": self.reserved_ratio,
            "reserved_tokens": self.reserved_tokens,
            "available_budget": self.available_budget,
            "min_iteration_budget": self.min_iteration_budget,
            "summary_mode_threshold": self.SUMMARY_MODE_THRESHOLD,
            "warning_threshold": self.WARNING_THRESHOLD,
            "current_usage": self.get_budget_status(),
        }
