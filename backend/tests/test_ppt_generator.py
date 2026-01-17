"""
PPT Generator Tests - PPT 生成模块测试

测试内容：
- 数据模型验证
- 模板引擎功能
- PPT 生成和导出
- Agent 工具调用
"""

from pathlib import Path

import pytest

from app.ppt.generator import PPTGenerator, quick_generate
from app.ppt.models import (
    BrandKit,
    PresentationSpec,
    SlideContent,
    SlideType,
)
from app.ppt.template_engine import TemplateEngine, get_global_engine


class TestModels:
    """数据模型测试"""

    def test_slide_type_enum(self):
        """测试幻灯片类型枚举"""
        assert SlideType.TITLE == "title"
        assert SlideType.BULLET == "bullet"
        assert SlideType.TWO_COLUMN == "two_column"

    def test_brand_kit_default(self):
        """测试品牌配置默认值"""
        brand = BrandKit()
        assert brand.primary_color == "#1a1a2e"
        assert brand.background_color == "#ffffff"

    def test_brand_kit_dark_theme(self):
        """测试深色主题"""
        brand = BrandKit.default_dark()
        assert brand.background_color == "#1a1a2e"
        assert brand.text_primary == "#f3f4f6"

    def test_slide_content_creation(self):
        """测试幻灯片内容创建"""
        slide = SlideContent(
            type=SlideType.BULLET,
            title="测试标题",
            bullets=["要点1", "要点2", "要点3"]
        )
        assert slide.title == "测试标题"
        assert len(slide.bullets) == 3

    def test_presentation_spec(self):
        """测试演示文稿规格"""
        spec = PresentationSpec(title="测试演示")
        spec.add_title_slide("欢迎", "副标题")
        spec.add_bullet_slide("要点", ["1", "2"])
        spec.add_section_slide("章节")

        assert len(spec.slides) == 3
        assert spec.slides[0].type == SlideType.TITLE
        assert spec.slides[1].type == SlideType.BULLET
        assert spec.slides[2].type == SlideType.SECTION


class TestTemplateEngine:
    """模板引擎测试"""

    def test_engine_initialization(self):
        """测试引擎初始化"""
        engine = TemplateEngine()
        engine.register_builtin_templates()
        assert len(engine) >= 10  # 至少 10 个内置模板

    def test_get_template(self):
        """测试获取模板"""
        engine = get_global_engine()

        title_template = engine.get_template(SlideType.TITLE)
        assert title_template is not None
        assert title_template.slide_type == SlideType.TITLE

        bullet_template = engine.get_template(SlideType.BULLET)
        assert bullet_template is not None

    def test_select_template_by_content(self):
        """测试根据内容选择模板"""
        engine = get_global_engine()

        # 明确指定 BULLET 类型
        content = SlideContent(type=SlideType.BULLET, bullets=["1", "2"])
        template = engine.select_template(content)
        assert template.slide_type == SlideType.BULLET

        # 默认 CONTENT 类型
        content2 = SlideContent(body="test")
        template2 = engine.select_template(content2)
        assert template2.slide_type == SlideType.CONTENT

    def test_list_templates(self):
        """测试列出模板"""
        engine = get_global_engine()
        templates = engine.list_templates()

        assert len(templates) > 0
        assert all("name" in t for t in templates)
        assert all("type" in t for t in templates)


class TestPPTGenerator:
    """PPT 生成器测试"""

    @pytest.fixture
    def generator(self, tmp_path):
        """创建生成器实例"""
        return PPTGenerator(output_dir=str(tmp_path))

    @pytest.mark.asyncio
    async def test_generate_simple_ppt(self, generator, tmp_path):
        """测试生成简单 PPT"""
        slides = [
            SlideContent(type=SlideType.TITLE, title="测试演示", subtitle="副标题"),
            SlideContent(type=SlideType.BULLET, title="要点", bullets=["要点1", "要点2"]),
            SlideContent(type=SlideType.THANK_YOU, title="谢谢"),
        ]

        output_path = tmp_path / "test.pptx"
        result = await generator.generate(slides, output_path=str(output_path))

        assert Path(result).exists()
        assert result.endswith(".pptx")

    @pytest.mark.asyncio
    async def test_generate_from_outline(self, generator, tmp_path):
        """测试从大纲生成"""
        outline = [
            {"type": "title", "title": "大纲测试", "subtitle": "副标题"},
            {"type": "bullet", "title": "要点页", "bullets": ["A", "B", "C"]},
            {"type": "section", "title": "章节"},
            {"type": "quote", "quote": "这是一段引用", "quote_author": "作者"},
        ]

        result = await generator.generate_from_outline(
            outline=outline,
            output_path=str(tmp_path / "outline.pptx")
        )

        assert Path(result).exists()

    @pytest.mark.asyncio
    async def test_generate_from_spec(self, generator, tmp_path):
        """测试从规格生成"""
        spec = PresentationSpec(
            title="规格测试",
            brand=BrandKit.default_light()
        )
        spec.add_title_slide("标题", "副标题")
        spec.add_bullet_slide("要点", ["1", "2", "3"])

        result = await generator.generate_from_spec(
            spec=spec,
            output_path=str(tmp_path / "spec.pptx")
        )

        assert Path(result).exists()

    @pytest.mark.asyncio
    async def test_quick_generate(self, tmp_path):
        """测试快速生成函数"""
        slides = [
            {"type": "title", "title": "快速生成测试"},
            {"type": "bullet", "title": "内容", "bullets": ["快速", "简单"]},
        ]

        result = await quick_generate(
            slides=slides,
            output_path=str(tmp_path / "quick.pptx")
        )

        assert Path(result).exists()

    def test_supported_types(self, generator):
        """测试支持的类型"""
        types = generator.get_supported_slide_types()
        assert "title" in types
        assert "bullet" in types
        assert "two_column" in types

    def test_template_info(self, generator):
        """测试模板信息"""
        info = generator.get_template_info()
        assert len(info) > 0


class TestAgentTool:
    """Agent 工具测试"""

    @pytest.mark.asyncio
    async def test_generate_ppt_tool(self, tmp_path):
        """测试 GeneratePPTTool"""
        from app.agent.tools.builtin.ppt_generator import GeneratePPTTool

        tool = GeneratePPTTool(output_dir=str(tmp_path))

        result = await tool.execute(
            title="工具测试",
            slides=[
                {"type": "title", "title": "工具测试"},
                {"type": "bullet", "title": "功能", "bullets": ["功能1", "功能2"]},
            ]
        )

        assert "successfully" in result.lower() or "generated" in result.lower()

    @pytest.mark.asyncio
    async def test_quick_ppt_tool(self, tmp_path):
        """测试 QuickPPTTool"""
        from app.agent.tools.builtin.ppt_generator import QuickPPTTool

        tool = QuickPPTTool(output_dir=str(tmp_path))

        result = await tool.execute(
            title="快速工具测试",
            sections=[
                {"title": "章节1", "points": ["要点A", "要点B"]},
                {"title": "章节2", "points": ["要点C", "要点D"]},
            ]
        )

        assert "generated" in result.lower() or "pptx" in result.lower()


class TestTemplateRendering:
    """模板渲染测试"""

    @pytest.mark.asyncio
    async def test_all_template_types(self, tmp_path):
        """测试所有模板类型渲染"""
        generator = PPTGenerator(output_dir=str(tmp_path))

        slides = [
            SlideContent(type=SlideType.TITLE, title="标题", subtitle="副标题"),
            SlideContent(type=SlideType.SECTION, title="章节"),
            SlideContent(type=SlideType.BULLET, title="要点", bullets=["A", "B", "C"]),
            SlideContent(
                type=SlideType.TWO_COLUMN,
                title="双栏",
                columns=[
                    {"title": "左栏", "content": "左侧内容"},
                    {"title": "右栏", "content": "右侧内容"},
                ]
            ),
            SlideContent(type=SlideType.QUOTE, quote="引用文字", quote_author="作者"),
            SlideContent(type=SlideType.CONTENT, title="内容", body="这是正文内容"),
            SlideContent(type=SlideType.THANK_YOU, title="感谢"),
            SlideContent(type=SlideType.BLANK),
        ]

        result = await generator.generate(
            slides=slides,
            output_path=str(tmp_path / "all_templates.pptx")
        )

        assert Path(result).exists()
        # 验证文件大小（应该有一定内容）
        assert Path(result).stat().st_size > 10000  # 至少 10KB
