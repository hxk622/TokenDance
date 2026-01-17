"""
Decoration Generator - 装饰元素生成

支持的装饰类型：
- 几何装饰（角落图形、边框）
- 线条装饰（分隔线、连接线）
- 图标装饰（占位符）
- 光效装饰（高光、光晕）
"""

import math
import random
from dataclasses import dataclass
from enum import Enum

from PIL import Image, ImageDraw, ImageFilter


class DecorationStyle(str, Enum):
    """装饰样式枚举"""

    # 角落装饰
    CORNER_CIRCLES = "corner_circles"
    CORNER_LINES = "corner_lines"
    CORNER_BRACKETS = "corner_brackets"

    # 边框装饰
    BORDER_GLOW = "border_glow"
    BORDER_GRADIENT = "border_gradient"

    # 分隔装饰
    DIVIDER_LINE = "divider_line"
    DIVIDER_DOTS = "divider_dots"

    # 光效
    SPOTLIGHT = "spotlight"
    LENS_FLARE = "lens_flare"

    # 几何装饰
    FLOATING_SHAPES = "floating_shapes"
    ACCENT_BAR = "accent_bar"


@dataclass
class DecorationConfig:
    """装饰配置"""

    color: str = "#4a90e2"
    opacity: float = 0.5
    size: int = 100
    position: str = "auto"  # auto, top-left, top-right, bottom-left, bottom-right, center


@dataclass
class ShapeDecoration:
    """形状装饰定义"""

    shape_type: str  # circle, rectangle, line, triangle
    x: float  # 相对位置 0-1
    y: float
    width: float
    height: float
    color: str
    opacity: float = 0.3
    rotation: float = 0.0


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Hex 转 RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


class DecorationGenerator:
    """装饰元素生成器

    生成可叠加到背景上的装饰元素。

    使用示例：
        generator = DecorationGenerator(1920, 1080)

        # 角落装饰
        deco = generator.generate(DecorationStyle.CORNER_CIRCLES)

        # 合并到背景
        background.paste(deco, (0, 0), deco)
    """

    def __init__(self, width: int = 1920, height: int = 1080):
        """初始化

        Args:
            width: 图像宽度
            height: 图像高度
        """
        self.width = width
        self.height = height

    def generate(
        self,
        style: DecorationStyle,
        config: DecorationConfig | None = None
    ) -> Image.Image:
        """生成装饰层

        Args:
            style: 装饰样式
            config: 装饰配置

        Returns:
            Image.Image: 带透明通道的装饰图层（RGBA）
        """
        config = config or DecorationConfig()

        if style == DecorationStyle.CORNER_CIRCLES:
            return self.generate_corner_circles(config)
        elif style == DecorationStyle.CORNER_LINES:
            return self.generate_corner_lines(config)
        elif style == DecorationStyle.CORNER_BRACKETS:
            return self.generate_corner_brackets(config)
        elif style == DecorationStyle.BORDER_GLOW:
            return self.generate_border_glow(config)
        elif style == DecorationStyle.DIVIDER_LINE:
            return self.generate_divider_line(config)
        elif style == DecorationStyle.DIVIDER_DOTS:
            return self.generate_divider_dots(config)
        elif style == DecorationStyle.SPOTLIGHT:
            return self.generate_spotlight(config)
        elif style == DecorationStyle.LENS_FLARE:
            return self.generate_lens_flare(config)
        elif style == DecorationStyle.FLOATING_SHAPES:
            return self.generate_floating_shapes(config)
        elif style == DecorationStyle.ACCENT_BAR:
            return self.generate_accent_bar(config)
        else:
            return self._create_empty_layer()

    def _create_empty_layer(self) -> Image.Image:
        """创建空透明图层"""
        return Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))

    def generate_corner_circles(self, config: DecorationConfig) -> Image.Image:
        """生成角落圆形装饰"""
        layer = self._create_empty_layer()
        draw = ImageDraw.Draw(layer)

        color_rgb = hex_to_rgb(config.color)
        alpha = int(config.opacity * 255)
        color = (*color_rgb, alpha)

        size = config.size

        # 四个角落的圆形
        positions = [
            (-size // 2, -size // 2),  # 左上
            (self.width - size // 2, -size // 2),  # 右上
            (-size // 2, self.height - size // 2),  # 左下
            (self.width - size // 2, self.height - size // 2),  # 右下
        ]

        for x, y in positions:
            draw.ellipse(
                [x, y, x + size, y + size],
                fill=color
            )

        # 添加轻微模糊
        layer = layer.filter(ImageFilter.GaussianBlur(radius=10))

        return layer

    def generate_corner_lines(self, config: DecorationConfig) -> Image.Image:
        """生成角落线条装饰"""
        layer = self._create_empty_layer()
        draw = ImageDraw.Draw(layer)

        color_rgb = hex_to_rgb(config.color)
        alpha = int(config.opacity * 255)
        color = (*color_rgb, alpha)

        length = config.size
        thickness = 3
        margin = 40

        # 左上角
        draw.line([(margin, margin), (margin + length, margin)], fill=color, width=thickness)
        draw.line([(margin, margin), (margin, margin + length)], fill=color, width=thickness)

        # 右上角
        draw.line([(self.width - margin - length, margin), (self.width - margin, margin)], fill=color, width=thickness)
        draw.line([(self.width - margin, margin), (self.width - margin, margin + length)], fill=color, width=thickness)

        # 左下角
        draw.line([(margin, self.height - margin), (margin + length, self.height - margin)], fill=color, width=thickness)
        draw.line([(margin, self.height - margin - length), (margin, self.height - margin)], fill=color, width=thickness)

        # 右下角
        draw.line([(self.width - margin - length, self.height - margin), (self.width - margin, self.height - margin)], fill=color, width=thickness)
        draw.line([(self.width - margin, self.height - margin - length), (self.width - margin, self.height - margin)], fill=color, width=thickness)

        return layer

    def generate_corner_brackets(self, config: DecorationConfig) -> Image.Image:
        """生成角落方括号装饰"""
        layer = self._create_empty_layer()
        draw = ImageDraw.Draw(layer)

        color_rgb = hex_to_rgb(config.color)
        alpha = int(config.opacity * 255)
        color = (*color_rgb, alpha)

        length = config.size
        thickness = 2
        margin = 60

        # 左上角 [
        draw.line([(margin + length // 3, margin), (margin, margin)], fill=color, width=thickness)
        draw.line([(margin, margin), (margin, margin + length)], fill=color, width=thickness)
        draw.line([(margin, margin + length), (margin + length // 3, margin + length)], fill=color, width=thickness)

        # 右下角 ]
        x = self.width - margin
        y = self.height - margin - length
        draw.line([(x - length // 3, y), (x, y)], fill=color, width=thickness)
        draw.line([(x, y), (x, y + length)], fill=color, width=thickness)
        draw.line([(x, y + length), (x - length // 3, y + length)], fill=color, width=thickness)

        return layer

    def generate_border_glow(self, config: DecorationConfig) -> Image.Image:
        """生成边框发光效果"""
        layer = self._create_empty_layer()
        draw = ImageDraw.Draw(layer)

        color_rgb = hex_to_rgb(config.color)

        # 绘制多层边框，从外到内透明度递增
        for i in range(5):
            alpha = int(config.opacity * 255 * (1 - i * 0.2))
            color = (*color_rgb, alpha)
            thickness = 10 - i * 2
            offset = i * 5

            draw.rectangle(
                [offset, offset, self.width - offset, self.height - offset],
                outline=color,
                width=thickness
            )

        layer = layer.filter(ImageFilter.GaussianBlur(radius=5))

        return layer

    def generate_divider_line(self, config: DecorationConfig) -> Image.Image:
        """生成分隔线"""
        layer = self._create_empty_layer()
        draw = ImageDraw.Draw(layer)

        color_rgb = hex_to_rgb(config.color)
        alpha = int(config.opacity * 255)

        y = self.height // 2
        margin = self.width // 6

        # 渐变分隔线
        for x in range(margin, self.width - margin):
            # 两端淡出
            dist_from_edge = min(x - margin, self.width - margin - x)
            fade_zone = 100
            local_alpha = min(1.0, dist_from_edge / fade_zone)
            pixel_alpha = int(alpha * local_alpha)
            draw.point((x, y), fill=(*color_rgb, pixel_alpha))

        return layer

    def generate_divider_dots(self, config: DecorationConfig) -> Image.Image:
        """生成点状分隔线"""
        layer = self._create_empty_layer()
        draw = ImageDraw.Draw(layer)

        color_rgb = hex_to_rgb(config.color)
        alpha = int(config.opacity * 255)
        color = (*color_rgb, alpha)

        y = self.height // 2
        margin = self.width // 6
        dot_size = 4
        spacing = 20

        for x in range(margin, self.width - margin, spacing):
            draw.ellipse(
                [x - dot_size, y - dot_size, x + dot_size, y + dot_size],
                fill=color
            )

        return layer

    def generate_spotlight(self, config: DecorationConfig) -> Image.Image:
        """生成聚光灯效果"""
        layer = self._create_empty_layer()
        draw = ImageDraw.Draw(layer)

        color_rgb = hex_to_rgb(config.color)

        # 确定聚光灯位置
        if config.position == "top-left":
            cx, cy = self.width // 4, self.height // 4
        elif config.position == "top-right":
            cx, cy = self.width * 3 // 4, self.height // 4
        elif config.position == "center":
            cx, cy = self.width // 2, self.height // 2
        else:  # auto - 右上角
            cx, cy = self.width * 3 // 4, self.height // 4

        max_radius = config.size * 3

        # 绘制径向渐变聚光灯
        for r in range(max_radius, 0, -5):
            alpha = int(config.opacity * 255 * (1 - r / max_radius) * 0.5)
            color = (*color_rgb, alpha)
            draw.ellipse(
                [cx - r, cy - r, cx + r, cy + r],
                fill=color
            )

        layer = layer.filter(ImageFilter.GaussianBlur(radius=30))

        return layer

    def generate_lens_flare(self, config: DecorationConfig) -> Image.Image:
        """生成镜头光晕效果"""
        layer = self._create_empty_layer()
        draw = ImageDraw.Draw(layer)

        color_rgb = hex_to_rgb(config.color)

        # 主光源位置（右上角）
        cx, cy = int(self.width * 0.8), int(self.height * 0.2)

        # 主光点
        for r in range(50, 0, -2):
            alpha = int(config.opacity * 255 * (1 - r / 50))
            draw.ellipse(
                [cx - r, cy - r, cx + r, cy + r],
                fill=(*color_rgb, alpha)
            )

        # 光晕链
        direction_x = self.width // 2 - cx
        direction_y = self.height // 2 - cy
        math.sqrt(direction_x ** 2 + direction_y ** 2)

        for i in range(1, 5):
            t = i * 0.2
            fx = cx + direction_x * t
            fy = cy + direction_y * t
            r = 20 + i * 10
            alpha = int(config.opacity * 255 * 0.3)

            draw.ellipse(
                [fx - r, fy - r, fx + r, fy + r],
                fill=(*color_rgb, alpha)
            )

        layer = layer.filter(ImageFilter.GaussianBlur(radius=10))

        return layer

    def generate_floating_shapes(self, config: DecorationConfig) -> Image.Image:
        """生成浮动几何形状"""
        layer = self._create_empty_layer()
        draw = ImageDraw.Draw(layer)

        color_rgb = hex_to_rgb(config.color)

        # 生成多个随机形状
        for _ in range(8):
            shape_type = random.choice(["circle", "rectangle", "triangle"])
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            size = random.randint(20, 80)
            alpha = int(config.opacity * 255 * random.uniform(0.3, 0.8))
            color = (*color_rgb, alpha)

            if shape_type == "circle":
                draw.ellipse([x - size, y - size, x + size, y + size], fill=color)
            elif shape_type == "rectangle":
                random.uniform(0, math.pi / 4)
                draw.rectangle([x - size, y - size // 2, x + size, y + size // 2], fill=color)
            else:  # triangle
                points = [
                    (x, y - size),
                    (x - size, y + size),
                    (x + size, y + size)
                ]
                draw.polygon(points, fill=color)

        layer = layer.filter(ImageFilter.GaussianBlur(radius=3))

        return layer

    def generate_accent_bar(self, config: DecorationConfig) -> Image.Image:
        """生成强调条装饰"""
        layer = self._create_empty_layer()
        draw = ImageDraw.Draw(layer)

        color_rgb = hex_to_rgb(config.color)
        alpha = int(config.opacity * 255)
        color = (*color_rgb, alpha)

        # 左侧垂直强调条
        bar_width = 8
        bar_height = self.height // 3
        y_start = (self.height - bar_height) // 2
        margin = 80

        draw.rectangle(
            [margin, y_start, margin + bar_width, y_start + bar_height],
            fill=color
        )

        # 顶部水平强调条
        h_bar_width = self.width // 4
        h_bar_height = 4
        x_start = (self.width - h_bar_width) // 2

        draw.rectangle(
            [x_start, margin, x_start + h_bar_width, margin + h_bar_height],
            fill=color
        )

        return layer

    def generate_from_shapes(self, shapes: list[ShapeDecoration]) -> Image.Image:
        """从形状定义列表生成装饰层

        Args:
            shapes: 形状装饰列表

        Returns:
            Image.Image: 合成的装饰图层
        """
        layer = self._create_empty_layer()
        draw = ImageDraw.Draw(layer)

        for shape in shapes:
            color_rgb = hex_to_rgb(shape.color)
            alpha = int(shape.opacity * 255)
            color = (*color_rgb, alpha)

            # 转换相对坐标为绝对坐标
            x = int(shape.x * self.width)
            y = int(shape.y * self.height)
            w = int(shape.width * self.width)
            h = int(shape.height * self.height)

            if shape.shape_type == "circle":
                r = min(w, h) // 2
                draw.ellipse([x - r, y - r, x + r, y + r], fill=color)
            elif shape.shape_type == "rectangle":
                draw.rectangle([x - w // 2, y - h // 2, x + w // 2, y + h // 2], fill=color)
            elif shape.shape_type == "line":
                draw.line([(x, y), (x + w, y + h)], fill=color, width=3)
            elif shape.shape_type == "triangle":
                points = [
                    (x, y - h // 2),
                    (x - w // 2, y + h // 2),
                    (x + w // 2, y + h // 2)
                ]
                draw.polygon(points, fill=color)

        return layer

    def composite(self, base: Image.Image, decoration: Image.Image) -> Image.Image:
        """将装饰层合成到基础图层

        Args:
            base: 基础图层（RGB）
            decoration: 装饰图层（RGBA）

        Returns:
            Image.Image: 合成结果（RGB）
        """
        if base.mode != "RGBA":
            base = base.convert("RGBA")

        result = Image.alpha_composite(base, decoration)
        return result.convert("RGB")
