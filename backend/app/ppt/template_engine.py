"""
Template Engine - 模板引擎

负责模板的注册、查找和管理。
"""

import logging

from .models import SlideContent, SlideType
from .templates.base import SlideTemplate
from .templates.builtin import get_all_templates

logger = logging.getLogger(__name__)


class TemplateEngine:
    """模板引擎

    负责管理所有幻灯片模板，根据类型选择合适的模板渲染幻灯片。

    使用示例：
        engine = TemplateEngine()
        engine.register_builtin_templates()

        template = engine.get_template(SlideType.TITLE)
        slide = template.render(prs, content, brand, config)
    """

    def __init__(self):
        self._templates: dict[SlideType, SlideTemplate] = {}
        self._template_by_name: dict[str, SlideTemplate] = {}
        logger.info("TemplateEngine initialized")

    def register(self, template: SlideTemplate) -> None:
        """注册模板

        Args:
            template: 模板实例
        """
        self._templates[template.slide_type] = template
        self._template_by_name[template.name] = template
        logger.debug(f"Registered template: {template.name} for {template.slide_type}")

    def register_class(self, template_class: type[SlideTemplate]) -> None:
        """注册模板类（自动实例化）

        Args:
            template_class: 模板类
        """
        template = template_class()
        self.register(template)

    def register_builtin_templates(self) -> None:
        """注册所有内置模板"""
        for template_class in get_all_templates():
            self.register_class(template_class)
        logger.info(f"Registered {len(self._templates)} builtin templates")

    def get_template(self, slide_type: SlideType) -> SlideTemplate | None:
        """根据幻灯片类型获取模板

        Args:
            slide_type: 幻灯片类型

        Returns:
            SlideTemplate: 模板实例，未找到返回 None
        """
        return self._templates.get(slide_type)

    def get_template_by_name(self, name: str) -> SlideTemplate | None:
        """根据名称获取模板

        Args:
            name: 模板名称

        Returns:
            SlideTemplate: 模板实例，未找到返回 None
        """
        return self._template_by_name.get(name)

    def get_or_default(
        self,
        slide_type: SlideType,
        default_type: SlideType = SlideType.CONTENT
    ) -> SlideTemplate:
        """获取模板，未找到时返回默认模板

        Args:
            slide_type: 幻灯片类型
            default_type: 默认类型

        Returns:
            SlideTemplate: 模板实例

        Raises:
            ValueError: 默认模板也未找到
        """
        template = self.get_template(slide_type)
        if template:
            return template

        logger.warning(
            f"Template for {slide_type} not found, using {default_type}"
        )

        default_template = self.get_template(default_type)
        if not default_template:
            raise ValueError(f"Default template {default_type} not found")

        return default_template

    def select_template(self, content: SlideContent) -> SlideTemplate:
        """智能选择模板

        根据内容特征自动选择最合适的模板。

        Args:
            content: 幻灯片内容

        Returns:
            SlideTemplate: 选择的模板
        """
        # 首先尝试使用指定的类型
        slide_type = content.type

        # 智能推断：如果指定类型没有对应模板，根据内容特征推断
        if slide_type not in self._templates:
            slide_type = self._infer_type(content)

        return self.get_or_default(slide_type)

    def _infer_type(self, content: SlideContent) -> SlideType:
        """根据内容推断幻灯片类型

        Args:
            content: 幻灯片内容

        Returns:
            SlideType: 推断的类型
        """
        # 有图片优先
        if content.image_path:
            if content.body or content.bullets:
                return SlideType.IMAGE_TEXT
            return SlideType.IMAGE

        # 有要点列表
        if content.bullets:
            return SlideType.BULLET

        # 有多栏内容
        if content.columns:
            if len(content.columns) >= 2:
                return SlideType.TWO_COLUMN

        # 有引用
        if content.quote:
            return SlideType.QUOTE

        # 有图表
        if content.chart:
            return SlideType.CHART

        # 有表格
        if content.table:
            return SlideType.TABLE

        # 默认内容页
        return SlideType.CONTENT

    def list_templates(self) -> list[dict]:
        """列出所有已注册模板

        Returns:
            List[Dict]: 模板信息列表
        """
        return [
            {
                "name": t.name,
                "type": t.slide_type.value if hasattr(t.slide_type, 'value') else str(t.slide_type),
                "description": t.description,
            }
            for t in self._templates.values()
        ]

    def has_template(self, slide_type: SlideType) -> bool:
        """检查是否有指定类型的模板

        Args:
            slide_type: 幻灯片类型

        Returns:
            bool: 是否存在
        """
        return slide_type in self._templates

    def __len__(self) -> int:
        return len(self._templates)

    def __repr__(self) -> str:
        return f"<TemplateEngine(templates={len(self._templates)})>"


# 全局模板引擎实例
_global_engine: TemplateEngine | None = None


def get_global_engine() -> TemplateEngine:
    """获取全局模板引擎（单例）

    Returns:
        TemplateEngine: 全局模板引擎
    """
    global _global_engine
    if _global_engine is None:
        _global_engine = TemplateEngine()
        _global_engine.register_builtin_templates()
    return _global_engine
