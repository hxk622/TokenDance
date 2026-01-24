"""
LLM 客户端基类
"""
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel


class ImageContent(BaseModel):
    """图片内容（用于多模态消息）"""
    type: str = "image_url"
    image_url: dict[str, str]  # {"url": "data:image/png;base64,..."}


class TextContent(BaseModel):
    """文本内容（用于多模态消息）"""
    type: str = "text"
    text: str


# 多模态消息内容类型
MultimodalContent = list[TextContent | ImageContent]


class LLMMessage(BaseModel):
    """LLM 消息格式

    支持两种 content 格式：
    1. 纯文本: content = "Hello"
    2. 多模态: content = [{"type": "text", "text": ".."}, {"type": "image_url", "image_url": {...}}]
    """
    role: str  # "user" | "assistant" | "system"
    content: str | MultimodalContent  # 支持纯文本或多模态内容


@dataclass
class LLMResponse:
    """LLM 完整响应"""
    content: str
    tool_calls: list[dict[str, Any]] | None = None
    stop_reason: str | None = None  # "end_turn" | "tool_use" | "max_tokens"
    usage: dict[str, int] | None = None  # {"input_tokens": 123, "output_tokens": 456}
    thinking: str | None = None  # DeepSeek R1 等模型的 reasoning/thinking 内容


class BaseLLM(ABC):
    """LLM 客户端抽象基类

    所有 LLM 客户端（Claude、Gemini 等）必须继承此类
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        max_tokens: int = 4096,
        temperature: float = 1.0
    ):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    @abstractmethod
    async def complete(
        self,
        messages: list[LLMMessage],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        stop_sequences: list[str] | None = None
    ) -> LLMResponse:
        """完整调用 LLM

        Args:
            messages: 消息列表
            system: 系统提示词
            tools: 工具定义列表（Claude Tool Use 格式）
            max_tokens: 最大输出 token 数
            temperature: 温度参数
            stop_sequences: 停止序列

        Returns:
            LLMResponse: 完整响应
        """
        pass

    @abstractmethod
    async def stream(
        self,
        messages: list[LLMMessage],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        stop_sequences: list[str] | None = None
    ) -> AsyncGenerator[str, None]:
        """流式调用 LLM

        Args:
            messages: 消息列表
            system: 系统提示词
            tools: 工具定义列表
            max_tokens: 最大输出 token 数
            temperature: 温度参数
            stop_sequences: 停止序列

        Yields:
            str: 流式文本块
        """
        pass

    def _merge_params(
        self,
        max_tokens: int | None,
        temperature: float | None
    ) -> dict[str, Any]:
        """合并默认参数和传入参数

        Args:
            max_tokens: 传入的 max_tokens
            temperature: 传入的 temperature

        Returns:
            Dict: 合并后的参数
        """
        return {
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
            "temperature": temperature if temperature is not None else self.temperature
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(model='{self.model}')>"
