"""
Tool 基类定义
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..types import ToolSchema
from .risk import RiskLevel, OperationCategory


@dataclass
class ToolResult:
    """工具执行结果
    
    用于封装工具执行的返回值，包含状态、数据和错误信息。
    """
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    summary: Optional[str] = None  # 简短摘要，用于显示
    
    def to_text(self) -> str:
        """转换为文本格式"""
        if not self.success:
            return f"Error: {self.error}"
        if self.summary:
            return self.summary
        if self.data:
            import json
            return json.dumps(self.data, ensure_ascii=False, indent=2)
        return "Success"


class BaseTool(ABC):
    """工具抽象基类

    所有工具必须继承此类并实现 execute 方法。

    风险控制属性：
    - risk_level: 工具的默认风险等级
    - operation_categories: 工具涉及的操作类别列表
    - requires_confirmation: 是否强制需要确认（向后兼容）

    子类可以覆盖 get_risk_level() 和 get_operation_categories() 方法
    来实现基于参数的动态风险评估。
    """

    # 子类必须定义这些属性
    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {}  # JSON Schema format

    # 风险控制属性
    risk_level: RiskLevel = RiskLevel.LOW  # 默认风险等级
    operation_categories: List[OperationCategory] = []  # 操作类别
    requires_confirmation: bool = False  # 向后兼容：强制需要确认
    
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

    # ==================== 风险评估方法 ====================

    def get_risk_level(self, **kwargs) -> RiskLevel:
        """获取操作的风险等级

        子类可以覆盖此方法实现基于参数的动态风险评估。
        例如：Shell 工具可以根据具体命令返回不同风险等级。

        Args:
            **kwargs: 工具调用参数

        Returns:
            RiskLevel: 风险等级
        """
        return self.risk_level

    def get_operation_categories(self, **kwargs) -> List[OperationCategory]:
        """获取操作的类别列表

        子类可以覆盖此方法实现基于参数的动态类别判断。

        Args:
            **kwargs: 工具调用参数

        Returns:
            List[OperationCategory]: 操作类别列表
        """
        return self.operation_categories

    def get_confirmation_description(self, **kwargs) -> str:
        """获取确认对话框的描述文本

        子类可以覆盖此方法提供更详细的、针对具体操作的描述。

        Args:
            **kwargs: 工具调用参数

        Returns:
            str: 人类可读的操作描述
        """
        return self.description

    def get_risk_summary(self, **kwargs) -> Dict[str, Any]:
        """获取完整的风险评估摘要

        Args:
            **kwargs: 工具调用参数

        Returns:
            Dict: 包含风险等级、操作类别、描述等信息
        """
        return {
            "tool_name": self.name,
            "risk_level": self.get_risk_level(**kwargs).value,
            "operation_categories": [c.value for c in self.get_operation_categories(**kwargs)],
            "description": self.get_confirmation_description(**kwargs),
            "requires_confirmation": self.requires_confirmation,
        }
