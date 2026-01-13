"""
FileSystem模块 - Agent文件系统抽象层

核心功能：
- 多租户隔离 (Org/Team/Workspace)
- YAML Frontmatter + Markdown解析
- 文件CRUD操作
- 目录管理

来源：Manus "文件系统是灵魂" 理念
"""

from .agent_fs import AgentFileSystem

__all__ = [
    "AgentFileSystem",
]
