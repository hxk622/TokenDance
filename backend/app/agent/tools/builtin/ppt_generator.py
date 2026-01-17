"""
PPT Generator Tool - PPT 生成工具

Agent 工具，用于生成演示文稿。
支持从大纲、结构化内容生成专业 PPT。
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from ..base import BaseTool, ToolResult
from ..risk import OperationCategory, RiskLevel

logger = logging.getLogger(__name__)


class GeneratePPTTool(BaseTool):
    """PPT 生成工具

    根据结构化内容生成专业演示文稿。
    支持多种幻灯片类型：标题、要点、双栏、图片、引用等。

    风险等级：LOW（文件创建操作）
    """

    name = "generate_ppt"
    description = """生成专业演示文稿（PPT/PPTX）。
根据提供的大纲和内容，自动生成结构化、设计精美的演示文稿。

支持的幻灯片类型：
- title: 标题页（主标题 + 副标题）
- section: 章节分隔页
- bullet: 要点列表页（标题 + 要点列表）
- two_column: 双栏对比页
- image: 图片页
- image_text: 图文混排页
- quote: 引用页
- content: 通用内容页
- thank_you: 感谢页

使用场景：研究报告演示、产品介绍、会议汇报、培训材料等。"""

    parameters = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "演示文稿标题"
            },
            "slides": {
                "type": "array",
                "description": "幻灯片内容列表",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": [
                                "title", "section", "bullet", "two_column",
                                "image", "image_text", "quote", "content",
                                "thank_you", "blank"
                            ],
                            "description": "幻灯片类型"
                        },
                        "title": {
                            "type": "string",
                            "description": "标题"
                        },
                        "subtitle": {
                            "type": "string",
                            "description": "副标题（用于 title/thank_you 类型）"
                        },
                        "body": {
                            "type": "string",
                            "description": "正文内容（用于 content 类型）"
                        },
                        "bullets": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "要点列表（用于 bullet 类型）"
                        },
                        "columns": {
                            "type": "array",
                            "description": "双栏内容（用于 two_column 类型）",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "content": {"type": "string"}
                                }
                            }
                        },
                        "image_path": {
                            "type": "string",
                            "description": "图片路径（用于 image/image_text 类型）"
                        },
                        "image_caption": {
                            "type": "string",
                            "description": "图片说明"
                        },
                        "quote": {
                            "type": "string",
                            "description": "引用文字（用于 quote 类型）"
                        },
                        "quote_author": {
                            "type": "string",
                            "description": "引用作者"
                        },
                        "speaker_notes": {
                            "type": "string",
                            "description": "演讲者备注"
                        }
                    }
                }
            },
            "theme": {
                "type": "string",
                "enum": ["light", "dark"],
                "default": "light",
                "description": "主题风格：light（浅色）或 dark（深色）"
            },
            "output_filename": {
                "type": "string",
                "description": "输出文件名（可选，默认自动生成）"
            }
        },
        "required": ["title", "slides"]
    }

    risk_level = RiskLevel.LOW
    operation_categories = [OperationCategory.DOCUMENT_CREATE]
    requires_confirmation = False

    def __init__(self, output_dir: str = "/tmp/tokendance/ppt"):
        super().__init__()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def execute(self, **kwargs: Any) -> str:
        """执行 PPT 生成

        Args:
            title: 演示文稿标题
            slides: 幻灯片内容列表
            theme: 主题风格
            output_filename: 输出文件名

        Returns:
            str: 生成结果信息
        """
        title = kwargs.get("title", "Presentation")
        slides = kwargs.get("slides", [])
        theme = kwargs.get("theme", "light")
        output_filename = kwargs.get("output_filename")

        if not slides:
            return ToolResult(
                success=False,
                error="No slides provided. Please provide at least one slide."
            ).to_text()

        try:
            # 延迟导入，避免循环依赖
            from app.ppt import BrandKit, PPTGenerator

            # 选择主题
            if theme == "dark":
                brand = BrandKit.default_dark()
            else:
                brand = BrandKit.default_light()

            # 确定输出路径
            if output_filename:
                if not output_filename.endswith('.pptx'):
                    output_filename += '.pptx'
                output_path = self.output_dir / output_filename
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = self.output_dir / f"presentation_{timestamp}.pptx"

            # 生成 PPT
            generator = PPTGenerator(output_dir=str(self.output_dir))
            pptx_path = await generator.generate_from_outline(
                outline=slides,
                brand=brand,
                output_path=str(output_path),
                title=title
            )

            # 返回结果
            result = ToolResult(
                success=True,
                data={
                    "file_path": pptx_path,
                    "title": title,
                    "slide_count": len(slides),
                    "theme": theme
                },
                summary=f"PPT generated successfully: {pptx_path} ({len(slides)} slides)"
            )

            return result.to_text()

        except ImportError as e:
            logger.error(f"Failed to import PPT module: {e}")
            return ToolResult(
                success=False,
                error=f"PPT module not available: {str(e)}"
            ).to_text()
        except Exception as e:
            logger.error(f"PPT generation failed: {e}")
            return ToolResult(
                success=False,
                error=f"PPT generation failed: {str(e)}"
            ).to_text()

    def get_confirmation_description(self, **kwargs) -> str:
        """获取确认描述"""
        title = kwargs.get("title", "Presentation")
        slides = kwargs.get("slides", [])
        return f"Generate PPT '{title}' with {len(slides)} slides"


class QuickPPTTool(BaseTool):
    """快速 PPT 生成工具

    简化版 PPT 生成，从纯文本大纲快速生成演示文稿。
    """

    name = "quick_ppt"
    description = """从文本大纲快速生成 PPT。
提供演示标题和章节内容，自动生成完整演示文稿（包含标题页和感谢页）。

适合快速创建简单演示文稿，如会议汇报、简短介绍等。"""

    parameters = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "演示文稿标题"
            },
            "subtitle": {
                "type": "string",
                "description": "副标题（可选）"
            },
            "sections": {
                "type": "array",
                "description": "章节列表",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "章节标题"
                        },
                        "points": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "章节要点"
                        }
                    },
                    "required": ["title", "points"]
                }
            }
        },
        "required": ["title", "sections"]
    }

    risk_level = RiskLevel.LOW
    operation_categories = [OperationCategory.DOCUMENT_CREATE]
    requires_confirmation = False

    def __init__(self, output_dir: str = "/tmp/tokendance/ppt"):
        super().__init__()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def execute(self, **kwargs: Any) -> str:
        """执行快速 PPT 生成"""
        title = kwargs.get("title", "Presentation")
        subtitle = kwargs.get("subtitle")
        sections = kwargs.get("sections", [])

        if not sections:
            return ToolResult(
                success=False,
                error="No sections provided."
            ).to_text()

        try:
            from app.ppt import PPTGenerator

            # 构建幻灯片大纲
            slides = [
                {"type": "title", "title": title, "subtitle": subtitle}
            ]

            for section in sections:
                # 章节分隔页
                slides.append({
                    "type": "section",
                    "title": section.get("title", "")
                })

                # 章节内容页
                slides.append({
                    "type": "bullet",
                    "title": section.get("title", ""),
                    "bullets": section.get("points", [])
                })

            # 感谢页
            slides.append({
                "type": "thank_you",
                "title": "Thank You",
                "subtitle": subtitle
            })

            # 生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"quick_ppt_{timestamp}.pptx"

            generator = PPTGenerator(output_dir=str(self.output_dir))
            pptx_path = await generator.generate_from_outline(
                outline=slides,
                output_path=str(output_path),
                title=title
            )

            return ToolResult(
                success=True,
                data={
                    "file_path": pptx_path,
                    "title": title,
                    "sections": len(sections)
                },
                summary=f"Quick PPT generated: {pptx_path}"
            ).to_text()

        except Exception as e:
            logger.error(f"Quick PPT generation failed: {e}")
            return ToolResult(
                success=False,
                error=f"Generation failed: {str(e)}"
            ).to_text()


def create_ppt_tools(output_dir: str = "/tmp/tokendance/ppt") -> list[BaseTool]:
    """创建 PPT 生成工具集

    Args:
        output_dir: 输出目录

    Returns:
        List[BaseTool]: PPT 工具列表
    """
    return [
        GeneratePPTTool(output_dir=output_dir),
        QuickPPTTool(output_dir=output_dir),
    ]
