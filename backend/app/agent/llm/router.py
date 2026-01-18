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
    # ============ 付费模型 ============
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

    # ============ 免费模型 (OpenRouter Free Tier) ============
    # 通用推理 - 强力推荐
    "deepseek/deepseek-r1:free": ModelConfig(
        name="deepseek/deepseek-r1:free",
        provider="openrouter",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        context_window=128000,
        avg_latency_ms=3000,
        capabilities=["reasoning", "analysis", "free", "thinking"]
    ),
    "deepseek/deepseek-chat-v3-0324:free": ModelConfig(
        name="deepseek/deepseek-chat-v3-0324:free",
        provider="openrouter",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        context_window=128000,
        avg_latency_ms=2000,
        capabilities=["reasoning", "coding", "balanced", "free"]
    ),
    # 代码生成 - 专业编码
    "mistralai/devstral-2:free": ModelConfig(
        name="mistralai/devstral-2:free",
        provider="openrouter",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        context_window=128000,
        avg_latency_ms=2500,
        capabilities=["coding", "agentic", "free"]
    ),
    # 超长上下文 - 1M tokens
    "google/gemini-2.0-flash-exp:free": ModelConfig(
        name="google/gemini-2.0-flash-exp:free",
        provider="openrouter",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        context_window=1000000,
        avg_latency_ms=1500,
        capabilities=["fast", "long_context", "balanced", "free"]
    ),
    # 通用对话 - Llama 系列
    "meta-llama/llama-3.3-70b-instruct:free": ModelConfig(
        name="meta-llama/llama-3.3-70b-instruct:free",
        provider="openrouter",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        context_window=128000,
        avg_latency_ms=2000,
        capabilities=["reasoning", "coding", "balanced", "free"]
    ),
    "meta-llama/llama-4-maverick:free": ModelConfig(
        name="meta-llama/llama-4-maverick:free",
        provider="openrouter",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        context_window=256000,
        avg_latency_ms=2000,
        capabilities=["reasoning", "coding", "balanced", "free"]
    ),
    # 快速响应
    "mistralai/mistral-small-3.1-24b-instruct:free": ModelConfig(
        name="mistralai/mistral-small-3.1-24b-instruct:free",
        provider="openrouter",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        context_window=128000,
        avg_latency_ms=1000,
        capabilities=["fast", "simple_qa", "free"]
    ),
    # 中文优化
    "zhipu/glm-4.5-air:free": ModelConfig(
        name="zhipu/glm-4.5-air:free",
        provider="openrouter",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        context_window=128000,
        avg_latency_ms=1500,
        capabilities=["reasoning", "chinese", "agentic", "free"]
    ),
    # 小米 MiMo - 309B MoE
    "xiaomi/mimo-v2-flash:free": ModelConfig(
        name="xiaomi/mimo-v2-flash:free",
        provider="openrouter",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        context_window=256000,
        avg_latency_ms=2000,
        capabilities=["reasoning", "coding", "agentic", "free", "thinking"]
    ),
    # OpenRouter 官方模型
    "openrouter/optimus-alpha": ModelConfig(
        name="openrouter/optimus-alpha",
        provider="openrouter",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        context_window=128000,
        avg_latency_ms=1500,
        capabilities=["balanced", "fast", "free"]
    ),
    "openrouter/quasar-alpha": ModelConfig(
        name="openrouter/quasar-alpha",
        provider="openrouter",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        context_window=128000,
        avg_latency_ms=2000,
        capabilities=["reasoning", "analysis", "free"]
    ),
    # 轻量级模型
    "nvidia/llama-3.1-nemotron-nano-8b-v1:free": ModelConfig(
        name="nvidia/llama-3.1-nemotron-nano-8b-v1:free",
        provider="openrouter",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        context_window=128000,
        avg_latency_ms=500,
        capabilities=["fast", "simple_qa", "free"]
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


class FreeModelRouter(SimpleRouter):
    """免费模型优先路由器

    优先使用 OpenRouter 免费模型，节省成本
    支持 fallback 策略和智能调度
    """

    # 免费模型任务映射 - 按任务类型推荐最佳免费模型 (2026-01 更新)
    FREE_TASK_MODEL_MAP = {
        TaskType.DEEP_RESEARCH: "deepseek/deepseek-r1-0528:free",       # 深度推理
        TaskType.FINANCIAL_ANALYSIS: "deepseek/deepseek-r1-0528:free",  # 分析任务
        TaskType.PPT_GENERATION: "meta-llama/llama-3.3-70b-instruct:free",  # 创意生成
        TaskType.CODE_GENERATION: "deepseek/deepseek-r1-0528:free",     # 专业编码
        TaskType.QUICK_QA: "xiaomi/mimo-v2-flash:free",                 # 快速响应
        TaskType.MULTIMODAL: "xiaomi/mimo-v2-flash:free",               # 多模态
        TaskType.GENERAL: "meta-llama/llama-3.3-70b-instruct:free",     # 通用
    }

    # Fallback 链 - 当主模型不可用时的备选 (2026-01 更新)
    FREE_FALLBACK_CHAIN = [
        "deepseek/deepseek-r1-0528:free",           # DeepSeek R1 - 推理强
        "meta-llama/llama-3.3-70b-instruct:free",   # Llama 3.3 - 通用
        "xiaomi/mimo-v2-flash:free",                # MiMo - 快速
        "z-ai/glm-4.5-air:free",                    # GLM - 中文友好
    ]

    def __init__(self, use_free_only: bool = True, fallback_to_paid: bool = False):
        """
        Args:
            use_free_only: 是否仅使用免费模型
            fallback_to_paid: 当免费模型都不可用时是否回退到付费模型
        """
        super().__init__(use_openrouter=True)
        self.use_free_only = use_free_only
        self.fallback_to_paid = fallback_to_paid
        logger.info(f"FreeModelRouter initialized (use_free_only={use_free_only})")

    def select_model(
        self,
        task_type: TaskType | str,
        context_length: int = 0,
        prefer_speed: bool = False,
        prefer_chinese: bool = False,
        **kwargs
    ) -> str:
        """智能选择免费模型

        Args:
            task_type: 任务类型
            context_length: 上下文长度（用于选择支持长上下文的模型）
            prefer_speed: 是否优先选择快速模型
            prefer_chinese: 是否优先选择中文优化模型

        Returns:
            str: 模型名称
        """
        if isinstance(task_type, str):
            try:
                task_type = TaskType(task_type)
            except ValueError:
                task_type = TaskType.GENERAL

        # 特殊场景处理
        if context_length > 200000:
            # 超长上下文 -> MiMo (256K)
            logger.info(f"Long context ({context_length} tokens), using MiMo v2 Flash")
            return "xiaomi/mimo-v2-flash:free"

        if prefer_speed:
            logger.info("Speed preferred, using MiMo v2 Flash")
            return "xiaomi/mimo-v2-flash:free"

        if prefer_chinese:
            logger.info("Chinese preferred, using GLM-4.5-Air")
            return "z-ai/glm-4.5-air:free"

        # 按任务类型选择
        model = self.FREE_TASK_MODEL_MAP.get(
            task_type,
            self.FREE_TASK_MODEL_MAP[TaskType.GENERAL]
        )
        logger.info(f"Selected free model '{model}' for task type '{task_type.value}'")
        return model

    def get_fallback_models(self, primary_model: str) -> list[str]:
        """获取备选模型列表"""
        fallbacks = [m for m in self.FREE_FALLBACK_CHAIN if m != primary_model]
        if self.fallback_to_paid:
            # 添加付费模型作为最后备选
            fallbacks.extend([
                "anthropic/claude-3-haiku",
                "anthropic/claude-3-5-sonnet",
            ])
        return fallbacks

    @staticmethod
    def list_free_models() -> list[str]:
        """列出所有可用的免费模型"""
        return [
            name for name, config in MODEL_REGISTRY.items()
            if "free" in config.capabilities or config.cost_per_1k_input == 0.0
        ]


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


def get_free_llm_for_task(
    task_type: TaskType | str,
    context_length: int = 0,
    prefer_speed: bool = False,
    prefer_chinese: bool = False,
    **llm_kwargs
) -> BaseLLM:
    """快捷方式：获取免费 LLM

    Args:
        task_type: 任务类型
        context_length: 上下文长度
        prefer_speed: 是否优先速度
        prefer_chinese: 是否优先中文模型
        **llm_kwargs: LLM 参数

    Returns:
        BaseLLM: 免费 LLM 客户端实例

    Example:
        >>> # 深度研究任务
        >>> llm = get_free_llm_for_task("deep_research")

        >>> # 快速问答
        >>> llm = get_free_llm_for_task("quick_qa", prefer_speed=True)

        >>> # 中文场景
        >>> llm = get_free_llm_for_task("general", prefer_chinese=True)

        >>> # 超长文档
        >>> llm = get_free_llm_for_task("general", context_length=500000)
    """
    router = FreeModelRouter()
    model = router.select_model(
        task_type,
        context_length=context_length,
        prefer_speed=prefer_speed,
        prefer_chinese=prefer_chinese
    )

    # 打印模型选择日志
    logger.info(
        f"\n"
        f"========== LLM Router ==========\n"
        f"  Task Type: {task_type}\n"
        f"  Selected Model: {model}\n"
        f"  Context Length: {context_length}\n"
        f"  Prefer Speed: {prefer_speed}\n"
        f"  Prefer Chinese: {prefer_chinese}\n"
        f"================================"
    )

    return create_openrouter_llm(model=model, **llm_kwargs)
