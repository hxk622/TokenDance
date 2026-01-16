"""
统一 LLM 路由入口

整合所有路由策略，提供统一接口和 Fallback 机制
"""
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from datetime import datetime
import logging
import asyncio

from .router import SimpleRouter, TaskType, MODEL_REGISTRY, get_llm_for_task
from .advanced_router import AdvancedRouter, RoutingConstraints, get_llm_with_constraints
from .adaptive_router import AdaptiveRouter
from .base import BaseLLM, LLMResponse, LLMMessage
from .openrouter import create_openrouter_llm

logger = logging.getLogger(__name__)


@dataclass
class FallbackConfig:
    """Fallback 配置"""
    # 最大重试次数
    max_retries: int = 3
    
    # 重试间隔（秒）
    retry_delay: float = 1.0
    
    # 是否启用 OpenRouter 自动调度作为 fallback
    enable_openrouter_auto: bool = True
    
    # 模型降级链
    fallback_chain: List[str] = None
    
    def __post_init__(self):
        if self.fallback_chain is None:
            # 默认降级链：高性能 → 平衡 → 快速便宜
            self.fallback_chain = [
                "anthropic/claude-3-5-sonnet",
                "anthropic/claude-3-haiku",
                "deepseek/deepseek-coder"
            ]


class UnifiedRouter:
    """统一 LLM 路由器
    
    提供统一入口，整合所有路由策略：
    - 简单规则路由 (Phase 1)
    - 高级约束路由 (Phase 2)
    - 自适应学习路由 (Phase 3)
    - Fallback 降级机制 (Phase 4)
    
    Features:
    - 自动重试和降级
    - OpenRouter 作为最终 fallback
    - 错误跟踪和监控
    - 统一的调用记录
    """
    
    def __init__(
        self,
        fallback_config: Optional[FallbackConfig] = None,
        context_graph_client = None,
        enable_adaptive: bool = True
    ):
        """
        Args:
            fallback_config: Fallback 配置
            context_graph_client: Neo4j Context Graph 客户端
            enable_adaptive: 是否启用自适应学习
        """
        self.fallback_config = fallback_config or FallbackConfig()
        
        # 初始化各层路由器
        self.simple_router = SimpleRouter()
        self.advanced_router = AdvancedRouter()
        self.adaptive_router = AdaptiveRouter(
            context_graph_client=context_graph_client,
            enable_exploration=enable_adaptive
        ) if enable_adaptive else None
        
        # 错误计数（用于熔断）
        self._error_counts: Dict[str, int] = {}
        self._error_timestamps: Dict[str, datetime] = {}
        
        # 熔断阈值
        self._circuit_breaker_threshold = 5  # 5 次错误触发熔断
        self._circuit_breaker_window = 300   # 5 分钟窗口
        
        logger.info(f"UnifiedRouter initialized (adaptive={enable_adaptive})")
    
    async def get_llm(
        self,
        task_type: TaskType | str,
        constraints: Optional[RoutingConstraints] = None,
        session_id: Optional[str] = None,
        **llm_kwargs
    ) -> BaseLLM:
        """获取 LLM 客户端（主入口）
        
        自动选择最优模型，支持约束和自适应学习
        
        Args:
            task_type: 任务类型
            constraints: 路由约束（可选）
            session_id: 会话 ID（用于 A/B 测试）
            **llm_kwargs: LLM 参数
            
        Returns:
            BaseLLM: LLM 客户端
        """
        # 选择模型
        model = await self._select_model(task_type, constraints, session_id)
        
        # 创建 LLM 客户端
        return create_openrouter_llm(model=model, **llm_kwargs)
    
    async def call_llm(
        self,
        task_type: TaskType | str,
        messages: List[LLMMessage],
        constraints: Optional[RoutingConstraints] = None,
        session_id: Optional[str] = None,
        system: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        **llm_kwargs
    ) -> LLMResponse:
        """调用 LLM（带自动重试和 Fallback）
        
        这是推荐的调用方式，自动处理错误和降级
        
        Args:
            task_type: 任务类型
            messages: 消息列表
            constraints: 路由约束
            session_id: 会话 ID
            system: 系统提示词
            tools: 工具定义
            **llm_kwargs: LLM 参数
            
        Returns:
            LLMResponse: LLM 响应
        """
        # 转换任务类型
        if isinstance(task_type, str):
            try:
                task_type = TaskType(task_type)
            except ValueError:
                task_type = TaskType.GENERAL
        
        # 构建尝试链
        models_to_try = await self._build_attempt_chain(task_type, constraints, session_id)
        
        last_error = None
        start_time = datetime.now()
        
        for attempt, model in enumerate(models_to_try):
            # 检查熔断
            if self._is_circuit_open(model):
                logger.warning(f"Circuit breaker open for {model}, skipping")
                continue
            
            try:
                # 创建 LLM 并调用
                llm = create_openrouter_llm(model=model, **llm_kwargs)
                response = await llm.complete(
                    messages=messages,
                    system=system,
                    tools=tools
                )
                
                # 记录成功
                latency_ms = (datetime.now() - start_time).total_seconds() * 1000
                await self._record_result(
                    model=model,
                    task_type=task_type,
                    success=True,
                    cost_usd=self._estimate_cost(model, response.usage) if response.usage else 0,
                    latency_ms=latency_ms,
                    session_id=session_id
                )
                
                # 重置错误计数
                self._reset_error_count(model)
                
                logger.info(f"LLM call succeeded: model={model}, attempt={attempt+1}")
                return response
                
            except Exception as e:
                last_error = e
                logger.warning(f"LLM call failed: model={model}, error={e}")
                
                # 记录错误
                self._record_error(model)
                
                # 等待后重试
                if attempt < len(models_to_try) - 1:
                    await asyncio.sleep(self.fallback_config.retry_delay)
        
        # 所有尝试都失败
        await self._record_result(
            model=models_to_try[-1] if models_to_try else "unknown",
            task_type=task_type,
            success=False,
            session_id=session_id
        )
        
        raise RuntimeError(f"All LLM attempts failed. Last error: {last_error}")
    
    async def _select_model(
        self,
        task_type: TaskType | str,
        constraints: Optional[RoutingConstraints],
        session_id: Optional[str]
    ) -> str:
        """选择模型（依次尝试各层路由）"""
        # 1. 尝试自适应路由
        if self.adaptive_router:
            try:
                return await self.adaptive_router.select_model_async(
                    task_type, constraints, session_id
                )
            except Exception as e:
                logger.warning(f"Adaptive router failed: {e}")
        
        # 2. 尝试高级路由
        if constraints:
            try:
                return self.advanced_router.select_model(task_type, constraints)
            except Exception as e:
                logger.warning(f"Advanced router failed: {e}")
        
        # 3. 回退到简单路由
        return self.simple_router.select_model(task_type)
    
    async def _build_attempt_chain(
        self,
        task_type: TaskType,
        constraints: Optional[RoutingConstraints],
        session_id: Optional[str]
    ) -> List[str]:
        """构建尝试链（主模型 + 降级模型）"""
        chain = []
        
        # 1. 首选模型
        primary_model = await self._select_model(task_type, constraints, session_id)
        chain.append(primary_model)
        
        # 2. 添加降级链中未包含的模型
        for fallback in self.fallback_config.fallback_chain:
            if fallback not in chain:
                chain.append(fallback)
        
        # 3. 如果启用 OpenRouter 自动调度，添加默认模型
        if self.fallback_config.enable_openrouter_auto:
            default_model = "anthropic/claude-3-5-sonnet"
            if default_model not in chain:
                chain.append(default_model)
        
        return chain[:self.fallback_config.max_retries + 1]
    
    async def _record_result(
        self,
        model: str,
        task_type: TaskType,
        success: bool,
        cost_usd: float = 0.0,
        latency_ms: float = 0.0,
        session_id: Optional[str] = None
    ):
        """记录调用结果"""
        if self.adaptive_router:
            await self.adaptive_router.record_call_result(
                model=model,
                task_type=task_type,
                success=success,
                cost_usd=cost_usd,
                latency_ms=latency_ms,
                session_id=session_id
            )
    
    def _estimate_cost(self, model: str, usage: Dict) -> float:
        """估算成本"""
        config = MODEL_REGISTRY.get(model)
        if not config or not usage:
            return 0.0
        
        return (
            (usage.get("input_tokens", 0) / 1000) * config.cost_per_1k_input +
            (usage.get("output_tokens", 0) / 1000) * config.cost_per_1k_output
        )
    
    def _record_error(self, model: str):
        """记录错误（用于熔断）"""
        now = datetime.now()
        
        # 清理过期的错误记录
        if model in self._error_timestamps:
            elapsed = (now - self._error_timestamps[model]).total_seconds()
            if elapsed > self._circuit_breaker_window:
                self._error_counts[model] = 0
        
        self._error_counts[model] = self._error_counts.get(model, 0) + 1
        self._error_timestamps[model] = now
    
    def _reset_error_count(self, model: str):
        """重置错误计数"""
        self._error_counts[model] = 0
    
    def _is_circuit_open(self, model: str) -> bool:
        """检查熔断器是否打开"""
        if model not in self._error_counts:
            return False
        
        # 检查时间窗口
        if model in self._error_timestamps:
            elapsed = (datetime.now() - self._error_timestamps[model]).total_seconds()
            if elapsed > self._circuit_breaker_window:
                # 窗口过期，重置
                self._error_counts[model] = 0
                return False
        
        return self._error_counts[model] >= self._circuit_breaker_threshold
    
    # ========== 便捷方法 ==========
    
    def get_simple_llm(
        self,
        task_type: TaskType | str,
        **llm_kwargs
    ) -> BaseLLM:
        """简单获取 LLM（同步，无约束）"""
        return get_llm_for_task(task_type, **llm_kwargs)
    
    def get_constrained_llm(
        self,
        task_type: TaskType | str,
        max_cost: Optional[float] = None,
        max_latency_ms: Optional[float] = None,
        **llm_kwargs
    ) -> BaseLLM:
        """根据约束获取 LLM（同步）"""
        return get_llm_with_constraints(
            task_type,
            max_cost=max_cost,
            max_latency_ms=max_latency_ms,
            **llm_kwargs
        )
    
    # ========== A/B 测试代理 ==========
    
    def create_ab_test(self, *args, **kwargs):
        """创建 A/B 测试"""
        if self.adaptive_router:
            return self.adaptive_router.create_ab_test(*args, **kwargs)
        raise RuntimeError("Adaptive router not enabled")
    
    def get_ab_test_results(self, name: str):
        """获取 A/B 测试结果"""
        if self.adaptive_router:
            return self.adaptive_router.get_ab_test_results(name)
        return None
    
    # ========== 状态和监控 ==========
    
    def get_router_status(self) -> Dict[str, Any]:
        """获取路由器状态"""
        status = {
            "simple_router": "active",
            "advanced_router": "active",
            "adaptive_router": "active" if self.adaptive_router else "disabled",
            "circuit_breakers": {
                model: {
                    "error_count": count,
                    "is_open": self._is_circuit_open(model)
                }
                for model, count in self._error_counts.items()
            }
        }
        
        if self.adaptive_router:
            status["performance_summary"] = self.adaptive_router.get_performance_summary()
        
        return status
    
    def get_model_info(self, model: str) -> Optional[Dict[str, Any]]:
        """获取模型信息"""
        config = MODEL_REGISTRY.get(model)
        if not config:
            return None
        
        return {
            "name": config.name,
            "provider": config.provider,
            "cost_per_1k_input": config.cost_per_1k_input,
            "cost_per_1k_output": config.cost_per_1k_output,
            "context_window": config.context_window,
            "avg_latency_ms": config.avg_latency_ms,
            "capabilities": config.capabilities
        }
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """列出所有可用模型"""
        return [
            self.get_model_info(model)
            for model in MODEL_REGISTRY.keys()
        ]


# ========== 全局单例 ==========

_router_instance: Optional[UnifiedRouter] = None


def get_router(
    context_graph_client = None,
    enable_adaptive: bool = True
) -> UnifiedRouter:
    """获取全局路由器实例
    
    Example:
        >>> from app.agent.llm.unified_router import get_router
        >>> router = get_router()
        >>> llm = await router.get_llm("deep_research")
    """
    global _router_instance
    
    if _router_instance is None:
        _router_instance = UnifiedRouter(
            context_graph_client=context_graph_client,
            enable_adaptive=enable_adaptive
        )
    
    return _router_instance


def reset_router():
    """重置全局路由器（用于测试）"""
    global _router_instance
    _router_instance = None
