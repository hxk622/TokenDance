# -*- coding: utf-8 -*-
"""
Qwen LLM 客户端实现

通义千问（Qwen）使用 OpenAI 兼容 API
"""
from typing import Any, AsyncGenerator, Dict, List, Optional
import logging
import os

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .base import BaseLLM, LLMMessage, LLMResponse

logger = logging.getLogger(__name__)


class QwenLLM(BaseLLM):
    """Qwen API 客户端
    
    使用 OpenAI SDK 调用通义千问 API
    官方文档：https://help.aliyun.com/zh/model-studio/developer-reference/
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "qwen-plus",
        max_tokens: int = 8192,
        temperature: float = 1.0,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    ):
        super().__init__(api_key, model, max_tokens, temperature)
        
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "openai SDK not installed. "
                "Install with: pip install openai"
            )
        
        self.base_url = base_url
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        logger.info(f"QwenLLM initialized with model: {model}")
    
    async def complete(
        self,
        messages: List[LLMMessage],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None
    ) -> LLMResponse:
        """完整调用 Qwen API
        
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
        api_params = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": params["max_tokens"],
            "temperature": params["temperature"],
        }
        
        if tools:
            # 转换为 OpenAI Function Calling 格式
            api_params["tools"] = self._convert_tools(tools)
        
        if stop_sequences:
            api_params["stop"] = stop_sequences
        
        # 调用 API
        response = await self.client.chat.completions.create(**api_params)
        
        # 解析响应
        message = response.choices[0].message
        content = message.content or ""
        
        # 解析工具调用
        tool_calls = None
        if message.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "input": eval(tc.function.arguments)  # JSON string to dict
                }
                for tc in message.tool_calls
            ]
        
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            stop_reason=response.choices[0].finish_reason,
            usage={
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens
            }
        )
    
    async def stream(
        self,
        messages: List[LLMMessage],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None
    ) -> AsyncGenerator[str, None]:
        """流式调用 Qwen API
        
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
        api_params = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": params["max_tokens"],
            "temperature": params["temperature"],
            "stream": True,
        }
        
        if tools:
            api_params["tools"] = self._convert_tools(tools)
        
        if stop_sequences:
            api_params["stop"] = stop_sequences
        
        # 流式调用
        stream = await self.client.chat.completions.create(**api_params)
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def _format_messages(
        self, 
        messages: List[Any],
        system: Optional[str] = None
    ) -> List[Dict[str, str]]:
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
        formatted = []
        
        # 添加 system 消息（如果提供）
        if system:
            formatted.append({"role": "system", "content": system})
        
        # 转换用户消息
        for msg in messages:
            # 支持 dict 和 LLMMessage 两种格式
            if isinstance(msg, dict):
                role = msg.get("role")
                content = msg.get("content")
            else:
                role = msg.role
                content = msg.content
            
            formatted.append({"role": role, "content": content})
        
        return formatted
    
    def _convert_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """转换工具定义为 OpenAI Function Calling 格式
        
        Args:
            tools: Claude Tool Use 格式的工具定义
            
        Returns:
            List[Dict]: OpenAI Function Calling 格式
        """
        # Claude 和 OpenAI 的工具格式非常相似，主要是结构调整
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
def create_qwen_llm(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = 8192,
    temperature: float = 1.0,
    base_url: Optional[str] = None
) -> QwenLLM:
    """创建 QwenLLM 实例
    
    支持从环境变量读取配置：
    - DASHSCOPE_API_KEY 或 QWEN_API_KEY: API Key
    - QWEN_MODEL: 模型名称
    - QWEN_BASE_URL: API Base URL
    
    推荐模型：
    - qwen-plus: 高性能，免费 100万 tokens/天
    - qwen-turbo: 快速，免费 200万 tokens/天
    - qwen-max: 最强，付费
    
    Args:
        api_key: Qwen API Key（如果为 None，从环境变量读取）
        model: 模型名称（如果为 None，从环境变量读取）
        max_tokens: 最大输出 token 数
        temperature: 温度参数
        base_url: API Base URL（如果为 None，从环境变量读取）
        
    Returns:
        QwenLLM: Qwen LLM 实例
    """
    # 读取 API Key（支持两种环境变量）
    if api_key is None:
        api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
        if not api_key:
            raise ValueError(
                "API Key not found. Set DASHSCOPE_API_KEY or QWEN_API_KEY"
            )
    
    # 读取模型名称
    if model is None:
        model = os.getenv("QWEN_MODEL", "qwen-plus")
    
    # 读取 Base URL
    if base_url is None:
        base_url = os.getenv(
            "QWEN_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
    
    return QwenLLM(
        api_key=api_key,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        base_url=base_url
    )
