"""
Create Document Tool - 创建并保存文档

功能：
- 创建 Markdown 文档
- 保存到 Workspace 文件系统
- 支持自定义文件名
- 自动创建目录
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.agent.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class CreateDocumentTool(BaseTool):
    """创建文档工具"""

    name = "create_document"
    description = (
        "Create and save a document (Markdown format) to the workspace. "
        "Use this to save research reports, summaries, or any structured content."
    )
    
    parameters = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Document title (used as filename)"
            },
            "content": {
                "type": "string",
                "description": "Document content in Markdown format"
            },
            "filename": {
                "type": "string",
                "description": "Custom filename (optional, auto-generated from title if not provided)",
                "default": None
            },
            "subdirectory": {
                "type": "string",
                "description": "Subdirectory within workspace (optional, e.g., 'reports', 'research')",
                "default": "documents"
            }
        },
        "required": ["title", "content"]
    }
    
    requires_confirmation = False

    def __init__(self, workspace_root: Optional[Path] = None):
        """初始化
        
        Args:
            workspace_root: Workspace 根目录路径
        """
        super().__init__()
        self.workspace_root = workspace_root or Path("/tmp/tokendance/workspaces")

    async def execute(
        self,
        title: str,
        content: str,
        filename: Optional[str] = None,
        subdirectory: str = "documents",
        **kwargs
    ) -> ToolResult:
        """创建并保存文档
        
        Args:
            title: 文档标题
            content: 文档内容（Markdown）
            filename: 自定义文件名
            subdirectory: 子目录
            
        Returns:
            ToolResult 包含文件路径
        """
        try:
            # 生成文件名
            if not filename:
                # 从标题生成文件名
                filename = self._sanitize_filename(title) + ".md"
            elif not filename.endswith(".md"):
                filename += ".md"
            
            # 构建文件路径
            # 获取当前会话的 workspace_id（从 kwargs 或 context）
            workspace_id = kwargs.get("workspace_id", "default")
            session_id = kwargs.get("session_id", "default")
            
            doc_dir = self.workspace_root / workspace_id / session_id / subdirectory
            doc_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = doc_dir / filename
            
            # 添加元数据到文档
            full_content = self._add_metadata(title, content)
            
            # 写入文件
            file_path.write_text(full_content, encoding="utf-8")
            
            logger.info(f"Document created: {file_path}")
            
            # 计算相对路径
            try:
                relative_path = file_path.relative_to(self.workspace_root)
            except ValueError:
                relative_path = file_path
            
            return ToolResult(
                success=True,
                output=f"Document created successfully!\n\nFile: {relative_path}\nSize: {len(full_content)} bytes",
                metadata={
                    "file_path": str(file_path),
                    "relative_path": str(relative_path),
                    "size": len(full_content),
                    "title": title,
                }
            )
            
        except OSError as e:
            logger.error(f"Failed to create document: {e}")
            return ToolResult(
                success=False,
                output=f"Failed to create document: {str(e)}",
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Error creating document: {e}", exc_info=True)
            return ToolResult(
                success=False,
                output=f"Failed to create document: {str(e)}",
                error=str(e)
            )

    def _sanitize_filename(self, title: str) -> str:
        """清理标题生成安全的文件名
        
        Args:
            title: 文档标题
            
        Returns:
            安全的文件名
        """
        import re
        
        # 移除或替换特殊字符
        filename = re.sub(r'[<>:"/\\|?*]', '', title)
        filename = re.sub(r'\s+', '_', filename)
        
        # 限制长度
        if len(filename) > 100:
            filename = filename[:100]
        
        # 添加时间戳避免冲突
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return f"{filename}_{timestamp}"

    def _add_metadata(self, title: str, content: str) -> str:
        """添加元数据到文档
        
        Args:
            title: 文档标题
            content: 文档内容
            
        Returns:
            带元数据的完整内容
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        metadata = f"""---
title: {title}
created_at: {timestamp}
generated_by: TokenDance Agent
---

"""
        
        return metadata + content


# 全局实例
create_document_tool = CreateDocumentTool()
