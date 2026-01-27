"""
OpenRouter LLM 客户端实现

OpenRouter 是一个 LLM 网关服务，提供统一接口访问多家 LLM 提供商
支持 Claude、GPT、Gemini 等模型，通过单一 API Key 调用
"""
import asyncio
import json
import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from .base import BaseLLM, LLMMessage, LLMResponse

logger = logging.getLogger(__name__)

# Global rate limiting for OpenRouter API calls (applies to all instances)
_openrouter_last_call_time: float = 0.0
_openrouter_min_interval: float = 3.0  # Minimum 3 seconds between calls for free tier
_openrouter_call_lock = asyncio.Lock()


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

        # 构造 OpenAI Chat Completions 格式
        formatted_messages = self._format_messages(messages, system)

        api_params = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": params["max_tokens"],
            "temperature": params["temperature"],
            "stream": False,
        }

        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = "auto"

        if stop_sequences:
            api_params["stop"] = stop_sequences

        # 打印请求日志
        logger.info(f"[OpenRouter] Calling model: {self.model} | max_tokens: {params['max_tokens']}")

        # Global rate limiting for free tier accounts
        global _openrouter_last_call_time
        async with _openrouter_call_lock:
            elapsed = time.time() - _openrouter_last_call_time
            if elapsed < _openrouter_min_interval:
                wait_time = _openrouter_min_interval - elapsed
                logger.info(f"[OpenRouter] Rate limiting: waiting {wait_time:.1f}s before API call")
                await asyncio.sleep(wait_time)
            _openrouter_last_call_time = time.time()

        # 重试配置
        max_retries = 3
        base_delay = 2.0  # 初始延迟2秒 (increased for free tier)

        for attempt in range(max_retries):
            try:
                # 调用 API (disable SSL verification for macOS compatibility)
                async with httpx.AsyncClient(timeout=120.0, verify=False) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=self.headers,
                        json=api_params
                    )
                    response.raise_for_status()

                    # 安全解析 JSON 响应
                    try:
                        data = response.json()  # httpx response.json() is synchronous
                    except json.JSONDecodeError as e:
                        # 记录原始响应以便调试
                        raw_text = response.text[:500] if response.text else "(empty)"
                        logger.error(f"[OpenRouter] JSON decode error: {e}")
                        logger.error(f"[OpenRouter] Raw response (first 500 chars): {raw_text}")
                        raise ValueError(f"OpenRouter returned invalid JSON: {e}") from e

                    # 验证响应结构
                    if "choices" not in data or not data["choices"]:
                        logger.error(f"[OpenRouter] Invalid response structure: {data}")
                        raise ValueError(f"OpenRouter response missing 'choices': {data}")

                # 打印响应日志
                usage_info = data.get("usage", {})
                logger.info(
                    f"[OpenRouter] Response from {self.model} | "
                    f"tokens: {usage_info.get('prompt_tokens', '?')}/{usage_info.get('completion_tokens', '?')}"
                )

                # 解析响应
                choice = data["choices"][0]
                message = choice["message"]

                content = message.get("content", "")
                tool_calls = []

                # 解析 DeepSeek R1 等模型的 thinking/reasoning 内容
                thinking = None
                # DeepSeek R1 使用 reasoning_content 字段
                if "reasoning_content" in message:
                    thinking = message.get("reasoning_content", "")
                # 其他模型可能使用 reasoning 或 thinking 字段
                elif "reasoning" in message:
                    thinking = message.get("reasoning", "")
                elif "thinking" in message:
                    thinking = message.get("thinking", "")

                # 处理新的 tool_calls 格式 (OpenAI tools API)
                if "tool_calls" in message and message["tool_calls"]:
                    for tc in message["tool_calls"]:
                        tool_calls.append({
                            "id": tc.get("id", f"call_{hash(tc['function']['name'])}"),
                            "name": tc["function"]["name"],
                            "input": json.loads(tc["function"]["arguments"])
                        })
                # 兼容旧的 function_call 格式
                elif "function_call" in message:
                    func_call = message["function_call"]
                    tool_calls.append({
                        "id": f"call_{hash(func_call['name'])}",
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
                    usage=usage,
                    thinking=thinking,
                )

            except httpx.HTTPStatusError as e:
                # 处理HTTP错误
                status_code = e.response.status_code

                # 429 Too Many Requests - 需要重试
                if status_code == 429:
                    if attempt < max_retries - 1:
                        # 指数退避：1s, 2s, 4s
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            f"[OpenRouter] Rate limited (429), retrying in {delay}s "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error(f"[OpenRouter] Rate limit exceeded after {max_retries} retries")
                        raise ValueError(
                            "OpenRouter API rate limit exceeded. Please try again later or upgrade your plan."
                        ) from e

                # 其他HTTP错误直接抛出
                logger.error(f"[OpenRouter] HTTP {status_code} error: {e.response.text[:200]}")
                raise

            except httpx.RequestError as e:
                # 网络错误
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"[OpenRouter] Network error, retrying in {delay}s "
                        f"(attempt {attempt + 1}/{max_retries}): {e}"
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"[OpenRouter] Network error after {max_retries} retries: {e}")
                    raise

        # 不应该到达这里
        raise RuntimeError("OpenRouter API call failed after all retries")

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
            api_params["tools"] = tools
            api_params["tool_choice"] = "auto"

        if stop_sequences:
            api_params["stop"] = stop_sequences

        # 打印请求日志
        logger.info(f"[OpenRouter] Streaming model: {self.model} | max_tokens: {params['max_tokens']}")

        # 流式调用 (disable SSL verification for macOS compatibility)
        async with httpx.AsyncClient(timeout=120.0, verify=False) as client:
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
    ) -> list[dict[str, Any]]:
        """格式化消息为 OpenAI Chat Completions API 格式

        支持多模态内容（图片 + 文本）

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
            if role == "system":
                continue

            # 处理内容格式
            formatted_content = self._format_content(content)
            formatted.append({"role": role, "content": formatted_content})

        return formatted

    def _format_content(self, content: Any) -> Any:
        """格式化消息内容，支持多模态

        Args:
            content: 消息内容，可以是字符串或多模态内容列表

        Returns:
            格式化后的内容（字符串或 OpenAI Vision 格式数组）
        """
        # 纯文本内容
        if isinstance(content, str):
            return content

        # 多模态内容（列表格式）
        if isinstance(content, list):
            formatted_parts = []
            for part in content:
                if isinstance(part, dict):
                    part_type = part.get("type")
                    if part_type == "text":
                        formatted_parts.append({
                            "type": "text",
                            "text": part.get("text", "")
                        })
                    elif part_type == "image_url":
                        formatted_parts.append({
                            "type": "image_url",
                            "image_url": part.get("image_url", {})
                        })
                elif hasattr(part, "type"):
                    # Pydantic model (TextContent or ImageContent)
                    if part.type == "text":
                        formatted_parts.append({
                            "type": "text",
                            "text": part.text
                        })
                    elif part.type == "image_url":
                        formatted_parts.append({
                            "type": "image_url",
                            "image_url": part.image_url
                        })
            return formatted_parts if formatted_parts else ""

        # 未知格式，尝试转换为字符串
        return str(content) if content else ""

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

    优先从环境变量读取，其次从 settings（非测试环境）

    Args:
        api_key: OpenRouter API Key
        model: 模型名称
        max_tokens: 最大输出 token 数
        temperature: 温度参数
        base_url: API Base URL
        site_url: 站点 URL
        app_name: 应用名称

    Returns:
        OpenRouterLLM: OpenRouter LLM 实例
    """
    import os

    # 优先从环境变量读取，其次从 settings
    if api_key is None:
        api_key = os.getenv("OPENROUTER_API_KEY")

    if api_key is None:
        import sys
        if "pytest" not in sys.modules:
            try:
                from app.core.config import settings
                api_key = settings.OPENROUTER_API_KEY
            except Exception:
                pass

    if not api_key:
        raise ValueError("API Key not found. Set OPENROUTER_API_KEY in .env or environment")

    # 读取模型名称
    if model is None:
        model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")

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
