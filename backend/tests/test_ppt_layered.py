"""
Tests for PPT Layered Generation Module

Phase 2: 分层图像生成测试
"""

import os
import tempfile
from pathlib import Path

from PIL import Image

from app.ppt.layered import (
    BackgroundGenerator,
    BackgroundStyle,
    CompositePresets,
    CompositeSpec,
    DecorationConfig,
    DecorationGenerator,
    DecorationStyle,
    GeometricConfig,
    GradientConfig,
    LayerCompositor,
    LayeredSlideContent,
    LayeredSlideGenerator,
    LayeredSlideStyle,
    LayerSpec,
    ParticleConfig,
    TextZone,
    WaveConfig,
)


class TestBackgroundGenerator:
    """背景生成器测试"""

    def test_init(self):
        """测试初始化"""
        gen = BackgroundGenerator(1920, 1080)
        assert gen.width == 1920
        assert gen.height == 1080

    def test_generate_solid(self):
        """测试纯色背景"""
        gen = BackgroundGenerator(800, 600)
        img = gen.generate_solid("#4a90e2")

        assert img.size == (800, 600)
        assert img.mode == "RGB"

    def test_generate_linear_gradient(self):
        """测试线性渐变"""
        gen = BackgroundGenerator(800, 600)
        config = GradientConfig(colors=["#1a1a2e", "#4a90e2"], angle=45)
        img = gen.generate_linear_gradient(config)

        assert img.size == (800, 600)
        assert img.mode == "RGB"

    def test_generate_radial_gradient(self):
        """测试径向渐变"""
        gen = BackgroundGenerator(800, 600)
        config = GradientConfig(colors=["#4a90e2", "#1a1a2e"])
        img = gen.generate_radial_gradient(config)

        assert img.size == (800, 600)

    def test_generate_circles(self):
        """测试圆形图案"""
        gen = BackgroundGenerator(800, 600)
        config = GeometricConfig(size=30)
        img = gen.generate_circles(config)

        assert img.size == (800, 600)

    def test_generate_hexagons(self):
        """测试六边形图案"""
        gen = BackgroundGenerator(800, 600)
        config = GeometricConfig(size=40)
        img = gen.generate_hexagons(config)

        assert img.size == (800, 600)

    def test_generate_grid(self):
        """测试网格背景"""
        gen = BackgroundGenerator(800, 600)
        config = GeometricConfig(size=50)
        img = gen.generate_grid(config)

        assert img.size == (800, 600)

    def test_generate_wave(self):
        """测试波浪背景"""
        gen = BackgroundGenerator(800, 600)
        config = WaveConfig(layers=3)
        img = gen.generate_wave(config, "#1a1a2e")

        assert img.size == (800, 600)

    def test_generate_particles(self):
        """测试粒子背景"""
        gen = BackgroundGenerator(800, 600)
        config = ParticleConfig(count=30)
        img = gen.generate_particles(config, "#1a1a2e")

        assert img.size == (800, 600)

    def test_generate_by_style(self):
        """测试通过样式枚举生成"""
        gen = BackgroundGenerator(800, 600)

        for style in BackgroundStyle:
            img = gen.generate(style)
            assert img.size == (800, 600)

    def test_save_and_load(self):
        """测试保存和加载"""
        gen = BackgroundGenerator(800, 600)
        img = gen.generate_solid("#4a90e2")

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name

        try:
            saved_path = gen.save(img, path)
            assert Path(saved_path).exists()

            loaded = Image.open(saved_path)
            assert loaded.size == (800, 600)
        finally:
            Path(path).unlink(missing_ok=True)


class TestDecorationGenerator:
    """装饰生成器测试"""

    def test_init(self):
        """测试初始化"""
        gen = DecorationGenerator(1920, 1080)
        assert gen.width == 1920
        assert gen.height == 1080

    def test_generate_corner_circles(self):
        """测试角落圆形装饰"""
        gen = DecorationGenerator(800, 600)
        config = DecorationConfig(size=100)
        img = gen.generate_corner_circles(config)

        assert img.size == (800, 600)
        assert img.mode == "RGBA"

    def test_generate_corner_lines(self):
        """测试角落线条装饰"""
        gen = DecorationGenerator(800, 600)
        config = DecorationConfig(size=80)
        img = gen.generate_corner_lines(config)

        assert img.size == (800, 600)
        assert img.mode == "RGBA"

    def test_generate_spotlight(self):
        """测试聚光灯效果"""
        gen = DecorationGenerator(800, 600)
        config = DecorationConfig(size=150, position="center")
        img = gen.generate_spotlight(config)

        assert img.size == (800, 600)

    def test_generate_by_style(self):
        """测试通过样式枚举生成"""
        gen = DecorationGenerator(800, 600)

        for style in DecorationStyle:
            img = gen.generate(style)
            assert img.size == (800, 600)
            assert img.mode == "RGBA"

    def test_composite_with_background(self):
        """测试与背景合成"""
        bg_gen = BackgroundGenerator(800, 600)
        deco_gen = DecorationGenerator(800, 600)

        bg = bg_gen.generate_solid("#1a1a2e")
        deco = deco_gen.generate(DecorationStyle.CORNER_LINES)

        result = deco_gen.composite(bg, deco)

        assert result.size == (800, 600)
        assert result.mode == "RGB"


class TestLayerCompositor:
    """图层合成器测试"""

    def test_init(self):
        """测试初始化"""
        comp = LayerCompositor(1920, 1080)
        assert comp.width == 1920
        assert comp.height == 1080

    def test_composite_simple(self):
        """测试简单合成"""
        comp = LayerCompositor(800, 600)

        spec = CompositeSpec(
            layers=[
                LayerSpec(layer_type="background", style="solid"),
            ],
            base_color="#1a1a2e"
        )

        result = comp.composite(spec)
        assert result.size == (800, 600)
        assert result.mode == "RGB"

    def test_composite_with_decoration(self):
        """测试带装饰的合成"""
        comp = LayerCompositor(800, 600)

        spec = CompositeSpec(
            layers=[
                LayerSpec(layer_type="background", style="linear_gradient"),
                LayerSpec(layer_type="decoration", style="corner_lines"),
            ],
            base_color="#1a1a2e",
            accent_color="#4a90e2"
        )

        result = comp.composite(spec)
        assert result.size == (800, 600)

    def test_composite_with_overlay(self):
        """测试带叠加层的合成"""
        comp = LayerCompositor(800, 600)

        spec = CompositeSpec(
            layers=[
                LayerSpec(layer_type="background", style="radial_gradient"),
                LayerSpec(layer_type="overlay", config={"color": "#000000", "opacity": 0.3}),
            ]
        )

        result = comp.composite(spec)
        assert result.size == (800, 600)

    def test_get_text_safe_area(self):
        """测试获取文字安全区域"""
        comp = LayerCompositor(1920, 1080)

        text_zones = [
            TextZone(name="title", x=0.1, y=0.35, width=0.8, height=0.2),
            TextZone(name="subtitle", x=0.15, y=0.55, width=0.7, height=0.1),
        ]

        areas = comp.get_text_safe_area(text_zones)

        assert "title" in areas
        assert "subtitle" in areas
        assert len(areas["title"]) == 4  # (x, y, w, h)


class TestCompositePresets:
    """预设配置测试"""

    def test_hero_title_preset(self):
        """测试 Hero 标题预设"""
        spec = CompositePresets.hero_title("#4a90e2")

        assert len(spec.layers) > 0
        assert len(spec.text_zones) > 0
        assert spec.accent_color == "#4a90e2"

    def test_section_header_preset(self):
        """测试章节标题预设"""
        spec = CompositePresets.section_header("#ff6b6b")

        assert len(spec.layers) > 0
        assert spec.accent_color == "#ff6b6b"

    def test_visual_impact_preset(self):
        """测试视觉冲击预设"""
        spec = CompositePresets.visual_impact()

        assert len(spec.layers) > 0

    def test_minimal_clean_preset(self):
        """测试极简风格预设"""
        spec = CompositePresets.minimal_clean("#fafafa")

        assert spec.base_color == "#fafafa"

    def test_tech_modern_preset(self):
        """测试科技现代风格预设"""
        spec = CompositePresets.tech_modern("#00d4ff")

        assert spec.accent_color == "#00d4ff"
        assert spec.base_color == "#0a0a1a"


class TestLayeredSlideGenerator:
    """分层幻灯片生成器测试"""

    def test_init(self):
        """测试初始化"""
        gen = LayeredSlideGenerator()
        assert gen.SLIDE_WIDTH == 1920
        assert gen.SLIDE_HEIGHT == 1080

    def test_generate_background_image(self):
        """测试单独生成背景图像"""
        gen = LayeredSlideGenerator()

        img = gen.generate_background_image(
            style=LayeredSlideStyle.HERO_TITLE,
            accent_color="#4a90e2"
        )

        assert isinstance(img, Image.Image)
        assert img.size == (1920, 1080)

    def test_generate_background_image_to_file(self):
        """测试背景图像保存到文件"""
        gen = LayeredSlideGenerator()

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name

        try:
            saved_path = gen.generate_background_image(
                style=LayeredSlideStyle.TECH_MODERN,
                output_path=path
            )

            assert Path(saved_path).exists()
            img = Image.open(saved_path)
            assert img.size == (1920, 1080)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_generate_single_slide(self):
        """测试生成单个幻灯片"""
        gen = LayeredSlideGenerator()

        content = LayeredSlideContent(
            style=LayeredSlideStyle.HERO_TITLE,
            title="Test Presentation",
            subtitle="Generated by AI",
            accent_color="#4a90e2"
        )

        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as f:
            path = f.name

        try:
            pptx_path = gen.generate_slide(content, path)

            assert Path(pptx_path).exists()
            assert pptx_path.endswith(".pptx")
        finally:
            Path(path).unlink(missing_ok=True)

    def test_generate_multiple_slides(self):
        """测试生成多个幻灯片"""
        gen = LayeredSlideGenerator()

        contents = [
            LayeredSlideContent(
                style=LayeredSlideStyle.HERO_TITLE,
                title="Title Slide",
                subtitle="Welcome"
            ),
            LayeredSlideContent(
                style=LayeredSlideStyle.SECTION_HEADER,
                title="Section 1"
            ),
            LayeredSlideContent(
                style=LayeredSlideStyle.TECH_MODERN,
                title="Technology",
                body="Modern tech stack"
            ),
        ]

        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as f:
            path = f.name

        try:
            pptx_path = gen.generate_slides(contents, path)

            assert Path(pptx_path).exists()
        finally:
            Path(path).unlink(missing_ok=True)

    def test_all_styles(self):
        """测试所有样式生成"""
        gen = LayeredSlideGenerator()

        for style in LayeredSlideStyle:
            if style == LayeredSlideStyle.CUSTOM:
                continue

            img = gen.generate_background_image(style=style)
            assert img.size == (1920, 1080)

    def test_custom_colors(self):
        """测试自定义颜色"""
        gen = LayeredSlideGenerator()

        content = LayeredSlideContent(
            style=LayeredSlideStyle.HERO_TITLE,
            title="Custom Colors",
            accent_color="#ff6b6b",
            base_color="#2d3436",
            title_color="#ffffff"
        )

        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as f:
            path = f.name

        try:
            pptx_path = gen.generate_slide(content, path)
            assert Path(pptx_path).exists()
        finally:
            Path(path).unlink(missing_ok=True)


class TestIntegration:
    """集成测试"""

    def test_full_pipeline(self):
        """测试完整流水线"""
        # 1. 生成背景
        bg_gen = BackgroundGenerator(1920, 1080)
        bg_gen.generate(BackgroundStyle.DIAGONAL_GRADIENT)

        # 2. 生成装饰
        deco_gen = DecorationGenerator(1920, 1080)
        deco_gen.generate(DecorationStyle.CORNER_LINES)
        deco_gen.generate(DecorationStyle.SPOTLIGHT)

        # 3. 合成
        comp = LayerCompositor(1920, 1080)
        spec = CompositeSpec(
            layers=[
                LayerSpec(layer_type="background", style="diagonal_gradient"),
                LayerSpec(layer_type="decoration", style="corner_lines"),
                LayerSpec(layer_type="decoration", style="spotlight"),
            ]
        )
        result = comp.composite(spec)

        assert result.size == (1920, 1080)

    def test_preset_to_pptx(self):
        """测试预设到 PPTX 的完整流程"""
        gen = LayeredSlideGenerator()

        # 使用各种预设创建幻灯片
        contents = [
            LayeredSlideContent(
                style=LayeredSlideStyle.HERO_TITLE,
                title="Welcome",
                subtitle="AI Presentation"
            ),
            LayeredSlideContent(
                style=LayeredSlideStyle.VISUAL_IMPACT,
                title="Big Idea"
            ),
            LayeredSlideContent(
                style=LayeredSlideStyle.MINIMAL_CLEAN,
                title="Clean Design",
                body="Simple and elegant"
            ),
        ]

        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as f:
            path = f.name

        try:
            pptx_path = gen.generate_slides(contents, path)

            assert Path(pptx_path).exists()
            # 验证文件大小（应该有背景图像嵌入）
            assert os.path.getsize(pptx_path) > 10000  # 至少 10KB
        finally:
            Path(path).unlink(missing_ok=True)
