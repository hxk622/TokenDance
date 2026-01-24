"""
LLM 客户端模块
"""
from .adaptive_router import AdaptiveRouter
from .advanced_router import AdvancedRouter, RoutingConstraints, get_llm_with_constraints
from .anthropic import ClaudeLLM
from .base import BaseLLM, ImageContent, LLMMessage, LLMResponse, MultimodalContent, TextContent
from .openrouter import OpenRouterLLM, create_openrouter_llm
from .qwen import QwenLLM, create_qwen_llm
from .siliconflow import (
    SILICONFLOW_FREE_MODELS,
    SILICONFLOW_PAID_MODELS,
    SiliconFlowLLM,
    create_siliconflow_llm,
    get_siliconflow_best_model,
    get_siliconflow_free_model,
    is_siliconflow_free_model,
)

# 路由器
from .router import FreeModelRouter, SimpleRouter, TaskType, get_free_llm_for_task, get_llm_for_task
from .unified_router import FallbackConfig, UnifiedRouter, get_router
from .vision_router import VisionRouter, VisionTaskType, get_vision_model

__all__ = [
    # 基础 LLM
    "BaseLLM",
    "LLMMessage",
    "LLMResponse",
    "TextContent",
    "ImageContent",
    "MultimodalContent",
    "ClaudeLLM",
    "QwenLLM",
    "create_qwen_llm",
    "OpenRouterLLM",
    "create_openrouter_llm",
    # SiliconFlow
    "SiliconFlowLLM",
    "create_siliconflow_llm",
    "get_siliconflow_free_model",
    "get_siliconflow_best_model",
    "is_siliconflow_free_model",
    "SILICONFLOW_FREE_MODELS",
    "SILICONFLOW_PAID_MODELS",
    # 路由器
    "SimpleRouter",
    "FreeModelRouter",
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
    "get_free_llm_for_task",
    "get_llm_with_constraints",
    "get_router",
    "get_vision_model",
]
