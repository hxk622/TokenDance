"""
Tool 基类定义
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from ..types import ToolSchema


class BaseTool(ABC):
    """工具抽象基类
    
    所有工具必须继承此类并实现 execute 方法
    """
    
    # 子类必须定义这些属性
    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {}  # JSON Schema format
    requires_confirmation: bool = False  # 是否需要 HITL 确认
    
    def __init__(self):
        if not self.name:
            raise ValueError(f"{self.__class__.__name__} must define 'name'")
        if not self.description:
            raise ValueError(f"{self.__class__.__name__} must define 'description'")
    
    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """执行工具
        
        Args:
            **kwargs: 工具参数（必须匹配 parameters schema）
            
        Returns:
            str: 工具执行结果（文本格式）
            
        Raises:
            Exception: 工具执行失败时抛出异常
        """
        pass
    
    def to_schema(self) -> ToolSchema:
        """转换为 ToolSchema（给 LLM 使用）"""
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=self.parameters
        )
    
    def to_llm_format(self) -> Dict[str, Any]:
        """转换为 LLM 工具定义格式（Claude Tool Use）"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters
        }
    
    def validate_args(self, args: Dict[str, Any]) -> None:
        """验证工具参数
        
        Args:
            args: 工具参数
            
        Raises:
            ValueError: 参数验证失败
        """
        # 检查必需参数
        required = self.parameters.get("required", [])
        for field in required:
            if field not in args:
                raise ValueError(f"Missing required parameter: {field}")
        
        # TODO: 更完整的 JSON Schema 验证
        # 可以使用 jsonschema 库进行完整验证
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"
