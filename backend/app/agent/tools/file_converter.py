"""
File Converter Tool - 文件转 Markdown 转换工具

使用 Microsoft MarkItDown 将各类文件格式转换为 Markdown，
便于 LLM 分析和处理。

支持的格式：
- Office文档: PDF, DOCX, PPTX, XLSX, XLS
- 图片: JPG, PNG, GIF, BMP, TIFF, WEBP (需 LLM client)
- 音频: WAV, MP3 (需语音识别)
- Web/结构化: HTML, CSV, JSON, XML
- 压缩包: ZIP (递归处理)
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Dict, Any

from app.agent.tools.base import Tool, ToolResult

logger = logging.getLogger(__name__)


class FileConverterTool(Tool):
    """
    文件转 Markdown 转换工具
    
    将各类文件格式转换为 Markdown，便于 Agent 分析。
    """
    
    name = "file_converter"
    description = (
        "将文件转换为 Markdown 格式。"
        "支持: PDF, DOCX, PPTX, XLSX, XLS, JPG, PNG, HTML, CSV, JSON, XML, ZIP。"
        "用于分析文档、提取内容、处理上传文件等场景。"
    )
    
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "要转换的文件路径（绝对路径或相对路径）"
            },
            "extract_images": {
                "type": "boolean",
                "description": "是否提取图片描述（需要 LLM，默认 False）",
                "default": False
            }
        },
        "required": ["file_path"]
    }
    
    def __init__(self, llm_client: Optional[Any] = None):
        """
        初始化文件转换工具
        
        Args:
            llm_client: LLM 客户端（用于图片描述），可选
        """
        super().__init__()
        self.llm_client = llm_client
        
        # 延迟导入 MarkItDown（避免启动时加载）
        self._markitdown = None
    
    def _get_markitdown(self):
        """延迟初始化 MarkItDown"""
        if self._markitdown is None:
            try:
                from markitdown import MarkItDown
                self._markitdown = MarkItDown(
                    llm_client=self.llm_client,
                    enable_plugins=False  # 默认禁用插件
                )
                logger.info("MarkItDown initialized successfully")
            except ImportError as e:
                logger.error(f"Failed to import MarkItDown: {e}")
                raise ImportError(
                    "MarkItDown not installed. "
                    "Install with: uv pip install markitdown"
                ) from e
        return self._markitdown
    
    async def execute(
        self, 
        file_path: str,
        extract_images: bool = False,
        **kwargs
    ) -> ToolResult:
        """
        执行文件转换
        
        Args:
            file_path: 文件路径
            extract_images: 是否提取图片描述
            
        Returns:
            ToolResult: 转换结果（Markdown 文本）
        """
        try:
            # 验证文件存在
            path = Path(file_path)
            if not path.exists():
                return ToolResult(
                    success=False,
                    error=f"File not found: {file_path}"
                )
            
            if not path.is_file():
                return ToolResult(
                    success=False,
                    error=f"Path is not a file: {file_path}"
                )
            
            # 获取 MarkItDown 实例
            md = self._get_markitdown()
            
            # 如果需要提取图片但没有 LLM client，警告用户
            if extract_images and not self.llm_client:
                logger.warning(
                    "extract_images=True but no LLM client configured. "
                    "Image descriptions will not be generated."
                )
            
            # 转换文件
            logger.info(f"Converting file: {file_path}")
            result = md.convert(str(path))
            
            # 提取元数据
            file_size = path.stat().st_size
            file_ext = path.suffix.lower()
            
            markdown_content = result.text_content
            char_count = len(markdown_content)
            line_count = markdown_content.count('\n') + 1
            
            logger.info(
                f"Conversion successful: {file_path} "
                f"({file_size} bytes -> {char_count} chars, {line_count} lines)"
            )
            
            return ToolResult(
                success=True,
                output=markdown_content,
                metadata={
                    "source_file": str(path),
                    "file_extension": file_ext,
                    "file_size_bytes": file_size,
                    "markdown_chars": char_count,
                    "markdown_lines": line_count,
                }
            )
        
        except ImportError as e:
            return ToolResult(
                success=False,
                error=f"MarkItDown dependency error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"File conversion failed for {file_path}: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Conversion error: {type(e).__name__}: {str(e)}"
            )
    
    def get_supported_formats(self) -> Dict[str, list]:
        """
        获取支持的文件格式列表
        
        Returns:
            dict: 按类别分组的文件扩展名
        """
        return {
            "office": [".pdf", ".docx", ".pptx", ".xlsx", ".xls"],
            "images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"],
            "audio": [".wav", ".mp3"],
            "web": [".html", ".htm"],
            "structured": [".csv", ".json", ".xml"],
            "archives": [".zip"]
        }
