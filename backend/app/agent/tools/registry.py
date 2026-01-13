"""
Tool 注册表 - 管理所有可用工具
"""
from typing import Dict, List, Any, Optional
import logging
from .base import BaseTool
from ..types import ToolSchema

logger = logging.getLogger(__name__)


class ToolRegistry:
    """工具注册表
    
    负责工具的注册、获取和管理
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        logger.info("ToolRegistry initialized")
    
    def register(self, tool: BaseTool) -> None:
        """注册工具
        
        Args:
            tool: 工具实例
            
        Raises:
            ValueError: 工具名称已存在
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def register_multiple(self, tools: List[BaseTool]) -> None:
        """批量注册工具
        
        Args:
            tools: 工具实例列表
        """
        for tool in tools:
            self.register(tool)
    
    def unregister(self, name: str) -> None:
        """注销工具
        
        Args:
            name: 工具名称
        """
        if name in self._tools:
            del self._tools[name]
            logger.info(f"Unregistered tool: {name}")
    
    def get(self, name: str) -> BaseTool:
        """获取工具实例
        
        Args:
            name: 工具名称
            
        Returns:
            BaseTool: 工具实例
            
        Raises:
            ValueError: 工具不存在
        """
        if name not in self._tools:
            available = ", ".join(self._tools.keys())
            raise ValueError(
                f"Tool '{name}' not found. "
                f"Available tools: {available or 'None'}"
            )
        return self._tools[name]
    
    def has(self, name: str) -> bool:
        """检查工具是否存在
        
        Args:
            name: 工具名称
            
        Returns:
            bool: 工具是否存在
        """
        return name in self._tools
    
    def list_names(self) -> List[str]:
        """列出所有工具名称
        
        Returns:
            List[str]: 工具名称列表
        """
        return list(self._tools.keys())
    
    def list_schemas(self) -> List[ToolSchema]:
        """列出所有工具 Schema
        
        Returns:
            List[ToolSchema]: 工具 Schema 列表
        """
        return [tool.to_schema() for tool in self._tools.values()]
    
    def to_llm_format(self, tool_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """转换为 LLM 工具定义格式（Claude Tool Use）
        
        Args:
            tool_names: 可选的工具名称列表，如果提供则只返回指定工具
            
        Returns:
            List[Dict]: LLM 工具定义列表
        """
        if tool_names is None:
            tools = self._tools.values()
        else:
            tools = [self.get(name) for name in tool_names]
        
        return [tool.to_llm_format() for tool in tools]
    
    def filter_by_confirmation(self, requires_confirmation: bool) -> List[BaseTool]:
        """筛选需要/不需要确认的工具
        
        Args:
            requires_confirmation: 是否需要确认
            
        Returns:
            List[BaseTool]: 工具列表
        """
        return [
            tool for tool in self._tools.values()
            if tool.requires_confirmation == requires_confirmation
        ]
    
    def __len__(self) -> int:
        """返回已注册工具数量"""
        return len(self._tools)
    
    def __repr__(self) -> str:
        return f"<ToolRegistry(tools={len(self._tools)})>"


# 全局工具注册表实例
_global_registry: Optional[ToolRegistry] = None


def get_global_registry() -> ToolRegistry:
    """获取全局工具注册表（单例）
    
    Returns:
        ToolRegistry: 全局工具注册表
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def register_tool(tool: BaseTool) -> None:
    """注册工具到全局注册表（便捷函数）
    
    Args:
        tool: 工具实例
    """
    registry = get_global_registry()
    registry.register(tool)
