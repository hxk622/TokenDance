"""
File Converter Tool - 文件转 Markdown 转换工具

使用智能路由选择最优解析引擎：
- MarkItDown: 简单文档（快速）
- MinerU: 复杂文档/金融报告（高精度）

支持的格式：
- Office文档: PDF, DOCX, PPTX, XLSX, XLS
- 图片: JPG, PNG, GIF, BMP, TIFF, WEBP (需 LLM client)
- 音频: WAV, MP3 (需语音识别)
- Web/结构化: HTML, CSV, JSON, XML
- 压缩包: ZIP (递归处理)

PDF 智能路由：
- 简单 PDF → MarkItDown (快速)
- 复杂 PDF/金融报告 → MinerU (高精度，需配置 MINERU_API_TOKEN)
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Literal

from app.agent.tools.base import BaseTool
from app.agent.tools.smart_document_converter import (
    ConversionMetrics,
    SmartDocumentConverter,
)

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
            },
            "force_engine": {
                "type": "string",
                "enum": ["auto", "markitdown", "mineru"],
                "description": "强制使用指定引擎: auto=智能选择, markitdown=快速, mineru=高精度",
                "default": "auto"
            }
        },
        "required": ["file_path"]
    }

    def __init__(
        self,
        llm_client: Any | None = None,
        openrouter_api_key: str | None = None,
        vision_model: str | None = None,
        vision_task_type: str = "general",
        mineru_api_token: str | None = None,
    ):
        """
        初始化文件转换工具

        Args:
            llm_client: LLM 客户端（用于图片描述），可选（已废弃，请使用 openrouter_api_key）
            openrouter_api_key: OpenRouter API Key（推荐方式）
            vision_model: 视觉模型名称（如 anthropic/claude-3-haiku）
            vision_task_type: 视觉任务类型（"ocr", "chart", "diagram", "general"）
            mineru_api_token: MinerU API Token（用于复杂 PDF 解析）
        """
        super().__init__()
        self.llm_client = llm_client  # 保留向后兼容
        self.vision_task_type = vision_task_type

        # 智能文档转换器（用于 PDF）
        self._smart_converter = SmartDocumentConverter(
            mineru_api_token=mineru_api_token or os.getenv("MINERU_API_TOKEN"),
            log_metrics=True,
        )

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
        self._converter: Any = None

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

    def _get_markitdown(self) -> Any:
        """延迟初始化 MarkItDown"""
        if self._converter is None:
            try:
                from markitdown import MarkItDown

                # 优先使用 OpenRouter 客户端
                client = self._openai_client or self.llm_client

                if client:
                    self._converter = MarkItDown(
                        llm_client=client,
                        llm_model=self.vision_model
                    )
                    logger.info(
                        f"MarkItDown initialized with Vision model: {self.vision_model}"
                    )
                else:
                    # 无 Vision 能力的基础版本
                    self._converter = MarkItDown()
                    logger.info("MarkItDown initialized (without Vision)")

            except ImportError as e:
                logger.error(f"Failed to import MarkItDown: {e}")
                raise ImportError(
                    "MarkItDown not installed. "
                    "Install with: uv pip install 'markitdown[all]'"
                ) from e
        return self._converter

    def execute(  # type: ignore[override]
        self,
        file_path: str = "",
        extract_images: bool = False,
        force_engine: Literal["auto", "markitdown", "mineru"] = "auto",
        **kwargs: Any
    ) -> str:
        """
        执行文件转换（同步方法）

        Args:
            file_path: 文件路径
            extract_images: 是否提取图片描述
            force_engine: 强制使用指定引擎 (仅对 PDF 有效)
                - "auto": 智能选择（默认）
                - "markitdown": 强制使用 MarkItDown（快速）
                - "mineru": 强制使用 MinerU（高精度）

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
            file_ext = path.suffix.lower()
            file_size = path.stat().st_size

            # PDF 使用智能转换器
            if file_ext == ".pdf":
                return self._convert_pdf_smart(
                    path, file_size, force_engine
                )

            # 其他格式使用 MarkItDown
            return self._convert_with_markitdown(
                path, file_size, file_ext, extract_images
            )

        except ImportError as e:
            logger.error(f"Dependency error: {e}")
            raise
        except Exception as e:
            logger.error(f"File conversion failed for {file_path}: {e}", exc_info=True)
            raise

    def _convert_pdf_smart(
        self,
        path: Path,
        file_size: int,
        force_engine: Literal["auto", "markitdown", "mineru"],
    ) -> str:
        """
        使用智能转换器处理 PDF

        自动根据文档复杂度选择最优引擎：
        - 简单 PDF → MarkItDown
        - 复杂 PDF/金融报告 → MinerU
        """
        # 设置强制引擎
        self._smart_converter.force_engine = force_engine

        # 转换
        markdown_content, metrics = self._smart_converter.convert(str(path))

        line_count = markdown_content.count('\n') + 1

        # 构建元信息头（包含引擎选择信息）
        header = (
            f"---\n"
            f"Source: {path.name}\n"
            f"Format: .pdf\n"
            f"Size: {file_size} bytes\n"
            f"Lines: {line_count}\n"
            f"Engine: {metrics.engine_used}\n"
            f"EngineReason: {metrics.engine_reason}\n"
            f"ComplexityScore: {metrics.complexity_score}\n"
            f"Latency: {metrics.total_latency_ms:.0f}ms\n"
            f"---\n\n"
        )
        return header + markdown_content

    def _convert_with_markitdown(
        self,
        path: Path,
        file_size: int,
        file_ext: str,
        extract_images: bool,
    ) -> str:
        """
        使用 MarkItDown 转换非 PDF 文件
        """
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
        logger.info(f"Converting file with MarkItDown: {path}")
        result = md.convert(str(path))

        markdown_content = result.text_content
        char_count = len(markdown_content)
        line_count = markdown_content.count('\n') + 1

        logger.info(
            f"Conversion successful: {path} "
            f"({file_size} bytes -> {char_count} chars, {line_count} lines)"
        )

        # 返回带元信息的结果（使用 YAML front matter）
        header = (
            f"---\n"
            f"Source: {path.name}\n"
            f"Format: {file_ext}\n"
            f"Size: {file_size} bytes\n"
            f"Lines: {line_count}\n"
            f"Engine: markitdown\n"
            f"---\n\n"
        )
        return str(header + markdown_content)

    def get_last_metrics(self) -> ConversionMetrics | None:
        """
        获取最后一次 PDF 转换的详细指标

        Returns:
            ConversionMetrics 或 None（如果没有进行过 PDF 转换）
        """
        # SmartDocumentConverter 不保存历史，这里返回 None
        # 如果需要，可以扩展 SmartDocumentConverter 保存最后一次的 metrics
        return None

    def get_supported_formats(self) -> dict[str, list[str]]:
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
