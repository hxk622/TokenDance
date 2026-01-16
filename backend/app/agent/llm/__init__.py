"""
LLM 客户端模块
"""
from .base import BaseLLM, LLMMessage, LLMResponse
from .anthropic import ClaudeLLM, create_claude_llm
from .qwen import QwenLLM, create_qwen_llm
from .openrouter import OpenRouterLLM, create_openrouter_llm

# 路由器
from .router import SimpleRouter, TaskType, get_llm_for_task
from .advanced_router import AdvancedRouter, RoutingConstraints, get_llm_with_constraints
from .adaptive_router import AdaptiveRouter
from .unified_router import UnifiedRouter, FallbackConfig, get_router
from .vision_router import VisionRouter, VisionTaskType, get_vision_model

__all__ = [
    # 基础 LLM
    "BaseLLM",
    "LLMMessage",
    "LLMResponse",
    "ClaudeLLM",
    "create_claude_llm",
    "QwenLLM",
    "create_qwen_llm",
    "OpenRouterLLM",
    "create_openrouter_llm",
    # 路由器
    "SimpleRouter",
    "AdvancedRouter",
    "AdaptiveRouter",
    "UnifiedRouter",
    "VisionRouter",
    "TaskType",
    "VisionTaskType",
    "RoutingConstraints",
    "FallbackConfig",
    # 便捷函数
    "get_llm_for_task",
    "get_llm_with_constraints",
    "get_router",
    "get_vision_model",
]
