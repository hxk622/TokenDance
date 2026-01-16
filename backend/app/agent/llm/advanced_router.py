"""
高级 LLM 路由器

基于多因素（预算、延迟、上下文长度、任务复杂度）动态选择最优模型
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import logging

from .router import SimpleRouter, TaskType, ModelConfig, MODEL_REGISTRY
from .base import BaseLLM
from .openrouter import create_openrouter_llm

logger = logging.getLogger(__name__)


@dataclass
class RoutingContext:
    """路由上下文 - 记录路由决策过程"""
    task_type: TaskType
    selected_model: str
    reason: str
    candidates: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_type": self.task_type.value,
            "selected_model": self.selected_model,
            "reason": self.reason,
            "candidates": self.candidates,
            "constraints": self.constraints,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class RoutingConstraints:
    """路由约束条件"""
    # 预算约束
    max_cost_per_call: Optional[float] = None  # 单次调用最大成本 (USD)
    daily_budget: Optional[float] = None       # 每日预算 (USD)
    
    # 性能约束
    max_latency_ms: Optional[float] = None     # 最大延迟 (ms)
    
    # 上下文约束
    context_length: int = 0                     # 输入上下文长度 (tokens)
    expected_output_length: int = 1000          # 预期输出长度 (tokens)
    
    # 质量约束
    min_capability_score: Optional[float] = None  # 最小能力分数
    required_capabilities: List[str] = field(default_factory=list)  # 必需能力
    
    # 用户偏好
    preferred_models: List[str] = field(default_factory=list)
    excluded_models: List[str] = field(default_factory=list)


class AdvancedRouter(SimpleRouter):
    """高级动态路由器
    
    基于多因素动态选择最优模型，支持：
    - 预算控制
    - 延迟要求
    - 上下文长度适配
    - 能力匹配
    - 用户偏好
    """
    
    # 任务类型 -> 推荐能力
    TASK_CAPABILITIES = {
        TaskType.DEEP_RESEARCH: ["reasoning", "analysis"],
        TaskType.FINANCIAL_ANALYSIS: ["reasoning", "analysis"],
        TaskType.PPT_GENERATION: ["balanced", "coding"],
        TaskType.CODE_GENERATION: ["coding"],
        TaskType.QUICK_QA: ["fast", "simple_qa"],
        TaskType.MULTIMODAL: ["multimodal", "vision"],
        TaskType.GENERAL: ["balanced"],
    }
    
    def __init__(self, use_openrouter: bool = True):
        super().__init__(use_openrouter)
        self._routing_history: List[RoutingContext] = []
        logger.info("AdvancedRouter initialized")
    
    def select_model(
        self,
        task_type: TaskType | str,
        constraints: Optional[RoutingConstraints] = None,
        **kwargs
    ) -> str:
        """智能选择模型
        
        Args:
            task_type: 任务类型
            constraints: 路由约束条件
            **kwargs: 其他参数
            
        Returns:
            str: 最优模型名称
        """
        # 转换任务类型
        if isinstance(task_type, str):
            try:
                task_type = TaskType(task_type)
            except ValueError:
                task_type = TaskType.GENERAL
        
        # 如果没有约束，使用简单路由
        if constraints is None:
            return super().select_model(task_type)
        
        # 获取候选模型
        candidates = self._get_candidates(task_type, constraints)
        
        if not candidates:
            # 无满足条件的模型，降级到简单路由
            logger.warning("No candidates match constraints, falling back to simple routing")
            return super().select_model(task_type)
        
        # 评分并选择最优模型
        best_model, reason = self._select_best(candidates, task_type, constraints)
        
        # 记录路由决策
        context = RoutingContext(
            task_type=task_type,
            selected_model=best_model,
            reason=reason,
            candidates=candidates,
            constraints={
                "max_cost_per_call": constraints.max_cost_per_call,
                "max_latency_ms": constraints.max_latency_ms,
                "context_length": constraints.context_length,
            }
        )
        self._routing_history.append(context)
        
        logger.info(f"Advanced routing: {best_model} ({reason})")
        return best_model
    
    def _get_candidates(
        self,
        task_type: TaskType,
        constraints: RoutingConstraints
    ) -> List[str]:
        """获取满足约束的候选模型"""
        candidates = []
        
        for model_name, config in MODEL_REGISTRY.items():
            # 检查排除列表
            if model_name in constraints.excluded_models:
                continue
            
            # 检查上下文窗口
            if constraints.context_length > config.context_window:
                continue
            
            # 检查延迟要求
            if constraints.max_latency_ms and config.avg_latency_ms > constraints.max_latency_ms:
                continue
            
            # 检查成本约束
            if constraints.max_cost_per_call:
                estimated_cost = self.estimate_cost(
                    model_name,
                    constraints.context_length,
                    constraints.expected_output_length
                )
                if estimated_cost > constraints.max_cost_per_call:
                    continue
            
            # 检查必需能力
            if constraints.required_capabilities:
                if not all(cap in config.capabilities for cap in constraints.required_capabilities):
                    continue
            
            candidates.append(model_name)
        
        return candidates
    
    def _select_best(
        self,
        candidates: List[str],
        task_type: TaskType,
        constraints: RoutingConstraints
    ) -> tuple[str, str]:
        """从候选中选择最优模型
        
        Returns:
            tuple: (model_name, selection_reason)
        """
        # 优先使用用户偏好
        for preferred in constraints.preferred_models:
            if preferred in candidates:
                return preferred, "user_preference"
        
        # 计算每个候选的综合评分
        scores = {}
        for model_name in candidates:
            scores[model_name] = self._calculate_score(model_name, task_type, constraints)
        
        # 选择最高分
        best_model = max(scores, key=scores.get)
        
        # 确定选择原因
        config = MODEL_REGISTRY[best_model]
        if "fast" in config.capabilities:
            reason = "latency_optimized"
        elif "cheap" in config.capabilities:
            reason = "cost_optimized"
        elif "reasoning" in config.capabilities:
            reason = "quality_optimized"
        else:
            reason = "balanced"
        
        return best_model, reason
    
    def _calculate_score(
        self,
        model_name: str,
        task_type: TaskType,
        constraints: RoutingConstraints
    ) -> float:
        """计算模型综合评分
        
        考虑因素：
        - 任务适配度 (40%)
        - 成本效益 (30%)
        - 延迟性能 (20%)
        - 能力覆盖 (10%)
        """
        config = MODEL_REGISTRY.get(model_name)
        if not config:
            return 0.0
        
        score = 0.0
        
        # 1. 任务适配度 (40%)
        required_caps = self.TASK_CAPABILITIES.get(task_type, [])
        cap_match = sum(1 for cap in required_caps if cap in config.capabilities)
        task_fit = (cap_match / max(len(required_caps), 1)) * 40
        score += task_fit
        
        # 2. 成本效益 (30%)
        # 成本越低分数越高
        cost = self.estimate_cost(
            model_name,
            constraints.context_length or 1000,
            constraints.expected_output_length or 1000
        )
        # 使用对数缩放，避免极端值
        if cost > 0:
            cost_score = max(0, 30 - (cost * 100))  # 成本每增加 0.01 USD 减少 1 分
        else:
            cost_score = 30
        score += cost_score
        
        # 3. 延迟性能 (20%)
        # 延迟越低分数越高
        latency_score = max(0, 20 - (config.avg_latency_ms / 500))  # 每 500ms 减少 1 分
        score += latency_score
        
        # 4. 能力覆盖 (10%)
        capability_score = min(len(config.capabilities) * 2, 10)
        score += capability_score
        
        return score
    
    def create_llm_with_constraints(
        self,
        task_type: TaskType | str,
        constraints: RoutingConstraints,
        **llm_kwargs
    ) -> BaseLLM:
        """根据约束创建 LLM
        
        Args:
            task_type: 任务类型
            constraints: 路由约束
            **llm_kwargs: LLM 参数
            
        Returns:
            BaseLLM: LLM 客户端
        """
        model = self.select_model(task_type, constraints)
        return create_openrouter_llm(model=model, **llm_kwargs)
    
    def get_routing_history(self) -> List[Dict[str, Any]]:
        """获取路由历史（用于分析和调试）"""
        return [ctx.to_dict() for ctx in self._routing_history[-100:]]  # 保留最近 100 条
    
    def clear_routing_history(self):
        """清空路由历史"""
        self._routing_history.clear()


# 便捷函数
def get_llm_with_constraints(
    task_type: TaskType | str,
    max_cost: Optional[float] = None,
    max_latency_ms: Optional[float] = None,
    context_length: int = 0,
    **llm_kwargs
) -> BaseLLM:
    """快捷方式：根据约束获取 LLM
    
    Args:
        task_type: 任务类型
        max_cost: 最大单次调用成本 (USD)
        max_latency_ms: 最大延迟 (ms)
        context_length: 上下文长度 (tokens)
        **llm_kwargs: LLM 参数
        
    Returns:
        BaseLLM: LLM 客户端
        
    Example:
        >>> # 快速响应场景
        >>> llm = get_llm_with_constraints("quick_qa", max_latency_ms=1000)
        
        >>> # 预算敏感场景
        >>> llm = get_llm_with_constraints("deep_research", max_cost=0.1)
    """
    constraints = RoutingConstraints(
        max_cost_per_call=max_cost,
        max_latency_ms=max_latency_ms,
        context_length=context_length
    )
    
    router = AdvancedRouter()
    return router.create_llm_with_constraints(task_type, constraints, **llm_kwargs)
