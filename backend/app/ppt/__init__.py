"""
PPT Generation Module - AI PPT 生成模块

支持 Template-Driven PPT 生成：
- 模板引擎：管理和渲染幻灯片模板
- PPT 生成器：协调模板生成完整演示文稿
- PPTX 导出：生成标准 PowerPoint 文件

使用示例：
    from app.ppt import PPTGenerator, SlideContent, SlideType

    generator = PPTGenerator()
    slides = [
        SlideContent(type=SlideType.TITLE, title="演示标题", subtitle="副标题"),
        SlideContent(type=SlideType.BULLET, title="要点", bullets=["要点1", "要点2"]),
    ]
    pptx_path = await generator.generate(slides, output_path="output.pptx")
"""

from .models import (
    SlideType,
    SlideContent,
    PresentationSpec,
    BrandKit,
    TemplateConfig,
)
from .generator import PPTGenerator
from .template_engine import TemplateEngine

__all__ = [
    # Models
    "SlideType",
    "SlideContent",
    "PresentationSpec",
    "BrandKit",
    "TemplateConfig",
    # Generator
    "PPTGenerator",
    # Engine
    "TemplateEngine",
]
