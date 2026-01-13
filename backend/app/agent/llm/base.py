"""
LLM 客户端基类
"""
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional
from dataclasses import dataclass
from pydantic import BaseModel


class LLMMessage(BaseModel):
    """LLM 消息格式"""
    role: str  # "user" | "assistant" | "system"
    content: str


@dataclass
class LLMResponse:
    """LLM 完整响应"""
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    stop_reason: Optional[str] = None  # "end_turn" | "tool_use" | "max_tokens"
    usage: Optional[Dict[str, int]] = None  # {"input_tokens": 123, "output_tokens": 456}


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
        messages: List[LLMMessage],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None
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
        messages: List[LLMMessage],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None
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
        max_tokens: Optional[int],
        temperature: Optional[float]
    ) -> Dict[str, Any]:
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
