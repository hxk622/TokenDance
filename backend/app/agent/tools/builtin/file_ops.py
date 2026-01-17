"""
FileOpsTool - 文件操作工具

核心功能：
- 读取文件（支持Frontmatter）
- 写入文件（支持Frontmatter）
- 列出目录文件
- 删除文件
- 检查文件存在

集成AgentFileSystem，支持多租户隔离

风险等级：动态（根据操作类型）
- read/exists/list: NONE
- write: LOW
- delete: MEDIUM
"""

from typing import Any

from pydantic import BaseModel, Field

from app.filesystem import AgentFileSystem

from ..base import BaseTool, ToolResult
from ..risk import OperationCategory, RiskLevel


class ReadFileArgs(BaseModel):
    """读取文件参数"""
    path: str = Field(..., description="文件相对路径")
    parse_frontmatter: bool = Field(False, description="是否解析YAML Frontmatter")


class WriteFileArgs(BaseModel):
    """写入文件参数"""
    path: str = Field(..., description="文件相对路径")
    content: str = Field(..., description="文件内容")
    metadata: dict[str, Any] | None = Field(None, description="YAML Frontmatter元数据（可选）")


class ListFilesArgs(BaseModel):
    """列出文件参数"""
    directory: str = Field("", description="目录相对路径，默认为workspace根目录")
    pattern: str = Field("*", description="文件名模式，支持通配符，如 *.md")


class DeleteFileArgs(BaseModel):
    """删除文件参数"""
    path: str = Field(..., description="文件相对路径")


class FileExistsArgs(BaseModel):
    """检查文件存在参数"""
    path: str = Field(..., description="文件相对路径")


class FileOpsTool(BaseTool):
    """
    文件操作工具

    提供文件读写、列表、删除、检查等操作，所有操作限制在workspace内。

    风险等级：动态（根据操作类型）
    - read/exists/list: NONE（纯读取）
    - write: LOW（创建/修改文件）
    - delete: MEDIUM（删除文件）
    """

    name = "file_ops"
    description = "文件操作工具。支持读写文件、列出目录、删除文件等操作。所有路径相对于workspace，确保安全。"

    # 默认风险配置（会被动态覆盖）
    risk_level = RiskLevel.LOW
    operation_categories = [OperationCategory.FILE_READ]
    requires_confirmation = False

    def __init__(self, filesystem: AgentFileSystem):
        """
        初始化FileOpsTool

        Args:
            filesystem: AgentFileSystem实例
        """
        super().__init__()
        self.fs = filesystem

    def get_risk_level(self, **kwargs) -> RiskLevel:
        """根据操作类型动态评估风险等级"""
        operation = kwargs.get("operation", "read")

        risk_mapping = {
            "read": RiskLevel.NONE,
            "exists": RiskLevel.NONE,
            "list": RiskLevel.NONE,
            "write": RiskLevel.LOW,
            "delete": RiskLevel.MEDIUM,
        }
        return risk_mapping.get(operation, RiskLevel.MEDIUM)

    def get_operation_categories(self, **kwargs) -> list[OperationCategory]:
        """根据操作类型返回操作类别"""
        operation = kwargs.get("operation", "read")

        category_mapping = {
            "read": [OperationCategory.FILE_READ],
            "exists": [OperationCategory.FILE_READ],
            "list": [OperationCategory.FILE_READ],
            "write": [OperationCategory.FILE_CREATE, OperationCategory.FILE_MODIFY],
            "delete": [OperationCategory.FILE_DELETE],
        }
        return category_mapping.get(operation, [OperationCategory.FILE_READ])

    def get_confirmation_description(self, **kwargs) -> str:
        """提供详细的确认描述"""
        operation = kwargs.get("operation", "read")
        path = kwargs.get("path", "unknown")

        descriptions = {
            "read": f"读取文件: {path}",
            "exists": f"检查文件是否存在: {path}",
            "list": f"列出目录: {path}",
            "write": f"写入文件: {path}",
            "delete": f"删除文件: {path}（此操作不可逆）",
        }
        return descriptions.get(operation, f"文件操作: {operation} on {path}")

    async def execute(self, operation: str, **kwargs) -> ToolResult:
        """
        执行文件操作

        Args:
            operation: 操作类型 (read/write/list/delete/exists)
            **kwargs: 操作参数

        Returns:
            ToolResult: 执行结果
        """
        try:
            if operation == "read":
                return await self._read_file(**kwargs)
            elif operation == "write":
                return await self._write_file(**kwargs)
            elif operation == "list":
                return await self._list_files(**kwargs)
            elif operation == "delete":
                return await self._delete_file(**kwargs)
            elif operation == "exists":
                return await self._file_exists(**kwargs)
            else:
                return ToolResult(
                    success=False,
                    error=f"未知的操作: {operation}。支持的操作: read, write, list, delete, exists"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"文件操作失败: {str(e)}"
            )

    async def _read_file(
        self,
        path: str,
        parse_frontmatter: bool = False,
    ) -> ToolResult:
        """
        读取文件

        Args:
            path: 文件路径
            parse_frontmatter: 是否解析Frontmatter

        Returns:
            ToolResult
        """
        try:
            if parse_frontmatter:
                data = self.fs.read_with_frontmatter(path)
                return ToolResult(
                    success=True,
                    data={
                        "path": path,
                        "content": data["content"],
                        "metadata": data["metadata"],
                        "has_frontmatter": bool(data["metadata"]),
                    }
                )
            else:
                content = self.fs.read(path)
                return ToolResult(
                    success=True,
                    data={
                        "path": path,
                        "content": content,
                    }
                )
        except FileNotFoundError:
            return ToolResult(
                success=False,
                error=f"文件不存在: {path}"
            )
        except PermissionError as e:
            return ToolResult(
                success=False,
                error=str(e)
            )

    async def _write_file(
        self,
        path: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> ToolResult:
        """
        写入文件

        Args:
            path: 文件路径
            content: 文件内容
            metadata: Frontmatter元数据

        Returns:
            ToolResult
        """
        try:
            if metadata:
                file_path = self.fs.write_with_frontmatter(path, content, metadata)
            else:
                file_path = self.fs.write(path, content)

            return ToolResult(
                success=True,
                data={
                    "path": path,
                    "absolute_path": str(file_path),
                    "has_frontmatter": metadata is not None,
                }
            )
        except PermissionError as e:
            return ToolResult(
                success=False,
                error=str(e)
            )

    async def _list_files(
        self,
        directory: str = "",
        pattern: str = "*",
    ) -> ToolResult:
        """
        列出目录下的文件

        Args:
            directory: 目录路径
            pattern: 文件名模式

        Returns:
            ToolResult
        """
        try:
            files = self.fs.list_files(directory, pattern)

            return ToolResult(
                success=True,
                data={
                    "directory": directory or "workspace根目录",
                    "pattern": pattern,
                    "files": files,
                    "count": len(files),
                }
            )
        except PermissionError as e:
            return ToolResult(
                success=False,
                error=str(e)
            )

    async def _delete_file(
        self,
        path: str,
    ) -> ToolResult:
        """
        删除文件

        Args:
            path: 文件路径

        Returns:
            ToolResult
        """
        try:
            # 检查文件是否存在
            if not self.fs.exists(path):
                return ToolResult(
                    success=False,
                    error=f"文件不存在: {path}"
                )

            self.fs.delete(path)

            return ToolResult(
                success=True,
                data={
                    "path": path,
                    "deleted": True,
                }
            )
        except PermissionError as e:
            return ToolResult(
                success=False,
                error=str(e)
            )

    async def _file_exists(
        self,
        path: str,
    ) -> ToolResult:
        """
        检查文件是否存在

        Args:
            path: 文件路径

        Returns:
            ToolResult
        """
        exists = self.fs.exists(path)

        return ToolResult(
            success=True,
            data={
                "path": path,
                "exists": exists,
            }
        )


# 便捷函数
def create_file_ops_tool(filesystem: AgentFileSystem) -> FileOpsTool:
    """
    创建FileOpsTool实例

    Args:
        filesystem: AgentFileSystem实例

    Returns:
        FileOpsTool实例
    """
    return FileOpsTool(filesystem=filesystem)
