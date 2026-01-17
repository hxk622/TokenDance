"""
Vision Router - 视觉任务智能路由器

专门用于图像理解、OCR、图表分析等视觉任务的模型选择。
根据任务类型、成本约束、质量要求智能选择最优 Vision 模型。

支持的视觉模型：
- Claude 3 Opus (最强理解力，贵)
- Claude 3.5 Sonnet (平衡)
- Claude 3 Haiku (快速廉价，适合 OCR)
- Gemini Pro Vision (极致性价比)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class VisionTaskType(str, Enum):
    """视觉任务类型枚举"""

    OCR_TEXT = "ocr_text"              # 文字提取（扫描件、发票等）
    CHART_ANALYSIS = "chart_analysis"  # 图表分析（折线图、柱状图等）
    DIAGRAM = "diagram"                # 科学示意图、流程图
    SCREENSHOT = "screenshot"          # 屏幕截图理解
    GENERAL_IMAGE = "general_image"    # 通用图像理解
    MULTIMODAL_DOC = "multimodal_doc"  # 复杂多模态文档（PDF with images）


@dataclass
class VisionModelConfig:
    """视觉模型配置"""

    name: str
    cost_per_1m_tokens_input: float
    cost_per_1m_tokens_output: float
    avg_latency_ms: int
    max_image_size: int  # MB
    capabilities: list[str]
    quality_score: int  # 1-10, 10 最高


class VisionRouter:
    """
    视觉任务智能路由器

    根据任务类型、成本约束、质量需求选择最优 Vision 模型。
    """

    # Vision 模型注册表
    MODELS = {
        "anthropic/claude-3-opus": VisionModelConfig(
            name="anthropic/claude-3-opus",
            cost_per_1m_tokens_input=15.0,
            cost_per_1m_tokens_output=75.0,
            avg_latency_ms=4000,
            max_image_size=32,
            capabilities=["ocr", "chart", "diagram", "screenshot", "general", "multimodal"],
            quality_score=10
        ),
        "anthropic/claude-3-5-sonnet": VisionModelConfig(
            name="anthropic/claude-3-5-sonnet",
            cost_per_1m_tokens_input=3.0,
            cost_per_1m_tokens_output=15.0,
            avg_latency_ms=2500,
            max_image_size=32,
            capabilities=["ocr", "chart", "diagram", "screenshot", "general", "multimodal"],
            quality_score=9
        ),
        "anthropic/claude-3-haiku": VisionModelConfig(
            name="anthropic/claude-3-haiku",
            cost_per_1m_tokens_input=0.25,
            cost_per_1m_tokens_output=1.25,
            avg_latency_ms=1200,
            max_image_size=25,
            capabilities=["ocr", "screenshot", "general"],
            quality_score=7
        ),
        "google/gemini-pro-vision": VisionModelConfig(
            name="google/gemini-pro-vision",
            cost_per_1m_tokens_input=0.125,
            cost_per_1m_tokens_output=0.375,
            avg_latency_ms=1800,
            max_image_size=20,
            capabilities=["ocr", "chart", "general"],
            quality_score=8
        )
    }

    # 任务类型 → 推荐模型映射（按优先级）
    TASK_TO_MODELS = {
        VisionTaskType.OCR_TEXT: [
            "anthropic/claude-3-haiku",      # 首选：快速便宜
            "google/gemini-pro-vision",      # 备选：更便宜
            "anthropic/claude-3-5-sonnet"    # 降级：如果上面失败
        ],
        VisionTaskType.CHART_ANALYSIS: [
            "anthropic/claude-3-5-sonnet",   # 首选：平衡准确性和成本
            "anthropic/claude-3-opus",       # 升级：复杂图表
            "google/gemini-pro-vision"       # 降级：成本敏感
        ],
        VisionTaskType.DIAGRAM: [
            "anthropic/claude-3-5-sonnet",   # 首选：科学理解力强
            "anthropic/claude-3-opus",       # 升级：极复杂示意图
            "google/gemini-pro-vision"       # 降级：简单流程图
        ],
        VisionTaskType.SCREENSHOT: [
            "anthropic/claude-3-haiku",      # 首选：UI 理解足够
            "anthropic/claude-3-5-sonnet",   # 升级：复杂界面
        ],
        VisionTaskType.GENERAL_IMAGE: [
            "google/gemini-pro-vision",      # 首选：性价比之王
            "anthropic/claude-3-5-sonnet",   # 升级：需要细节
            "anthropic/claude-3-opus"        # 升级：艺术品分析
        ],
        VisionTaskType.MULTIMODAL_DOC: [
            "anthropic/claude-3-opus",       # 首选：最强多模态
            "anthropic/claude-3-5-sonnet"    # 降级：成本考虑
        ]
    }

    @classmethod
    def select_model(
        cls,
        task_type: VisionTaskType | str,
        max_cost: float | None = None,
        min_quality: int | None = None,
        max_latency_ms: int | None = None,
        prefer_speed: bool = False
    ) -> str:
        """
        选择最适合的视觉模型

        Args:
            task_type: 任务类型
            max_cost: 最大成本限制（$/1M tokens input）
            min_quality: 最低质量要求（1-10）
            max_latency_ms: 最大延迟限制（毫秒）
            prefer_speed: 是否优先速度

        Returns:
            str: 模型名称
        """
        # 类型转换
        if isinstance(task_type, str):
            try:
                task_type = VisionTaskType(task_type)
            except ValueError:
                logger.warning(f"Unknown task type: {task_type}, using GENERAL_IMAGE")
                task_type = VisionTaskType.GENERAL_IMAGE

        # 获取候选模型列表
        candidates = cls.TASK_TO_MODELS.get(
            task_type,
            ["anthropic/claude-3-5-sonnet"]  # 默认
        )

        # 过滤符合约束的模型
        valid_models = []
        for model_name in candidates:
            config = cls.MODELS.get(model_name)
            if not config:
                continue

            # 检查成本约束
            if max_cost and config.cost_per_1m_tokens_input > max_cost:
                logger.debug(f"Model {model_name} exceeds cost limit: {config.cost_per_1m_tokens_input} > {max_cost}")
                continue

            # 检查质量约束
            if min_quality and config.quality_score < min_quality:
                logger.debug(f"Model {model_name} below quality requirement: {config.quality_score} < {min_quality}")
                continue

            # 检查延迟约束
            if max_latency_ms and config.avg_latency_ms > max_latency_ms:
                logger.debug(f"Model {model_name} exceeds latency limit: {config.avg_latency_ms} > {max_latency_ms}")
                continue

            valid_models.append((model_name, config))

        # 如果没有符合条件的模型，返回最便宜的
        if not valid_models:
            logger.warning(
                f"No models match constraints for {task_type}. "
                f"Falling back to cheapest option."
            )
            return "anthropic/claude-3-haiku"

        # 选择策略
        if prefer_speed:
            # 按延迟排序
            valid_models.sort(key=lambda x: x[1].avg_latency_ms)
        else:
            # 按质量/成本比排序（默认策略）
            valid_models.sort(
                key=lambda x: x[1].quality_score / x[1].cost_per_1m_tokens_input,
                reverse=True
            )

        selected_model = valid_models[0][0]
        logger.info(
            f"Selected Vision model for {task_type}: {selected_model} "
            f"(quality: {valid_models[0][1].quality_score}, "
            f"cost: ${valid_models[0][1].cost_per_1m_tokens_input}/1M tokens)"
        )

        return selected_model

    @classmethod
    def estimate_cost(
        cls,
        model_name: str,
        num_images: int = 1,
        avg_tokens_per_image: int = 1000,
        output_tokens: int = 500
    ) -> dict[str, Any]:
        """
        估算视觉任务成本

        Args:
            model_name: 模型名称
            num_images: 图片数量
            avg_tokens_per_image: 每张图片平均 token 数（默认 1000）
            output_tokens: 输出 token 数

        Returns:
            dict: 成本估算信息
        """
        config = cls.MODELS.get(model_name)
        if not config:
            return {"error": f"Unknown model: {model_name}"}

        input_tokens = num_images * avg_tokens_per_image
        input_cost = (input_tokens / 1_000_000) * config.cost_per_1m_tokens_input
        output_cost = (output_tokens / 1_000_000) * config.cost_per_1m_tokens_output
        total_cost = input_cost + output_cost

        return {
            "model": model_name,
            "num_images": num_images,
            "estimated_input_tokens": input_tokens,
            "estimated_output_tokens": output_tokens,
            "input_cost_usd": round(input_cost, 6),
            "output_cost_usd": round(output_cost, 6),
            "total_cost_usd": round(total_cost, 6),
            "estimated_latency_ms": config.avg_latency_ms
        }

    @classmethod
    def get_model_info(cls, model_name: str) -> dict[str, Any] | None:
        """获取模型详细信息"""
        config = cls.MODELS.get(model_name)
        if not config:
            return None

        return {
            "name": config.name,
            "cost_per_1m_input": config.cost_per_1m_tokens_input,
            "cost_per_1m_output": config.cost_per_1m_tokens_output,
            "avg_latency_ms": config.avg_latency_ms,
            "max_image_size_mb": config.max_image_size,
            "capabilities": config.capabilities,
            "quality_score": config.quality_score
        }

    @classmethod
    def list_models_by_task(cls, task_type: VisionTaskType | str) -> list[str]:
        """列出某任务类型的所有推荐模型"""
        if isinstance(task_type, str):
            try:
                task_type = VisionTaskType(task_type)
            except ValueError:
                return []

        return cls.TASK_TO_MODELS.get(task_type, [])


# 便捷函数
def get_vision_model(
    task_type: VisionTaskType | str = VisionTaskType.GENERAL_IMAGE,
    **kwargs
) -> str:
    """
    快速获取视觉模型

    Args:
        task_type: 任务类型
        **kwargs: 传递给 VisionRouter.select_model 的其他参数

    Returns:
        str: 模型名称
    """
    return VisionRouter.select_model(task_type, **kwargs)
