"""
SiliconFlow LLM 客户端实现

硅基流动（SiliconFlow）是国内的 AI 基础设施平台，提供高性价比的 GenAI 服务。
- 兼容 OpenAI API 格式
- 提供多种免费模型（Qwen2.5-7B、Llama3.1-8B 等）
- 国内访问速度快，无需翻墙

官方文档：https://docs.siliconflow.cn
模型列表：https://siliconflow.cn/zh-cn/models
"""
import json
import logging
import os
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from .base import BaseLLM, LLMMessage, LLMResponse

logger = logging.getLogger(__name__)


# 硅基流动免费模型列表
SILICONFLOW_FREE_MODELS = [
    "Qwen/Qwen2.5-7B-Instruct",
    "Qwen/Qwen2-7B-Instruct",
    "THUDM/glm-4-9b-chat",
    "01-ai/Yi-1.5-9B-Chat-16K",
    "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "internlm/internlm2_5-7b-chat",
]

# 硅基流动付费但性价比高的模型
SILICONFLOW_PAID_MODELS = [
    "Qwen/Qwen2.5-72B-Instruct",  # 默认推荐
    "deepseek-ai/DeepSeek-V2.5",
    "deepseek-ai/DeepSeek-R1",  # 推理模型
    "Qwen/Qwen2.5-32B-Instruct",
    "Qwen/QwQ-32B",  # 推理模型
]

# 任务类型 -> 模型映射（硅基流动）
SILICONFLOW_TASK_MODEL_MAP = {
    # 深度推理/研究 -> DeepSeek-R1 (推理能力强)
    "deep_research": "deepseek-ai/DeepSeek-R1",
    # 金融分析 -> DeepSeek-R1 (复杂推理)
    "financial_analysis": "deepseek-ai/DeepSeek-R1",
    # PPT/文档生成 -> Qwen2.5-72B (创意+结构化)
    "ppt_generation": "Qwen/Qwen2.5-72B-Instruct",
    # 代码生成 -> DeepSeek-V2.5 (代码能力强)
    "code_generation": "deepseek-ai/DeepSeek-V2.5",
    # 快速问答 -> Qwen2.5-7B 免费模型 (快速便宜)
    "quick_qa": "Qwen/Qwen2.5-7B-Instruct",
    # 通用任务 -> Qwen2.5-72B (平衡性能)
    "general": "Qwen/Qwen2.5-72B-Instruct",
    # 多模态 -> Qwen2.5-72B (支持 vision)
    "multimodal": "Qwen/Qwen2.5-72B-Instruct",
}

# Fallback 链 - 当主模型不可用时的备选
SILICONFLOW_FALLBACK_CHAIN = [
    "Qwen/Qwen2.5-72B-Instruct",  # 首选性价比
    "deepseek-ai/DeepSeek-V2.5",   # DeepSeek 备选
    "Qwen/Qwen2.5-7B-Instruct",    # 免费备选
]


class SiliconFlowLLM(BaseLLM):
    """SiliconFlow API 客户端

    使用 httpx 直接调用硅基流动 API（绕过 SSL 证书问题）
    官方文档：https://docs.siliconflow.cn
    """

    def __init__(
        self,
        api_key: str,
        model: str = "Qwen/Qwen2.5-72B-Instruct",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        base_url: str = "https://api.siliconflow.cn/v1"
    ):
        super().__init__(api_key, model, max_tokens, temperature)
        self.base_url = base_url.rstrip("/")
        logger.info(f"SiliconFlowLLM initialized with model: {model}")

    async def complete(
        self,
        messages: list[LLMMessage],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        stop_sequences: list[str] | None = None
    ) -> LLMResponse:
        """完整调用 SiliconFlow API

        Args:
            messages: 消息列表
            system: 系统提示词
            tools: 工具定义列表（OpenAI Function Calling 格式）
            max_tokens: 最大输出 token 数
            temperature: 温度参数
            stop_sequences: 停止序列

        Returns:
            LLMResponse: 完整响应
        """
        params = self._merge_params(max_tokens, temperature)

        # 格式化消息（包含 system）
        formatted_messages = self._format_messages(messages, system)

        # 构造 API 请求参数
        api_params: dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": params["max_tokens"],
            "temperature": params["temperature"],
        }

        if tools:
            # 转换为 OpenAI Function Calling 格式
            api_params["tools"] = self._convert_tools(tools)
            api_params["tool_choice"] = "auto"

        if stop_sequences:
            api_params["stop"] = stop_sequences

        logger.info(f"[SiliconFlow] Calling model: {self.model} | max_tokens: {params['max_tokens']}")

        try:
            # 使用 httpx 直接调用（禁用 SSL 验证，绕过证书问题）
            async with httpx.AsyncClient(verify=False, timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=api_params
                )
                response.raise_for_status()
                data = response.json()

            # 解析响应
            message = data["choices"][0]["message"]
            content = message.get("content") or ""

            # 解析工具调用
            tool_calls = None
            if message.get("tool_calls"):
                tool_calls = []
                for tc in message["tool_calls"]:
                    try:
                        # 尝试解析 JSON 参数
                        arguments = json.loads(tc["function"]["arguments"])
                    except json.JSONDecodeError:
                        arguments = {"raw": tc["function"]["arguments"]}

                    tool_calls.append({
                        "id": tc["id"],
                        "name": tc["function"]["name"],
                        "input": arguments
                    })

            # 处理使用量信息
            usage = None
            if data.get("usage"):
                usage = {
                    "input_tokens": data["usage"]["prompt_tokens"],
                    "output_tokens": data["usage"]["completion_tokens"]
                }
                logger.info(
                    f"[SiliconFlow] Response from {self.model} | "
                    f"tokens: {usage['input_tokens']}/{usage['output_tokens']}"
                )

            return LLMResponse(
                content=content,
                tool_calls=tool_calls,
                stop_reason=data["choices"][0].get("finish_reason"),
                usage=usage
            )

        except Exception as e:
            logger.error(f"[SiliconFlow] API call failed: {e}")
            raise

    async def stream(  # type: ignore[override]
        self,
        messages: list[LLMMessage],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        stop_sequences: list[str] | None = None
    ) -> AsyncGenerator[str, None]:
        """流式调用 SiliconFlow API

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

        # 格式化消息（包含 system）
        formatted_messages = self._format_messages(messages, system)

        # 构造 API 请求参数
        api_params: dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": params["max_tokens"],
            "temperature": params["temperature"],
            "stream": True,
        }

        if tools:
            api_params["tools"] = self._convert_tools(tools)
            api_params["tool_choice"] = "auto"

        if stop_sequences:
            api_params["stop"] = stop_sequences

        logger.info(f"[SiliconFlow] Streaming from model: {self.model}")

        try:
            # 使用 httpx 直接流式调用（禁用 SSL 验证）
            async with httpx.AsyncClient(verify=False, timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=api_params
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                if chunk.get("choices") and chunk["choices"][0].get("delta"):
                                    content = chunk["choices"][0]["delta"].get("content")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue

        except Exception as e:
            logger.error(f"[SiliconFlow] Stream failed: {e}")
            raise

    def _format_messages(
        self,
        messages: list[Any],
        system: str | None = None
    ) -> list[dict[str, Any]]:
        """格式化消息为 OpenAI API 格式

        支持两种输入格式：
        - LLMMessage 对象
        - Dict {"role": "...", "content": "..."}

        Args:
            messages: 消息列表（LLMMessage 或 dict）
            system: 系统提示词（会添加到消息列表开头）

        Returns:
            List[Dict]: OpenAI API 消息格式
        """
        formatted: list[dict[str, Any]] = []

        # 添加 system 消息（如果提供）
        if system:
            formatted.append({"role": "system", "content": system})

        # 转换用户消息
        for msg in messages:
            # 支持 dict 和 LLMMessage 两种格式
            if isinstance(msg, dict):
                role = str(msg.get("role", ""))
                content = msg.get("content", "")
            else:
                role = msg.role
                content = msg.content

            # 处理多模态内容
            if isinstance(content, list):
                # 多模态消息，保持原格式
                formatted.append({"role": role, "content": content})
            else:
                formatted.append({"role": role, "content": content})

        return formatted

    def _convert_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """转换工具定义为 OpenAI Function Calling 格式

        Args:
            tools: Claude Tool Use 格式的工具定义

        Returns:
            List[Dict]: OpenAI Function Calling 格式
        """
        openai_tools = []
        for tool in tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool.get("name"),
                    "description": tool.get("description"),
                    "parameters": tool.get("input_schema", {})
                }
            }
            openai_tools.append(openai_tool)

        return openai_tools


# 便捷函数
def create_siliconflow_llm(
    api_key: str | None = None,
    model: str | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    base_url: str | None = None,
    prefer_free: bool = False
) -> SiliconFlowLLM:
    """创建 SiliconFlowLLM 实例

    支持从环境变量读取配置：
    - SILICONFLOW_API_KEY: API Key
    - SILICONFLOW_MODEL: 模型名称
    - SILICONFLOW_BASE_URL: API Base URL

    免费模型推荐：
    - Qwen/Qwen2.5-7B-Instruct: 性能不错的免费模型
    - THUDM/glm-4-9b-chat: 智谱 GLM 免费模型
    - meta-llama/Meta-Llama-3.1-8B-Instruct: Llama 免费模型

    付费模型推荐（性价比高）：
    - Qwen/Qwen2.5-72B-Instruct: 高性能，价格实惠
    - deepseek-ai/DeepSeek-V2.5: DeepSeek 最新模型
    - deepseek-ai/DeepSeek-R1: 推理能力强

    Args:
        api_key: SiliconFlow API Key（如果为 None，从环境变量读取）
        model: 模型名称（如果为 None，从环境变量读取）
        max_tokens: 最大输出 token 数
        temperature: 温度参数
        base_url: API Base URL（如果为 None，从环境变量读取）
        prefer_free: 是否优先使用免费模型（默认 False）

    Returns:
        SiliconFlowLLM: SiliconFlow LLM 实例
    """
    # 读取 API Key
    if api_key is None:
        api_key = os.getenv("SILICONFLOW_API_KEY")
        if not api_key:
            raise ValueError(
                "API Key not found. Set SILICONFLOW_API_KEY environment variable"
            )

    # 读取模型名称
    if model is None:
        model = os.getenv("SILICONFLOW_MODEL")
        if not model:
            if prefer_free:
                model = "Qwen/Qwen2.5-7B-Instruct"  # 免费模型
            else:
                model = "Qwen/Qwen2.5-72B-Instruct"  # 付费但便宜

    # 读取 Base URL
    if base_url is None:
        base_url = os.getenv(
            "SILICONFLOW_BASE_URL",
            "https://api.siliconflow.cn/v1"
        )

    return SiliconFlowLLM(
        api_key=api_key,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        base_url=base_url
    )


def get_siliconflow_free_model() -> str:
    """获取硅基流动免费模型名称

    Returns:
        str: 推荐的免费模型名称
    """
    return "Qwen/Qwen2.5-7B-Instruct"


def get_siliconflow_best_model() -> str:
    """获取硅基流动性价比最高的付费模型名称

    Returns:
        str: 推荐的付费模型名称
    """
    return "Qwen/Qwen2.5-72B-Instruct"


def is_siliconflow_free_model(model: str) -> bool:
    """检查是否为硅基流动免费模型

    Args:
        model: 模型名称

    Returns:
        bool: 是否为免费模型
    """
    return model in SILICONFLOW_FREE_MODELS


def select_siliconflow_model(
    task_type: str,
    prefer_free: bool = False,
    context_length: int = 0
) -> str:
    """根据任务类型选择硅基流动模型

    Args:
        task_type: 任务类型 (deep_research, code_generation, quick_qa, etc.)
        prefer_free: 是否优先使用免费模型
        context_length: 上下文长度 (tokens)

    Returns:
        str: 模型名称
    """
    # 如果优先免费，使用免费模型
    if prefer_free:
        logger.info("[SiliconFlow] prefer_free=True, using free model")
        return "Qwen/Qwen2.5-7B-Instruct"

    # 超长上下文 -> Qwen2.5-72B (128K context)
    if context_length > 64000:
        logger.info(f"[SiliconFlow] Long context ({context_length}), using Qwen2.5-72B")
        return "Qwen/Qwen2.5-72B-Instruct"

    # 按任务类型选择
    model = SILICONFLOW_TASK_MODEL_MAP.get(task_type, SILICONFLOW_TASK_MODEL_MAP["general"])
    logger.info(f"[SiliconFlow] Selected model '{model}' for task '{task_type}'")
    return model


def get_siliconflow_llm_for_task(
    task_type: str,
    prefer_free: bool = False,
    context_length: int = 0,
    **llm_kwargs
) -> SiliconFlowLLM:
    """根据任务类型获取硅基流动 LLM

    Args:
        task_type: 任务类型
        prefer_free: 是否优先免费模型
        context_length: 上下文长度
        **llm_kwargs: 其他 LLM 参数

    Returns:
        SiliconFlowLLM: LLM 实例

    Example:
        >>> # 深度研究
        >>> llm = get_siliconflow_llm_for_task("deep_research")

        >>> # 快速问答（免费）
        >>> llm = get_siliconflow_llm_for_task("quick_qa", prefer_free=True)

        >>> # 代码生成
        >>> llm = get_siliconflow_llm_for_task("code_generation", temperature=0.3)
    """
    model = select_siliconflow_model(
        task_type=task_type,
        prefer_free=prefer_free,
        context_length=context_length
    )
    return create_siliconflow_llm(model=model, **llm_kwargs)


def is_siliconflow_available() -> bool:
    """检查硅基流动 API 是否可用（是否配置了 API Key）

    Returns:
        bool: 是否可用
    """
    api_key = os.getenv("SILICONFLOW_API_KEY")
    return bool(api_key and api_key.strip())
