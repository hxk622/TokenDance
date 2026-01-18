"""
Layer Compositor - 图层合成器

将背景、装饰、文字区域等多个图层合成为最终图像。
支持导出为 PPTX 幻灯片背景。
"""

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from .backgrounds import BackgroundGenerator, BackgroundStyle
from .decorations import DecorationConfig, DecorationGenerator, DecorationStyle


@dataclass
class LayerSpec:
    """图层规格"""

    layer_type: str  # background, decoration, overlay, text_zone
    style: str | None = None
    config: dict[str, Any] = field(default_factory=dict)
    opacity: float = 1.0
    blend_mode: str = "normal"  # normal, multiply, screen, overlay


@dataclass
class TextZone:
    """文字区域定义

    定义可编辑文字的安全区域，避免与背景元素冲突。
    """

    name: str  # title, subtitle, body, etc.
    x: float  # 相对位置 0-1
    y: float
    width: float
    height: float
    padding: int = 20


@dataclass
class CompositeSpec:
    """合成规格"""

    layers: list[LayerSpec] = field(default_factory=list)
    text_zones: list[TextZone] = field(default_factory=list)
    base_color: str = "#1a1a2e"
    accent_color: str = "#4a90e2"


class LayerCompositor:
    """图层合成器

    将多个图层按顺序合成为最终图像。

    使用示例：
        compositor = LayerCompositor(1920, 1080)

        spec = CompositeSpec(
            layers=[
                LayerSpec(layer_type="background", style="linear_gradient"),
                LayerSpec(layer_type="decoration", style="corner_lines"),
            ],
            base_color="#1a1a2e",
            accent_color="#4a90e2"
        )

        result = compositor.composite(spec)
    """

    def __init__(self, width: int = 1920, height: int = 1080):
        """初始化

        Args:
            width: 画布宽度
            height: 画布高度
        """
        self.width = width
        self.height = height
        self.bg_generator = BackgroundGenerator(width, height)
        self.deco_generator = DecorationGenerator(width, height)

    def composite(self, spec: CompositeSpec) -> Image.Image:
        """合成图层

        Args:
            spec: 合成规格

        Returns:
            Image.Image: 合成结果
        """
        # 创建画布
        canvas = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))

        # 按顺序合成每个图层
        for layer_spec in spec.layers:
            layer = self._generate_layer(layer_spec, spec.base_color, spec.accent_color)

            if layer is not None:
                # 应用透明度
                if layer_spec.opacity < 1.0:
                    layer = self._apply_opacity(layer, layer_spec.opacity)

                # 合成
                canvas = self._blend_layers(canvas, layer, layer_spec.blend_mode)

        return canvas.convert("RGB")

    def _generate_layer(
        self,
        layer_spec: LayerSpec,
        base_color: str,
        accent_color: str
    ) -> Image.Image | None:
        """生成单个图层"""

        if layer_spec.layer_type == "background":
            style = BackgroundStyle(layer_spec.style) if layer_spec.style else BackgroundStyle.SOLID
            return self.bg_generator.generate(
                style,
                base_color=base_color,
                accent_color=accent_color,
                **layer_spec.config
            ).convert("RGBA")

        elif layer_spec.layer_type == "decoration":
            style = DecorationStyle(layer_spec.style) if layer_spec.style else None
            if style:
                config = DecorationConfig(
                    color=layer_spec.config.get("color", accent_color),
                    opacity=layer_spec.config.get("opacity", 0.5),
                    size=layer_spec.config.get("size", 100),
                    position=layer_spec.config.get("position", "auto")
                )
                return self.deco_generator.generate(style, config)

        elif layer_spec.layer_type == "overlay":
            # 纯色叠加层
            color = layer_spec.config.get("color", "#000000")
            opacity = layer_spec.config.get("opacity", 0.3)
            return self._create_overlay(color, opacity)

        elif layer_spec.layer_type == "vignette":
            # 暗角效果
            return self._create_vignette(
                layer_spec.config.get("intensity", 0.5),
                layer_spec.config.get("color", "#000000")
            )

        return None

    def _create_overlay(self, color: str, opacity: float) -> Image.Image:
        """创建纯色叠加层"""
        layer = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)

        hex_color = color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        alpha = int(opacity * 255)

        draw.rectangle(
            [0, 0, self.width, self.height],
            fill=(r, g, b, alpha)
        )

        return layer

    def _create_vignette(self, intensity: float, color: str) -> Image.Image:
        """创建暗角效果"""
        layer = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)

        hex_color = color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        # 从边缘到中心的渐变
        cx, cy = self.width // 2, self.height // 2
        max_dist = (cx ** 2 + cy ** 2) ** 0.5

        for y in range(self.height):
            for x in range(self.width):
                dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                t = dist / max_dist
                alpha = int(intensity * 255 * t * t)  # 二次曲线
                draw.point((x, y), fill=(r, g, b, alpha))

        return layer

    def _apply_opacity(self, layer: Image.Image, opacity: float) -> Image.Image:
        """应用透明度"""
        if layer.mode != "RGBA":
            layer = layer.convert("RGBA")

        # 获取 alpha 通道并调整
        r, g, b, a = layer.split()
        a = a.point(lambda x: int(x * opacity))

        return Image.merge("RGBA", (r, g, b, a))

    def _blend_layers(
        self,
        base: Image.Image,
        layer: Image.Image,
        blend_mode: str
    ) -> Image.Image:
        """混合图层

        Args:
            base: 底层
            layer: 叠加层
            blend_mode: 混合模式

        Returns:
            Image.Image: 混合结果
        """
        if base.mode != "RGBA":
            base = base.convert("RGBA")
        if layer.mode != "RGBA":
            layer = layer.convert("RGBA")

        if blend_mode == "normal":
            return Image.alpha_composite(base, layer)

        elif blend_mode == "multiply":
            # 正片叠底
            return self._blend_multiply(base, layer)

        elif blend_mode == "screen":
            # 滤色
            return self._blend_screen(base, layer)

        elif blend_mode == "overlay":
            # 叠加
            return self._blend_overlay(base, layer)

        else:
            return Image.alpha_composite(base, layer)

    def _blend_multiply(self, base: Image.Image, layer: Image.Image) -> Image.Image:
        """正片叠底混合"""
        result = Image.new("RGBA", (self.width, self.height))

        base_pixels = base.load()
        layer_pixels = layer.load()
        result_pixels = result.load()

        for y in range(self.height):
            for x in range(self.width):
                br, bg, bb, ba = base_pixels[x, y]
                lr, lg, lb, la = layer_pixels[x, y]

                # 正片叠底公式
                t = la / 255
                nr = int(br * lr / 255 * t + br * (1 - t))
                ng = int(bg * lg / 255 * t + bg * (1 - t))
                nb = int(bb * lb / 255 * t + bb * (1 - t))

                result_pixels[x, y] = (nr, ng, nb, ba)

        return result

    def _blend_screen(self, base: Image.Image, layer: Image.Image) -> Image.Image:
        """滤色混合"""
        result = Image.new("RGBA", (self.width, self.height))

        base_pixels = base.load()
        layer_pixels = layer.load()
        result_pixels = result.load()

        for y in range(self.height):
            for x in range(self.width):
                br, bg, bb, ba = base_pixels[x, y]
                lr, lg, lb, la = layer_pixels[x, y]

                # 滤色公式
                t = la / 255
                nr = int((255 - (255 - br) * (255 - lr) / 255) * t + br * (1 - t))
                ng = int((255 - (255 - bg) * (255 - lg) / 255) * t + bg * (1 - t))
                nb = int((255 - (255 - bb) * (255 - lb) / 255) * t + bb * (1 - t))

                result_pixels[x, y] = (nr, ng, nb, ba)

        return result

    def _blend_overlay(self, base: Image.Image, layer: Image.Image) -> Image.Image:
        """叠加混合"""
        result = Image.new("RGBA", (self.width, self.height))

        base_pixels = base.load()
        layer_pixels = layer.load()
        result_pixels = result.load()

        def overlay_channel(base_val: int, layer_val: int) -> int:
            if base_val < 128:
                return int(2 * base_val * layer_val / 255)
            else:
                return int(255 - 2 * (255 - base_val) * (255 - layer_val) / 255)

        for y in range(self.height):
            for x in range(self.width):
                br, bg, bb, ba = base_pixels[x, y]
                lr, lg, lb, la = layer_pixels[x, y]

                t = la / 255
                nr = int(overlay_channel(br, lr) * t + br * (1 - t))
                ng = int(overlay_channel(bg, lg) * t + bg * (1 - t))
                nb = int(overlay_channel(bb, lb) * t + bb * (1 - t))

                result_pixels[x, y] = (nr, ng, nb, ba)

        return result

    def save(self, image: Image.Image, path: str | Path) -> str:
        """保存合成图像"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(str(path), quality=95)
        return str(path)

    def to_bytes(self, image: Image.Image, format: str = "PNG") -> bytes:
        """转换为字节"""
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        return buffer.getvalue()

    def get_text_safe_area(
        self,
        text_zones: list[TextZone]
    ) -> dict[str, tuple[int, int, int, int]]:
        """获取文字安全区域（像素坐标）

        Args:
            text_zones: 文字区域定义列表

        Returns:
            Dict[str, Tuple]: {zone_name: (x, y, width, height)}
        """
        result = {}

        for zone in text_zones:
            x = int(zone.x * self.width) + zone.padding
            y = int(zone.y * self.height) + zone.padding
            w = int(zone.width * self.width) - 2 * zone.padding
            h = int(zone.height * self.height) - 2 * zone.padding

            result[zone.name] = (x, y, w, h)

        return result


# 预设合成配置
class CompositePresets:
    """预设合成配置"""

    @staticmethod
    def hero_title(accent_color: str = "#4a90e2") -> CompositeSpec:
        """Hero 标题页配置"""
        return CompositeSpec(
            layers=[
                LayerSpec(layer_type="background", style="diagonal_gradient"),
                LayerSpec(layer_type="decoration", style="corner_lines", config={"opacity": 0.6}),
                LayerSpec(layer_type="decoration", style="spotlight", config={"opacity": 0.3, "size": 150}),
            ],
            text_zones=[
                TextZone(name="title", x=0.1, y=0.35, width=0.8, height=0.2),
                TextZone(name="subtitle", x=0.15, y=0.55, width=0.7, height=0.1),
            ],
            accent_color=accent_color
        )

    @staticmethod
    def section_header(accent_color: str = "#4a90e2") -> CompositeSpec:
        """章节标题配置"""
        return CompositeSpec(
            layers=[
                LayerSpec(layer_type="background", style="radial_gradient"),
                LayerSpec(layer_type="decoration", style="accent_bar", config={"opacity": 0.8}),
            ],
            text_zones=[
                TextZone(name="section_number", x=0.1, y=0.3, width=0.2, height=0.15),
                TextZone(name="section_title", x=0.1, y=0.45, width=0.8, height=0.2),
            ],
            accent_color=accent_color
        )

    @staticmethod
    def visual_impact(accent_color: str = "#4a90e2") -> CompositeSpec:
        """视觉冲击配置"""
        return CompositeSpec(
            layers=[
                LayerSpec(layer_type="background", style="blob"),
                LayerSpec(layer_type="overlay", config={"color": "#000000", "opacity": 0.2}),
                LayerSpec(layer_type="decoration", style="floating_shapes", config={"opacity": 0.4}),
                LayerSpec(layer_type="vignette", config={"intensity": 0.3}),
            ],
            text_zones=[
                TextZone(name="main_text", x=0.15, y=0.4, width=0.7, height=0.2),
            ],
            accent_color=accent_color
        )

    @staticmethod
    def minimal_clean(base_color: str = "#fafafa") -> CompositeSpec:
        """极简干净配置（浅色）"""
        return CompositeSpec(
            layers=[
                LayerSpec(layer_type="background", style="grid"),
            ],
            text_zones=[
                TextZone(name="content", x=0.1, y=0.1, width=0.8, height=0.8),
            ],
            base_color=base_color,
            accent_color="#333333"
        )

    @staticmethod
    def tech_modern(accent_color: str = "#00d4ff") -> CompositeSpec:
        """科技现代风格"""
        return CompositeSpec(
            layers=[
                LayerSpec(layer_type="background", style="hexagons"),
                LayerSpec(layer_type="decoration", style="corner_brackets", config={"opacity": 0.7}),
                LayerSpec(layer_type="decoration", style="floating_shapes", config={"opacity": 0.2}),
            ],
            text_zones=[
                TextZone(name="title", x=0.1, y=0.3, width=0.8, height=0.15),
                TextZone(name="body", x=0.1, y=0.5, width=0.8, height=0.35),
            ],
            base_color="#0a0a1a",
            accent_color=accent_color
        )
