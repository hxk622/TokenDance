"""
PPT Templates - 幻灯片模板

包含：
- SlideTemplate: 模板抽象基类
- 内置模板：title, bullet, two_column, image, section 等
"""

from .base import SlideTemplate
from .builtin import (
    BlankSlideTemplate,
    BulletSlideTemplate,
    ContentSlideTemplate,
    ImageSlideTemplate,
    ImageTextSlideTemplate,
    QuoteSlideTemplate,
    SectionSlideTemplate,
    ThankYouSlideTemplate,
    TitleSlideTemplate,
    TwoColumnSlideTemplate,
    get_all_templates,
)

__all__ = [
    # Base
    "SlideTemplate",
    # Builtin templates
    "TitleSlideTemplate",
    "SectionSlideTemplate",
    "BulletSlideTemplate",
    "TwoColumnSlideTemplate",
    "ImageSlideTemplate",
    "ImageTextSlideTemplate",
    "QuoteSlideTemplate",
    "ContentSlideTemplate",
    "ThankYouSlideTemplate",
    "BlankSlideTemplate",
    # Helper
    "get_all_templates",
]
