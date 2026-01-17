"""
World Interface - 世界接口

实现铁律三：工具是世界接口，不是插件

核心洞察：
- Agent 只能通过工具与外界交互
- 工具不是可选的插件，而是必须的世界接口
- 4+2 核心工具模型：核心4 + 扩展2

4 个核心工具（必须）：
1. read_file  - 读取文件
2. write_file - 写入文件
3. run_code   - 执行代码/Shell
4. exit       - 主动终止

2 个扩展工具（常用）：
5. web_search - 网络搜索
6. read_url   - 读取网页

参考文档：docs/architecture/Agent-Runtime-Design.md
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .base import BaseTool, ToolResult


class ToolCategory(Enum):
    """工具分类"""
    CORE = "core"           # 核心工具（4个）
    EXTENDED = "extended"   # 扩展工具（2个）
    CUSTOM = "custom"       # 自定义工具


@dataclass
class ToolMetadata:
    """工具元数据"""
    name: str
    category: ToolCategory
    description: str
    is_essential: bool = False  # 是否是必需的工具
    affects_world: bool = True  # 是否影响外部世界
    is_reversible: bool = False # 是否可逆


# 4+2 核心工具定义
CORE_TOOLS: dict[str, ToolMetadata] = {
    "read_file": ToolMetadata(
        name="read_file",
        category=ToolCategory.CORE,
        description="读取文件内容 - 感知世界的窗口",
        is_essential=True,
        affects_world=False,  # 只读
        is_reversible=True,
    ),
    "write_file": ToolMetadata(
        name="write_file",
        category=ToolCategory.CORE,
        description="写入文件内容 - 改变世界的画笔",
        is_essential=True,
        affects_world=True,
        is_reversible=False,  # 覆盖不可逆
    ),
    "run_code": ToolMetadata(
        name="run_code",
        category=ToolCategory.CORE,
        description="执行代码/Shell - 与环境交互的手",
        is_essential=True,
        affects_world=True,
        is_reversible=False,
    ),
    "exit": ToolMetadata(
        name="exit",
        category=ToolCategory.CORE,
        description="主动终止任务 - exit code 是最诚实的反馈",
        is_essential=True,
        affects_world=False,
        is_reversible=True,
    ),
}

EXTENDED_TOOLS: dict[str, ToolMetadata] = {
    "web_search": ToolMetadata(
        name="web_search",
        category=ToolCategory.EXTENDED,
        description="网络搜索 - 获取外部信息",
        is_essential=False,
        affects_world=False,
        is_reversible=True,
    ),
    "read_url": ToolMetadata(
        name="read_url",
        category=ToolCategory.EXTENDED,
        description="读取网页内容 - 深入了解信息源",
        is_essential=False,
        affects_world=False,
        is_reversible=True,
    ),
}


class WorldInterface:
    """世界接口 - Agent 与外界交互的唯一通道

    核心理念：
    - Agent 是一个封闭系统
    - 所有对外交互必须通过 WorldInterface
    - 工具是 Agent 的"感官"和"肢体"

    职责：
    1. 注册和管理工具
    2. 执行工具调用
    3. 验证工具可用性
    4. 记录工具使用
    """

    def __init__(self):
        # 所有已注册的工具
        self._tools: dict[str, BaseTool] = {}

        # 当前允许使用的工具（Action Space Pruning）
        self._allowed_tools: set[str] | None = None

        # 工具元数据
        self._metadata: dict[str, ToolMetadata] = {}

        # 工具使用统计
        self._usage_stats: dict[str, int] = {}

    def register_tool(
        self,
        tool: BaseTool,
        category: ToolCategory = ToolCategory.CUSTOM,
        metadata: ToolMetadata | None = None,
    ) -> None:
        """注册工具到世界接口

        Args:
            tool: 工具实例
            category: 工具分类
            metadata: 工具元数据（可选）
        """
        name = tool.name
        self._tools[name] = tool
        self._usage_stats[name] = 0

        # 设置元数据
        if metadata:
            self._metadata[name] = metadata
        elif name in CORE_TOOLS:
            self._metadata[name] = CORE_TOOLS[name]
        elif name in EXTENDED_TOOLS:
            self._metadata[name] = EXTENDED_TOOLS[name]
        else:
            self._metadata[name] = ToolMetadata(
                name=name,
                category=category,
                description=tool.description,
            )

    def get_tool(self, name: str) -> BaseTool | None:
        """获取工具实例"""
        if not self._is_tool_allowed(name):
            return None
        return self._tools.get(name)

    def _is_tool_allowed(self, name: str) -> bool:
        """检查工具是否被允许使用（Action Space Pruning）"""
        if self._allowed_tools is None:
            return True  # 没有限制
        return name in self._allowed_tools

    async def execute(
        self,
        tool_name: str,
        parameters: dict[str, Any],
    ) -> ToolResult:
        """执行工具调用

        这是 Agent 与外界交互的唯一入口

        Args:
            tool_name: 工具名称
            parameters: 工具参数

        Returns:
            ToolResult: 执行结果
        """
        # 检查工具是否存在
        if tool_name not in self._tools:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool not found: {tool_name}",
            )

        # 检查工具是否被允许
        if not self._is_tool_allowed(tool_name):
            return ToolResult(
                success=False,
                output="",
                error=f"Tool not allowed in current context: {tool_name}",
            )

        tool = self._tools[tool_name]

        # 更新使用统计
        self._usage_stats[tool_name] += 1

        # 执行工具
        try:
            result = await tool.execute(**parameters)
            return result
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool execution error: {str(e)}",
            )

    def set_allowed_tools(self, tool_names: list[str]) -> None:
        """设置允许使用的工具（Action Space Pruning）

        核心工具始终可用
        """
        # 核心工具始终可用
        core_tool_names = set(CORE_TOOLS.keys())
        self._allowed_tools = core_tool_names | set(tool_names)

    def reset_allowed_tools(self) -> None:
        """重置工具限制"""
        self._allowed_tools = None

    def get_available_tools(self) -> list[str]:
        """获取当前可用的工具列表"""
        if self._allowed_tools is None:
            return list(self._tools.keys())
        return list(self._allowed_tools & set(self._tools.keys()))

    def get_core_tools(self) -> list[str]:
        """获取核心工具列表"""
        return [name for name in self._tools.keys() if name in CORE_TOOLS]

    def get_extended_tools(self) -> list[str]:
        """获取扩展工具列表"""
        return [name for name in self._tools.keys() if name in EXTENDED_TOOLS]

    def has_all_core_tools(self) -> bool:
        """检查是否已注册所有核心工具"""
        return all(name in self._tools for name in CORE_TOOLS.keys())

    def get_missing_core_tools(self) -> list[str]:
        """获取缺失的核心工具"""
        return [name for name in CORE_TOOLS.keys() if name not in self._tools]

    def get_tool_metadata(self, name: str) -> ToolMetadata | None:
        """获取工具元数据"""
        return self._metadata.get(name)

    def get_usage_stats(self) -> dict[str, int]:
        """获取工具使用统计"""
        return self._usage_stats.copy()

    def get_tool_definitions_for_llm(self) -> list[dict[str, Any]]:
        """获取工具定义（用于 LLM）"""
        definitions = []

        for name in self.get_available_tools():
            tool = self._tools.get(name)
            if tool:
                definitions.append({
                    "name": name,
                    "description": tool.description,
                    "parameters": tool.get_parameters_schema() if hasattr(tool, 'get_parameters_schema') else {},
                })

        return definitions

    def __contains__(self, name: str) -> bool:
        """检查工具是否存在"""
        return name in self._tools

    def __len__(self) -> int:
        """获取工具数量"""
        return len(self._tools)


# 便捷函数
def create_world_interface_with_core_tools() -> WorldInterface:
    """创建包含核心工具的世界接口（需要外部注册具体实现）"""
    return WorldInterface()


def validate_core_tools(interface: WorldInterface) -> dict[str, Any]:
    """验证核心工具是否齐全

    Returns:
        验证结果
    """
    missing = interface.get_missing_core_tools()

    return {
        "is_valid": len(missing) == 0,
        "missing_tools": missing,
        "registered_core_tools": interface.get_core_tools(),
        "registered_extended_tools": interface.get_extended_tools(),
        "total_tools": len(interface),
    }
