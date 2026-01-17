"""
ActionSpace Manager - 动作空间管理器

实现铁律五 PolicyLayer 的第二个组件：ActionSpace

ActionSpace 管理：
- 可用工具集合（Action Space Pruning）
- 工具权限控制
- 动态工具启用/禁用
- 工具使用限制

核心理念：
- 最小工具集 > 100个垂直API
- 根据 Skill 动态调整可用工具
- 核心工具（4+2）始终可用

参考文档：docs/architecture/Agent-Runtime-Design.md
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ActionType(Enum):
    """动作类型"""
    TOOL_CALL = "tool_call"      # 工具调用
    LLM_QUERY = "llm_query"      # LLM 查询
    USER_QUERY = "user_query"    # 用户交互
    EXIT = "exit"                # 退出


@dataclass
class ActionConstraint:
    """动作约束"""
    max_calls: int = 0           # 最大调用次数（0=无限制）
    requires_confirmation: bool = False  # 是否需要确认
    cooldown_seconds: int = 0    # 冷却时间
    allowed_in_phases: list[str] = field(default_factory=list)  # 允许的阶段


@dataclass
class ToolPermission:
    """工具权限"""
    tool_name: str
    is_enabled: bool = True
    is_core: bool = False        # 是否是核心工具
    constraint: ActionConstraint | None = None
    usage_count: int = 0

    def can_use(self) -> bool:
        """检查是否可以使用"""
        if not self.is_enabled:
            return False

        if self.constraint and self.constraint.max_calls > 0:
            return self.usage_count < self.constraint.max_calls

        return True

    def increment_usage(self) -> None:
        """增加使用计数"""
        self.usage_count += 1


# 核心工具名称（始终可用）
CORE_TOOL_NAMES = {"read_file", "write_file", "run_code", "exit"}

# 扩展工具名称
EXTENDED_TOOL_NAMES = {"web_search", "read_url"}


class ActionSpaceManager:
    """动作空间管理器

    管理 Agent 可以执行的动作集合

    核心功能：
    1. Action Space Pruning - 限制可用工具
    2. 权限管理 - 控制工具使用权限
    3. 使用统计 - 追踪工具使用情况
    """

    def __init__(self):
        # 所有工具权限
        self._permissions: dict[str, ToolPermission] = {}

        # 当前允许的工具集（None = 全部允许）
        self._allowed_tools: set[str] | None = None

        # 禁用的工具集
        self._disabled_tools: set[str] = set()

        # 全局约束
        self._global_constraints: dict[str, ActionConstraint] = {}

    def register_tool(
        self,
        tool_name: str,
        is_core: bool = False,
        constraint: ActionConstraint | None = None,
    ) -> None:
        """注册工具

        Args:
            tool_name: 工具名称
            is_core: 是否是核心工具
            constraint: 约束条件
        """
        self._permissions[tool_name] = ToolPermission(
            tool_name=tool_name,
            is_enabled=True,
            is_core=is_core or tool_name in CORE_TOOL_NAMES,
            constraint=constraint,
        )

    def set_allowed_tools(self, tool_names: list[str]) -> None:
        """设置允许的工具集（Action Space Pruning）

        核心工具始终被允许

        Args:
            tool_names: 允许的工具名称列表
        """
        # 核心工具始终可用
        self._allowed_tools = CORE_TOOL_NAMES | set(tool_names)

    def reset_allowed_tools(self) -> None:
        """重置允许的工具集"""
        self._allowed_tools = None

    def enable_tool(self, tool_name: str) -> bool:
        """启用工具"""
        if tool_name in self._permissions:
            self._permissions[tool_name].is_enabled = True
            self._disabled_tools.discard(tool_name)
            return True
        return False

    def disable_tool(self, tool_name: str) -> bool:
        """禁用工具（核心工具不能禁用）"""
        if tool_name in CORE_TOOL_NAMES:
            return False  # 核心工具不能禁用

        if tool_name in self._permissions:
            self._permissions[tool_name].is_enabled = False
            self._disabled_tools.add(tool_name)
            return True
        return False

    def can_use_tool(self, tool_name: str) -> bool:
        """检查是否可以使用工具

        Args:
            tool_name: 工具名称

        Returns:
            是否可以使用
        """
        # 检查工具是否存在
        if tool_name not in self._permissions:
            return False

        permission = self._permissions[tool_name]

        # 检查是否被禁用
        if tool_name in self._disabled_tools:
            return False

        # 检查 Action Space Pruning
        if self._allowed_tools is not None:
            if tool_name not in self._allowed_tools:
                return False

        # 检查权限
        return permission.can_use()

    def use_tool(self, tool_name: str) -> bool:
        """使用工具（更新使用计数）

        Returns:
            是否成功使用
        """
        if not self.can_use_tool(tool_name):
            return False

        self._permissions[tool_name].increment_usage()
        return True

    def get_available_tools(self) -> list[str]:
        """获取当前可用的工具列表"""
        available = []

        for name, _perm in self._permissions.items():
            if self.can_use_tool(name):
                available.append(name)

        return available

    def get_core_tools(self) -> list[str]:
        """获取核心工具列表"""
        return [
            name for name, perm in self._permissions.items()
            if perm.is_core
        ]

    def get_extended_tools(self) -> list[str]:
        """获取扩展工具列表"""
        return [
            name for name in self._permissions.keys()
            if name in EXTENDED_TOOL_NAMES
        ]

    def get_usage_stats(self) -> dict[str, int]:
        """获取工具使用统计"""
        return {
            name: perm.usage_count
            for name, perm in self._permissions.items()
        }

    def get_tool_permission(self, tool_name: str) -> ToolPermission | None:
        """获取工具权限"""
        return self._permissions.get(tool_name)

    def set_tool_constraint(
        self,
        tool_name: str,
        constraint: ActionConstraint,
    ) -> bool:
        """设置工具约束"""
        if tool_name in self._permissions:
            self._permissions[tool_name].constraint = constraint
            return True
        return False

    def get_pruning_summary(self) -> dict[str, Any]:
        """获取 Action Space Pruning 摘要"""
        all_tools = set(self._permissions.keys())
        available = set(self.get_available_tools())
        pruned = all_tools - available

        return {
            "total_tools": len(all_tools),
            "available_tools": len(available),
            "pruned_tools": len(pruned),
            "pruning_ratio": len(pruned) / len(all_tools) if all_tools else 0,
            "core_tools": self.get_core_tools(),
            "extended_tools": self.get_extended_tools(),
            "disabled_tools": list(self._disabled_tools),
            "allowed_tools": list(self._allowed_tools) if self._allowed_tools else "all",
        }

    def reset_usage_counts(self) -> None:
        """重置所有使用计数"""
        for perm in self._permissions.values():
            perm.usage_count = 0

    def reset(self) -> None:
        """完全重置"""
        self._allowed_tools = None
        self._disabled_tools = set()
        self.reset_usage_counts()


def create_default_action_space() -> ActionSpaceManager:
    """创建默认的动作空间管理器"""
    manager = ActionSpaceManager()

    # 注册核心工具
    for name in CORE_TOOL_NAMES:
        manager.register_tool(name, is_core=True)

    # 注册扩展工具
    for name in EXTENDED_TOOL_NAMES:
        manager.register_tool(name, is_core=False)

    return manager
