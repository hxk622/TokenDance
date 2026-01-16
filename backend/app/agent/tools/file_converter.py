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
import os
from pathlib import Path
from typing import Optional, Dict, Any

from app.agent.tools.base import BaseTool

# Export MarkItDown for testing
try:
    from markitdown import MarkItDown  # noqa: F401
except ImportError:
    MarkItDown = None  # type: ignore

# OpenAI client for MarkItDown (OpenRouter compatible)
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore

logger = logging.getLogger(__name__)


class FileConverterTool(BaseTool):
    """
    文件转 Markdown 转换工具
    
    将各类文件格式转换为 Markdown，便于 Agent 分析。
    """
    
    name = "file_converter"
    category = "File Operations"
    description = (
        "Convert files (PDF, DOCX, PPTX, XLSX, XLS, JPG, PNG, HTML, CSV, JSON, XML, ZIP) to Markdown format. "
        "Useful for document analysis, content extraction, and processing uploaded files."
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
    
    def __init__(
        self, 
        llm_client: Optional[Any] = None,
        openrouter_api_key: Optional[str] = None,
        vision_model: Optional[str] = None,
        vision_task_type: str = "general"
    ):
        """
        初始化文件转换工具
        
        Args:
            llm_client: LLM 客户端（用于图片描述），可选（已废弃，请使用 openrouter_api_key）
            openrouter_api_key: OpenRouter API Key（推荐方式）
            vision_model: 视觉模型名称（如 anthropic/claude-3-haiku）
            vision_task_type: 视觉任务类型（"ocr", "chart", "diagram", "general"）
        """
        super().__init__()
        self.llm_client = llm_client  # 保留向后兼容
        self.vision_task_type = vision_task_type
        
        # 确定 Vision 模型（根据任务类型智能选择）
        if vision_model:
            self.vision_model = vision_model
        else:
            # 根据任务类型选择默认模型
            self.vision_model = self._select_default_vision_model(vision_task_type)
        
        # 创建 OpenAI-compatible 客户端（指向 OpenRouter）
        self._openai_client = None
        api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        
        if api_key:
            if OpenAI is None:
                logger.warning(
                    "openai package not installed. "
                    "Install with: uv pip install openai"
                )
            else:
                try:
                    self._openai_client = OpenAI(
                        api_key=api_key,
                        base_url="https://openrouter.ai/api/v1",
                        default_headers={
                            "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "https://tokendance.app"),
                            "X-Title": os.getenv("OPENROUTER_APP_NAME", "TokenDance")
                        }
                    )
                    logger.info(
                        f"OpenRouter Vision client initialized with model: {self.vision_model}"
                    )
                except Exception as e:
                    logger.error(f"Failed to initialize OpenRouter client: {e}")
        else:
            logger.warning(
                "No OpenRouter API key configured. "
                "Image descriptions will not be generated. "
                "Set OPENROUTER_API_KEY in environment or pass openrouter_api_key parameter."
            )
        
        # 延迟导入 MarkItDown（避免启动时加载）
        self._converter = None
    
    def _select_default_vision_model(self, task_type: str) -> str:
        """
        根据任务类型选择默认视觉模型
        
        Args:
            task_type: 任务类型（"ocr", "chart", "diagram", "general"）
            
        Returns:
            str: 模型名称
        """
        # Vision 任务类型 → 模型映射
        task_to_model = {
            "ocr": "anthropic/claude-3-haiku",          # 文字提取：快速便宜
            "chart": "anthropic/claude-3-5-sonnet",    # 图表分析：平衡
            "diagram": "anthropic/claude-3-5-sonnet",  # 科学示意图：平衡
            "general": "google/gemini-pro-vision"      # 通用：极致性价比
        }
        return task_to_model.get(task_type, "anthropic/claude-3-5-sonnet")
    
    def _get_markitdown(self):
        """延迟初始化 MarkItDown"""
        if self._converter is None:
            try:
                from markitdown import MarkItDown
                
                # 优先使用 OpenRouter 客户端
                client = self._openai_client or self.llm_client
                
                if client:
                    self._converter = MarkItDown(
                        llm_client=client,
                        llm_model=self.vision_model,
                        enable_plugins=False
                    )
                    logger.info(
                        f"MarkItDown initialized with Vision model: {self.vision_model}"
                    )
                else:
                    # 无 Vision 能力的基础版本
                    self._converter = MarkItDown(enable_plugins=False)
                    logger.info("MarkItDown initialized (without Vision)")
                    
            except ImportError as e:
                logger.error(f"Failed to import MarkItDown: {e}")
                raise ImportError(
                    "MarkItDown not installed. "
                    "Install with: uv pip install 'markitdown[all]'"
                ) from e
        return self._converter
    
    def execute(
        self, 
        file_path: str = "",
        extract_images: bool = False,
        **kwargs
    ) -> str:
        """
        执行文件转换（同步方法）
        
        Args:
            file_path: 文件路径
            extract_images: 是否提取图片描述
            
        Returns:
            str: 转换后的 Markdown 文本
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不支持或路径无效
        """
        # 验证输入
        if not file_path or file_path.strip() == "":
            raise ValueError("file_path cannot be empty")
        
        # 验证文件存在
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        # 检查文件格式
        supported_extensions = {
            ext for formats in self.get_supported_formats().values() 
            for ext in formats
        }
        if path.suffix.lower() not in supported_extensions:
            raise ValueError(
                f"Unsupported file format: {path.suffix}. "
                f"Supported formats: {', '.join(sorted(supported_extensions))}"
            )
        
        try:
            # 获取 MarkItDown 实例
            md = self._get_markitdown()
            
            # 如果需要提取图片但没有 Vision client，警告用户
            if extract_images and not self._openai_client and not self.llm_client:
                logger.warning(
                    "extract_images=True but no Vision client configured. "
                    "Image descriptions will not be generated. "
                    "Set OPENROUTER_API_KEY to enable Vision."
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
            
            # 返回带元信息的结果（使用 YAML front matter）
            header = (
                f"---\n"
                f"Source: {path.name}\n"
                f"Format: {file_ext}\n"
                f"Size: {file_size} bytes\n"
                f"Lines: {line_count}\n"
                f"---\n\n"
            )
            return header + markdown_content
        
        except ImportError as e:
            logger.error(f"MarkItDown dependency error: {e}")
            raise ImportError(
                "MarkItDown not installed. Install with: uv pip install markitdown"
            ) from e
        except Exception as e:
            logger.error(f"File conversion failed for {file_path}: {e}", exc_info=True)
            raise
    
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
            "archives": [".zip"],
            "text": [".txt", ".md"]
        }
