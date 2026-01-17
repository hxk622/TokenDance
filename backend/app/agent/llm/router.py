"""
LLM 路由器模块

提供智能模型选择策略，根据任务类型、预算、延迟等因素选择最优 LLM
"""
import logging
from enum import Enum

from .anthropic import create_claude_llm
from .base import BaseLLM
from .openrouter import create_openrouter_llm
from .vision_router import VisionRouter

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """任务类型枚举"""
    DEEP_RESEARCH = "deep_research"           # 深度研究
    FINANCIAL_ANALYSIS = "financial_analysis" # 金融投研
    PPT_GENERATION = "ppt_generation"         # PPT 生成
    CODE_GENERATION = "code_generation"       # 代码生成
    QUICK_QA = "quick_qa"                     # 快速问答
    MULTIMODAL = "multimodal"                 # 多模态（图像，使用 VisionRouter 细化）
    GENERAL = "general"                       # 通用任务


class ModelConfig:
    """模型配置"""
    def __init__(
        self,
        name: str,
        provider: str,
        cost_per_1k_input: float,
        cost_per_1k_output: float,
        context_window: int,
        avg_latency_ms: float = 2000,
        capabilities: list[str] = None
    ):
        self.name = name
        self.provider = provider
        self.cost_per_1k_input = cost_per_1k_input
        self.cost_per_1k_output = cost_per_1k_output
        self.context_window = context_window
        self.avg_latency_ms = avg_latency_ms
        self.capabilities = capabilities or []


# 模型配置表
MODEL_REGISTRY = {
    "anthropic/claude-3-opus": ModelConfig(
        name="anthropic/claude-3-opus",
        provider="openrouter",
        cost_per_1k_input=15.0,
        cost_per_1k_output=75.0,
        context_window=200000,
        avg_latency_ms=3000,
        capabilities=["reasoning", "coding", "analysis"]
    ),
    "anthropic/claude-3-5-sonnet": ModelConfig(
        name="anthropic/claude-3-5-sonnet",
        provider="openrouter",
        cost_per_1k_input=3.0,
        cost_per_1k_output=15.0,
        context_window=200000,
        avg_latency_ms=2000,
        capabilities=["reasoning", "coding", "analysis", "balanced"]
    ),
    "anthropic/claude-3-haiku": ModelConfig(
        name="anthropic/claude-3-haiku",
        provider="openrouter",
        cost_per_1k_input=0.25,
        cost_per_1k_output=1.25,
        context_window=200000,
        avg_latency_ms=800,
        capabilities=["fast", "cheap", "simple_qa"]
    ),
    "deepseek/deepseek-coder": ModelConfig(
        name="deepseek/deepseek-coder",
        provider="openrouter",
        cost_per_1k_input=0.14,
        cost_per_1k_output=0.28,
        context_window=64000,
        avg_latency_ms=1500,
        capabilities=["coding", "cheap"]
    ),
    "google/gemini-pro-vision": ModelConfig(
        name="google/gemini-pro-vision",
        provider="openrouter",
        cost_per_1k_input=0.125,
        cost_per_1k_output=0.375,
        context_window=30720,
        avg_latency_ms=2500,
        capabilities=["multimodal", "vision"]
    ),
}


class SimpleRouter:
    """简单规则路由器

    基于任务类型选择最优模型
    适用于快速开始，工作量小，立即见效
    """

    # 任务类型 -> 模型映射
    TASK_MODEL_MAP = {
        TaskType.DEEP_RESEARCH: "anthropic/claude-3-opus",         # 最强推理
        TaskType.FINANCIAL_ANALYSIS: "anthropic/claude-3-5-sonnet", # 平衡性能
        TaskType.PPT_GENERATION: "anthropic/claude-3-5-sonnet",    # 创意 + 结构化
        TaskType.CODE_GENERATION: "deepseek/deepseek-coder",       # 代码专精
        TaskType.QUICK_QA: "anthropic/claude-3-haiku",             # 快速便宜
        TaskType.MULTIMODAL: "google/gemini-pro-vision",           # 图像理解
        TaskType.GENERAL: "anthropic/claude-3-5-sonnet",           # 通用场景
    }

    def __init__(self, use_openrouter: bool = True):
        """
        Args:
            use_openrouter: 是否使用 OpenRouter（统一网关）还是直连各家 API
        """
        self.use_openrouter = use_openrouter
        logger.info(f"SimpleRouter initialized (use_openrouter={use_openrouter})")

    def select_model(
        self,
        task_type: TaskType | str,
        vision_task_type: str | None = None,
        **kwargs
    ) -> str:
        """选择最优模型

        Args:
            task_type: 任务类型
            vision_task_type: 视觉子任务类型（当 task_type=MULTIMODAL 时使用）
            **kwargs: 其他参数，传递给 VisionRouter

        Returns:
            str: 模型名称
        """
        # 支持字符串类型
        if isinstance(task_type, str):
            try:
                task_type = TaskType(task_type)
            except ValueError:
                logger.warning(f"Unknown task type: {task_type}, using GENERAL")
                task_type = TaskType.GENERAL

        # 如果是多模态任务，使用 VisionRouter
        if task_type == TaskType.MULTIMODAL:
            if vision_task_type:
                model = VisionRouter.select_model(
                    task_type=vision_task_type,
                    **kwargs  # 传递 max_cost, min_quality 等
                )
                logger.info(
                    f"Selected Vision model '{model}' for "
                    f"vision_task_type '{vision_task_type}'"
                )
                return model
            else:
                # 默认通用视觉模型
                return self.TASK_MODEL_MAP[TaskType.MULTIMODAL]

        # 文本任务，使用传统映射
        model = self.TASK_MODEL_MAP.get(task_type, self.TASK_MODEL_MAP[TaskType.GENERAL])
        logger.info(f"Selected model '{model}' for task type '{task_type.value}'")
        return model

    def create_llm(
        self,
        task_type: TaskType | str,
        **llm_kwargs
    ) -> BaseLLM:
        """创建 LLM 客户端

        Args:
            task_type: 任务类型
            **llm_kwargs: 传递给 LLM 构造函数的参数（如 temperature, max_tokens）

        Returns:
            BaseLLM: LLM 客户端实例
        """
        model = self.select_model(task_type)

        if self.use_openrouter:
            return create_openrouter_llm(model=model, **llm_kwargs)
        else:
            # 直连 API（当前只支持 Claude）
            if "anthropic" in model:
                return create_claude_llm(**llm_kwargs)
            else:
                # 其他模型回退到 OpenRouter
                logger.warning(f"Model {model} not supported for direct API, using OpenRouter")
                return create_openrouter_llm(model=model, **llm_kwargs)

    def get_model_info(self, model_name: str) -> ModelConfig:
        """获取模型配置信息

        Args:
            model_name: 模型名称

        Returns:
            ModelConfig: 模型配置
        """
        return MODEL_REGISTRY.get(model_name)

    def estimate_cost(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """估算调用成本

        Args:
            model_name: 模型名称
            input_tokens: 输入 token 数
            output_tokens: 输出 token 数

        Returns:
            float: 成本（USD）
        """
        config = self.get_model_info(model_name)
        if not config:
            return 0.0

        cost = (
            (input_tokens / 1000) * config.cost_per_1k_input +
            (output_tokens / 1000) * config.cost_per_1k_output
        )
        return round(cost, 6)


# 便捷函数
def get_llm_for_task(
    task_type: TaskType | str,
    use_openrouter: bool = True,
    **llm_kwargs
) -> BaseLLM:
    """快捷方式：根据任务类型获取 LLM

    Args:
        task_type: 任务类型
        use_openrouter: 是否使用 OpenRouter
        **llm_kwargs: LLM 参数

    Returns:
        BaseLLM: LLM 客户端实例

    Example:
        >>> llm = get_llm_for_task("deep_research")
        >>> llm = get_llm_for_task(TaskType.QUICK_QA, temperature=0.7)
    """
    router = SimpleRouter(use_openrouter=use_openrouter)
    return router.create_llm(task_type, **llm_kwargs)
