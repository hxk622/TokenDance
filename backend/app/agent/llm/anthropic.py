"""
Claude LLM 客户端实现
"""
import logging
from collections.abc import AsyncGenerator
from typing import Any

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .base import BaseLLM, LLMMessage, LLMResponse

logger = logging.getLogger(__name__)


class ClaudeLLM(BaseLLM):
    """Claude API 客户端

    使用 Anthropic SDK 调用 Claude 3.5 Sonnet
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 8192,
        temperature: float = 1.0,
        base_url: str | None = None
    ):
        super().__init__(api_key, model, max_tokens, temperature)

        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic SDK not installed. "
                "Install with: pip install anthropic"
            )

        # 构造客户端参数
        client_params = {"api_key": api_key}
        if base_url:
            client_params["base_url"] = base_url

        self.client = anthropic.AsyncAnthropic(**client_params)
        logger.info(f"ClaudeLLM initialized with model: {model}, base_url: {base_url or 'default'}")

    async def complete(
        self,
        messages: list[LLMMessage],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        stop_sequences: list[str] | None = None
    ) -> LLMResponse:
        """完整调用 Claude API

        Args:
            messages: 消息列表
            system: 系统提示词
            tools: 工具定义列表
            max_tokens: 最大输出 token 数
            temperature: 温度参数
            stop_sequences: 停止序列

        Returns:
            LLMResponse: 完整响应
        """
        params = self._merge_params(max_tokens, temperature)

        # 构造 API 请求参数
        api_params = {
            "model": self.model,
            "max_tokens": params["max_tokens"],
            "temperature": params["temperature"],
            "messages": self._format_messages(messages),
        }

        if system:
            api_params["system"] = system

        if tools:
            api_params["tools"] = tools

        if stop_sequences:
            api_params["stop_sequences"] = stop_sequences

        # 调用 API
        response = await self.client.messages.create(**api_params)

        # 解析响应
        content = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })

        return LLMResponse(
            content=content,
            tool_calls=tool_calls if tool_calls else None,
            stop_reason=response.stop_reason,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
        )

    async def stream(
        self,
        messages: list[LLMMessage],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        stop_sequences: list[str] | None = None
    ) -> AsyncGenerator[str, None]:
        """流式调用 Claude API

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
        params = self._merge_params(max_tokens, temperature)

        # 构造 API 请求参数
        api_params = {
            "model": self.model,
            "max_tokens": params["max_tokens"],
            "temperature": params["temperature"],
            "messages": self._format_messages(messages),
        }

        if system:
            api_params["system"] = system

        if tools:
            api_params["tools"] = tools

        if stop_sequences:
            api_params["stop_sequences"] = stop_sequences

        # 流式调用
        async with self.client.messages.stream(**api_params) as stream:
            async for text in stream.text_stream:
                yield text

    def _format_messages(self, messages: list[Any]) -> list[dict[str, str]]:
        """格式化消息为 Claude API 格式

        支持两种输入格式：
        - LLMMessage 对象
        - Dict {"role": "...", "content": "..."}

        Args:
            messages: 消息列表（LLMMessage 或 dict）

        Returns:
            List[Dict]: Claude API 消息格式
        """
        formatted = []
        for msg in messages:
            # 支持 dict 和 LLMMessage 两种格式
            if isinstance(msg, dict):
                role = msg.get("role")
                content = msg.get("content")
            else:
                role = msg.role
                content = msg.content

            # 过滤 system 消息（system 单独传入）
            if role != "system":
                formatted.append({"role": role, "content": content})

        return formatted


# 便捷函数
def create_claude_llm(
    api_key: str | None = None,
    model: str | None = None,
    max_tokens: int = 8192,
    temperature: float = 1.0,
    base_url: str | None = None
) -> ClaudeLLM:
    """创建 ClaudeLLM 实例

    支持从环境变量读取配置：
    - ANTHROPIC_AUTH_TOKEN 或 ANTHROPIC_API_KEY: API Key
    - ANTHROPIC_API_MODEL: 模型名称
    - ANTHROPIC_BASE_URL: API Base URL

    Args:
        api_key: Anthropic API Key（如果为 None，从环境变量读取）
        model: 模型名称（如果为 None，从环境变量读取）
        max_tokens: 最大输出 token 数
        temperature: 温度参数
        base_url: API Base URL（如果为 None，从环境变量读取）

    Returns:
        ClaudeLLM: Claude LLM 实例
    """
    import os

    # 读取 API Key（支持两种环境变量）
    if api_key is None:
        api_key = os.getenv("ANTHROPIC_AUTH_TOKEN") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "API Key not found. Set ANTHROPIC_AUTH_TOKEN or ANTHROPIC_API_KEY"
            )

    # 读取模型名称
    if model is None:
        model = os.getenv("ANTHROPIC_API_MODEL", "claude-3-5-sonnet-20241022")

    # 读取 Base URL
    if base_url is None:
        base_url = os.getenv("ANTHROPIC_BASE_URL")

    return ClaudeLLM(
        api_key=api_key,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        base_url=base_url
    )


# 兼容别名 - 保持向后兼容
AnthropicLLM = ClaudeLLM
