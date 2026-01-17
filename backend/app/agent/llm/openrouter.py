"""
OpenRouter LLM 客户端实现

OpenRouter 是一个 LLM 网关服务，提供统一接口访问多家 LLM 提供商
支持 Claude、GPT、Gemini 等模型，通过单一 API Key 调用
"""
import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from .base import BaseLLM, LLMMessage, LLMResponse

logger = logging.getLogger(__name__)


class OpenRouterLLM(BaseLLM):
    """OpenRouter API 客户端

    通过 OpenRouter 网关调用各种 LLM 模型
    兼容 OpenAI Chat Completions API 格式
    """

    def __init__(
        self,
        api_key: str,
        model: str = "anthropic/claude-3-5-sonnet",
        max_tokens: int = 4096,
        temperature: float = 1.0,
        base_url: str = "https://openrouter.ai/api/v1",
        site_url: str | None = None,
        app_name: str | None = None
    ):
        super().__init__(api_key, model, max_tokens, temperature)

        self.base_url = base_url
        self.site_url = site_url or "https://tokendance.ai"
        self.app_name = app_name or "TokenDance"

        # 构造请求头
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.app_name,
        }

        logger.info(f"OpenRouterLLM initialized with model: {model}")

    async def complete(
        self,
        messages: list[LLMMessage],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        stop_sequences: list[str] | None = None
    ) -> LLMResponse:
        """完整调用 OpenRouter API

        Args:
            messages: 消息列表
            system: 系统提示词
            tools: 工具定义列表 (OpenAI function calling 格式)
            max_tokens: 最大输出 token 数
            temperature: 温度参数
            stop_sequences: 停止序列

        Returns:
            LLMResponse: 完整响应
        """
        params = self._merge_params(max_tokens, temperature)

        # 构造 OpenAI Chat Completions API 格式
        formatted_messages = self._format_messages(messages, system)

        api_params = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": params["max_tokens"],
            "temperature": params["temperature"],
            "stream": False,
        }

        if tools:
            api_params["functions"] = self._format_tools(tools)
            api_params["function_call"] = "auto"

        if stop_sequences:
            api_params["stop"] = stop_sequences

        # 调用 API
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=api_params
            )
            response.raise_for_status()
            data = response.json()  # httpx response.json() is synchronous

        # 解析响应
        choice = data["choices"][0]
        message = choice["message"]

        content = message.get("content", "")
        tool_calls = []

        # 处理 function calling
        if "function_call" in message:
            func_call = message["function_call"]
            tool_calls.append({
                "id": f"call_{hash(func_call['name'])}",  # 生成虚拟 ID
                "name": func_call["name"],
                "input": json.loads(func_call["arguments"])
            })

        # 处理使用量信息
        usage = None
        if "usage" in data:
            usage = {
                "input_tokens": data["usage"]["prompt_tokens"],
                "output_tokens": data["usage"]["completion_tokens"]
            }

        return LLMResponse(
            content=content,
            tool_calls=tool_calls if tool_calls else None,
            stop_reason=choice["finish_reason"],
            usage=usage
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
        """流式调用 OpenRouter API

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
        formatted_messages = self._format_messages(messages, system)

        api_params = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": params["max_tokens"],
            "temperature": params["temperature"],
            "stream": True,
        }

        if tools:
            api_params["functions"] = self._format_tools(tools)
            api_params["function_call"] = "auto"

        if stop_sequences:
            api_params["stop"] = stop_sequences

        # 流式调用
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=api_params
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        chunk_data = line[6:]  # 移除 "data: " 前缀

                        if chunk_data == "[DONE]":
                            break

                        try:
                            chunk = json.loads(chunk_data)
                            if "choices" in chunk and chunk["choices"]:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue

    def _format_messages(
        self,
        messages: list[Any],
        system: str | None = None
    ) -> list[dict[str, str]]:
        """格式化消息为 OpenAI Chat Completions API 格式

        Args:
            messages: 消息列表（LLMMessage 或 dict）
            system: 系统提示词

        Returns:
            List[Dict]: OpenAI API 消息格式
        """
        formatted = []

        # 添加系统消息
        if system:
            formatted.append({"role": "system", "content": system})

        # 添加对话消息
        for msg in messages:
            # 支持 dict 和 LLMMessage 两种格式
            if isinstance(msg, dict):
                role = msg.get("role")
                content = msg.get("content")
            else:
                role = msg.role
                content = msg.content

            # 过滤已经处理的 system 消息
            if role != "system":
                formatted.append({"role": role, "content": content})

        return formatted

    def _format_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """将 Claude Tool Use 格式转换为 OpenAI Function Calling 格式

        Args:
            tools: Claude 格式工具列表

        Returns:
            List[Dict]: OpenAI functions 格式
        """
        functions = []
        for tool in tools:
            if tool.get("type") == "function":
                functions.append({
                    "name": tool["function"]["name"],
                    "description": tool["function"].get("description", ""),
                    "parameters": tool["function"].get("parameters", {})
                })
        return functions


# 便捷函数
def create_openrouter_llm(
    api_key: str | None = None,
    model: str | None = None,
    max_tokens: int = 4096,
    temperature: float = 1.0,
    base_url: str | None = None,
    site_url: str | None = None,
    app_name: str | None = None
) -> OpenRouterLLM:
    """创建 OpenRouterLLM 实例

    支持从环境变量读取配置：
    - OPENROUTER_API_KEY: API Key
    - OPENROUTER_MODEL: 模型名称
    - OPENROUTER_BASE_URL: API Base URL
    - OPENROUTER_SITE_URL: 站点 URL
    - OPENROUTER_APP_NAME: 应用名称

    Args:
        api_key: OpenRouter API Key（如果为 None，从环境变量读取）
        model: 模型名称（如果为 None，从环境变量读取）
        max_tokens: 最大输出 token 数
        temperature: 温度参数
        base_url: API Base URL
        site_url: 站点 URL
        app_name: 应用名称

    Returns:
        OpenRouterLLM: OpenRouter LLM 实例
    """
    import os

    # 读取 API Key
    if api_key is None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("API Key not found. Set OPENROUTER_API_KEY environment variable")

    # 读取模型名称
    if model is None:
        model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3-5-sonnet")

    # 读取其他配置
    if base_url is None:
        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    if site_url is None:
        site_url = os.getenv("OPENROUTER_SITE_URL", "https://tokendance.ai")

    if app_name is None:
        app_name = os.getenv("OPENROUTER_APP_NAME", "TokenDance")

    return OpenRouterLLM(
        api_key=api_key,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        base_url=base_url,
        site_url=site_url,
        app_name=app_name
    )
